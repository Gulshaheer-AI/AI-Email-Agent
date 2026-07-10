import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
from config.database import SessionLocal
from models.schemas import Ticket
from tools.operational_tools import route_to_refunds, mark_as_spam, search_company_policy, deny_request
import time

load_dotenv()

# Initialize the Gemini Client using the latest 2026 SDK architecture
client = genai.Client(api_key=os.getenv("Gemini_Key_2"))

def process_next_pending_ticket():
    """Fetches the oldest unassigned ticket from Neon and hands it to the Gemini Agent loop."""
    db = SessionLocal()
    ticket = db.query(Ticket).filter(Ticket.current_status == "pending").order_by(Ticket.created_at.asc()).first()
    
    if not ticket:
        # We remove the print statement here so it doesn't spam your terminal every 10 seconds
        db.close()
        return False # Return False to let the loop know nothing happened
    

    print(f"\n[Processing Ticket] ID: {ticket.id} | From: {ticket.sender_email}")
    print(f"Subject: {ticket.subject}")
    print(f"Body: {ticket.raw_body.strip()}")
    
    
    # 2. Build the System Instruction to guide the agent behavior safely
    system_prompt = (
        "You are an empowered, intelligent customer support employee for GlobalTech. "
        "Your goal is to read incoming customer emails and handle them appropriately. "
        "You have access to company tools, but you must use your own judgment to decide "
        "If the customer request violates company policy, you have the authority to deny it"
        "if and when to use them based on the context of the email. "
        "You dont need to worry about not having authority to make a certain decision, because you are empowered to act on behalf of the company. "
        "Think critically before acting."
    )

    # 3. Configure the Agent with Automatic Tool Calling enabled
    chat = client.chats.create(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            tools=[route_to_refunds, mark_as_spam, search_company_policy, deny_request],
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=False),
            temperature=0.4
        )
    )
    

    # 4. Prompt the agent with the data payload
    user_message = f"Process this ticket:\nTicket ID: {ticket.id}\nEmail Body: {ticket.raw_body}"
    
    print("\n[Running Gemini Agent Thinking Loop...]")
    response = chat.send_message(user_message)
    
    print(f"\n[Agent Final Output]: {response.text}")
    db.close()
    return True  # Return True to indicate a ticket was processed

def start_worker_node():
    """Keeps the agent alive in the background listening for new database rows."""
    print("[Agent Node Online] Listening for incoming webhooks...")
    while True:
        try:
            # If it processed a ticket, it will immediately loop and check for another.
            # If it didn't find one, it sleeps for 10 seconds before checking again.
            found_ticket = process_next_pending_ticket()
            if not found_ticket:
                time.sleep(10)
        except Exception as e:
            print(f"\n[Critical Worker Error] {str(e)}")
            time.sleep(10) # If the database drops, sleep before retrying to prevent a crash loop

if __name__ == "__main__":
    start_worker_node()