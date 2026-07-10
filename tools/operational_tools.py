import os
from sqlalchemy.orm import Session
from config.database import SessionLocal
from models.schemas import Ticket, AgentExecutionLog,RagReference
import os
from pinecone import Pinecone
from google import genai

def route_to_refunds(ticket_id: str, reasoning: str) -> str:
    """
    Escalates a ticket to the human refunds department for final processing.
    """
    print(f"\n[Tool Executing] Routing ticket {ticket_id} to Refunds department...")
    
    db: Session = SessionLocal()
    try:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if ticket:
            ticket.assigned_category = "refund"
            ticket.current_status = "processed"
            
            # Create an audit log trace
            log = AgentExecutionLog(
                ticket_id=ticket_id,
                model_used="gemini-2.5-flash",
                tool_invoked="route_to_refunds",
                llm_reasoning=reasoning,
                execution_status="success"
            )
            db.add(log)
            db.commit()
            return f"Successfully escalated ticket {ticket_id} to the refunds team queue."
        return "Error: Ticket ID not found."
    finally:
        db.close()

def mark_as_spam(ticket_id: str, reasoning: str) -> str:
    """
    Flags an email ticket as malicious, promotional, or junk spam.
    Use this tool if the email is an advertisement, phishing attempt, or random gibberish.
    """
    print(f"\n[Tool Executing] Flagging ticket {ticket_id} as Spam...")
    
    db: Session = SessionLocal()
    try:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if ticket:
            ticket.assigned_category = "spam"
            ticket.current_status = "processed"
            
            log = AgentExecutionLog(
                ticket_id=ticket_id,
                model_used="gemini-2.5-flash",
                tool_invoked="mark_as_spam",
                llm_reasoning=reasoning,
                execution_status="success"
            )
            db.add(log)
            db.commit()
            return f"Ticket {ticket_id} has been safely marked as spam and archived."
        return "Error: Ticket ID not found."
    finally:
        db.close()
        
def search_company_policy(ticket_id: str, search_query: str) -> str:
    """
   Searches the internal company knowledge base for policies, rules, and guidelines regarding refunds, hardware, and software.
    """
    try:
        # 1. Initialize clients
        client_gemini = genai.Client(api_key=os.getenv("Gemini_Key_2"))
        pc = Pinecone(api_key=os.getenv("Pinecone_Key")) 
        print(f"\n[Tool Executing] Searching company policy for: {search_query}")
        # 2. Target your existing cloud index
        index = pc.Index("refund-policy-index")

        # 3. Generate vector for the AI's search query
        query_response = client_gemini.models.embed_content(
            model="gemini-embedding-2",
            contents=search_query,
            config={"output_dimensionality": 768}
        )
        query_vector = query_response.embeddings[0].values

        # 4. Perform similarity search in Pinecone
        search_results = index.query(
            vector=query_vector,
            top_k=2,  # Grab the top 2 closest chunks for better context
            include_metadata=True 
        )
        db = SessionLocal()
        try:
            # 2. Create the Execution Log right here because the tool WAS invoked
            execution_log = AgentExecutionLog(

                ticket_id=ticket_id,
                model_used="gemini-2.5-flash",
                tool_invoked="search_company_policy",
                llm_reasoning=f"Search query: {search_query}",
                execution_status="success"
        
            )
            db.add(execution_log)
            db.commit()
            db.refresh(execution_log)  # Captures the newly generated log ID
            
            # 3. Immediately create the RAG Reference using that brand new ID
            rag_ref = RagReference(
                log_id=execution_log.id,  # Perfect foreign key relation
                retrieved_chunk_text="\n---\n".join([match.metadata['text'] for match in search_results.matches]),
                pinecone_vector_id=search_results.matches[0].id if search_results.matches else None,
                similarity_score=search_results.matches[0].score if search_results.matches else None
            )
            db.add(rag_ref)
            db.commit()
            print("[Database] Successfully tied RAG reference to Tool Execution Log.")
            
        except Exception as e:
            db.rollback()
            print(f"Logging failed: {e}")
        finally:
            db.close()

            # 5. Handle empty results
            if not search_results.matches:
                return "No relevant policy found for this query."

            # 6. Extract and combine the text from the top matches
            retrieved_texts = [match.metadata['text'] for match in search_results.matches]
            combined_context = "\n---\n".join(retrieved_texts)

            return f"Retrieved Policy Information:\n{combined_context}"
    except Exception as e:
        return f"Error during policy search: {str(e)}"

  
    


    
def deny_request(ticket_id: str, reason: str) -> str:
    """
    Denies a customer's request and automatically closes the ticket in the database.
    Use this tool when a user's request explicitly violates company policy discovered during a search.
    """
    print(f"\n[Tool Executing] Denying ticket {ticket_id}...")
    print(f"[Reason]: {reason}")
    
    # Open a clean database session for the worker
    db = SessionLocal()
    try:
        # Locate the open ticket in PostgreSQL
       ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    
       if ticket:
            ticket.assigned_category = "rejected"
            ticket.current_status = "processed"
            
            # Create an audit log trace
            log = AgentExecutionLog(
                ticket_id=ticket_id,
                model_used="gemini-2.5-flash",
                tool_invoked="deny_request",
                llm_reasoning=reason,
                execution_status="success"
            )
            db.add(log)
            db.commit()
            print(f"[Database Success] Ticket {ticket_id} status updated to 'Closed_Denied'.")
    except Exception as e:
        db.rollback()    
        return f"Error accessing ticket database: {str(e)}"         
      
    return f"Ticket has been officially denied and closed in the system. Reason logged: {reason}"
   