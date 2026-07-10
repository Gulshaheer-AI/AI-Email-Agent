from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from config.database import get_db
from models.schemas import Ticket
import uuid

router = APIRouter(prefix="/api/v1/webhooks", tags=["Inbound Webhooks"])

@router.post("/incoming-email", status_code=status.HTTP_201_CREATED)
async def receive_inbound_email(request: Request, db: Session = Depends(get_db)) -> dict:
    """
    Receives a Normalized JSON webhook from CloudMailin,
    extracts the email data, and registers a ticket.
    """
    try:
        # Read the raw JSON payload from the webhook provider
        payload = await request.json()
        
        # Parse CloudMailin's specific nested JSON structure
        sender = payload.get("envelope", {}).get("from", "unknown_sender")
        headers = payload.get("headers", {})
        
        # Safely handle case-sensitivity in headers
        subject = headers.get("subject", headers.get("Subject", "No Subject"))
        body = payload.get("plain", "No body text provided.")

        # Create a new Ticket record in PostgreSQL
        new_ticket = Ticket(
            id=str(uuid.uuid4()),
            sender_email=sender,
            subject=subject,
            raw_body=body,
            assigned_category="unassigned",
            current_status="pending"
        )
        
        db.add(new_ticket)
        db.commit()
        db.refresh(new_ticket)
        
        print(f"\n[Webhook Success] Ticket {new_ticket.id} created for {sender}")
        
        return {"status": "success", "ticket_id": new_ticket.id}
        
    except Exception as e:
        db.rollback()
        print(f"[Webhook Error] {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process inbound webhook."
        )