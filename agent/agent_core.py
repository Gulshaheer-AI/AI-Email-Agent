import os
import time
from dotenv import load_dotenv
from config.database import SessionLocal
from models.schemas import Ticket
from tools.operational_tools import route_to_refunds, mark_as_spam, search_company_policy, deny_request

# LangGraph ecosystem imports
from typing import Annotated, TypedDict
from langchain_core.messages import AnyMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.types import Command
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

# --- 1. STATE DEFINITION ---
class TicketState(TypedDict):
    ticket_id: str
    email_body: str
    messages: Annotated[list[AnyMessage], add_messages]

# --- 2. MODEL & TOOL INITIALIZATION ---
api_key = os.getenv("Gemini_Key_2") or os.getenv("GEMINI_KEY")
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=api_key, temperature=0.4)

system_instruction = (
    "You are an empowered, intelligent customer support employee for GlobalTech. "
    "Your goal is to read incoming customer emails and handle them appropriately. "
    "You have access to company tools, but you must use your own judgment to decide "
    "if and when to use them based on the context of the email. "
    "If the customer request violates company policy, you have the authority to deny it. "
    "Think critically before acting."
)

llm_with_system = llm.bind(system_instruction=system_instruction)
llm_with_tools = llm_with_system.bind_tools([route_to_refunds, mark_as_spam, search_company_policy, deny_request])

# --- 3. GRAPH NODES ---
def triage_agent(state: TicketState):
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}

tool_node = ToolNode([route_to_refunds, mark_as_spam, search_company_policy, deny_request])

# --- 4. GRAPH TOPOLOGY (BLUEPRINT) ---
builder = StateGraph(TicketState)
builder.add_node("triage_agent", triage_agent)
builder.add_node("tools", tool_node)
builder.add_edge(START, "triage_agent")
builder.add_conditional_edges("triage_agent", tools_condition)
builder.add_edge("tools", "triage_agent") # The cyclic ReAct loop

# --- 5. WORKER EXECUTION LOGIC ---
def process_next_pending_ticket(email_agent_graph):
    """Fetches the ticket and runs the compiled graph engine."""
    db = SessionLocal()
    ticket = db.query(Ticket).filter(Ticket.current_status == "pending").order_by(Ticket.created_at.asc()).first()
    
    if not ticket:
        db.close()
        return False

    print(f"\n[Processing Ticket] ID: {ticket.id} | From: {ticket.sender_email}")
    
    initial_input = {
        "ticket_id": str(ticket.id),
        "email_body": ticket.raw_body,
        "messages": [HumanMessage(content=f"Process this ticket:\nTicket ID: {ticket.id}\nEmail Body: {ticket.raw_body}")]
    }
    
    # Establish the thread ID so Postgres knows where to save this ticket's memory
    config = {"configurable": {"thread_id": str(ticket.id)}}
    
    print("\n[Running LangGraph Engine...]")
    # 1. Run the graph. (If it hits the tripwire, it saves to DB and returns immediately)
    email_agent_graph.invoke(initial_input, config)
    
    # 2. Check the memory to see if the graph froze mid-task
    state_snapshot = email_agent_graph.get_state(config)
    
    if state_snapshot.tasks:
        # Extract the dictionary we passed into the interrupt() function
        interrupt_data = state_snapshot.tasks[0].interrupts[0].value
        
        print(f"\n[⚠️ MANAGER APPROVAL REQUIRED]")
        print(f"Action: {interrupt_data['action']}")
        print(f"Reasoning: {interrupt_data['ai_reasoning']}")
        
        # 3. Simulate the Human-in-the-Loop decision
        user_input = input("\nType 'approve' to execute, or 'reject' to block: ").strip().lower()
        
        print("\n[Resuming Graph Execution...]")
        # 4. Use the delivery truck (Command) to pass the string directly into the frozen variable
        email_agent_graph.invoke(Command(resume=user_input), config)
    
    # Print the final trace output for debugging
    final_state = email_agent_graph.get_state(config).values
    print("\n[Agent Execution Complete] Final Conversation Trace:")
    for msg in final_state["messages"]:
        msg.pretty_print()
        
    db.close()
    return True

def start_worker_node():
    """Compiles the graph with the DB connection and starts the listener loop."""
    db_uri = os.getenv("DATABASE_URL")
    
    # Open the connection to Neon and keep it alive for the entire worker session
    with PostgresSaver.from_conn_string(db_uri) as checkpointer:
        print("[Database] Checkpointer connected. Verifying tables...")
        checkpointer.setup() # Automatically builds tracking tables if missing
        
        # Compile the graph blueprint into a live engine attached to the checkpointer
        email_agent_graph = builder.compile(checkpointer=checkpointer)
        
        print("[Agent Node Online] Listening for incoming webhooks...")
        while True:
            try:
                # Pass the live engine into the processor
                found_ticket = process_next_pending_ticket(email_agent_graph)
                if not found_ticket:
                    time.sleep(10)
            except Exception as e:
                print(f"\n[Critical Worker Error] {str(e)}")
                time.sleep(10)

if __name__ == "__main__":
    start_worker_node()