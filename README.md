# Autonomous Email Operations Agent

An AI-powered backend system that receives inbound customer emails through webhooks, stores them as support tickets, and uses a Gemini-based autonomous agent to classify, process, and route each request.

The project is built with FastAPI, SQLAlchemy, PostgreSQL/Neon, Google Gemini, Pinecone, and a simple RAG pipeline for company policy lookup. It is designed as a backend foundation for an intelligent customer support workflow where incoming emails can be automatically reviewed, checked against internal policy documents, marked as spam, denied, or escalated to the correct department.

## Features

- Receives inbound email webhooks through a FastAPI endpoint
- Stores email tickets in a PostgreSQL database using SQLAlchemy
- Runs a background Gemini agent to process pending tickets
- Uses Gemini automatic function calling to let the agent choose operational tools
- Supports ticket routing, spam detection, request denial, and policy lookup
- Includes a RAG workflow for uploading PDF policy documents to Pinecone
- Logs agent actions and retrieved policy references for traceability

## Tech Stack

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL / Neon
- Google Gemini API
- Pinecone Vector Database
- pypdf
- Uvicorn
- python-dotenv

## Project Structure

```txt
email_agent_system/
├── main.py                  # FastAPI application entry point
├── api/
│   └── webhooks.py           # Inbound email webhook routes
├── agent/
│   └── agent_core.py         # Gemini agent worker loop
├── config/
│   └── database.py           # Database connection setup
├── models/
│   └── schemas.py            # SQLAlchemy database models
├── tools/
│   └── operational_tools.py  # Agent tools for routing, spam, RAG, and denial
├── scripts/
│   ├── rag_doc.py            # PDF parsing and text chunking
│   └── rag_upload.py         # Embedding and Pinecone upload script
└── requirements.txt
## Purpose

This project demonstrates how an autonomous AI agent can be integrated into a real backend workflow. Instead of only generating text responses, the agent can inspect incoming customer requests, search company policy, update database records, and create an auditable trail of its decisions.

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/email-agent-system.git
cd email-agent-system
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

Activate it on macOS/Linux:

```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file in the project root and add your credentials:

```env
DATABASE_URL=your_postgresql_or_neon_connection_url
Gemini_Key_2=your_gemini_api_key
GEMINI_KEY=your_gemini_api_key
Pinecone_Key=your_pinecone_api_key
Pinecone_key=your_pinecone_api_key
```

Note: The project currently uses slightly different environment variable names in different files, so both uppercase/lowercase variants are included above.

## Running the API Server

Start the FastAPI backend:

```bash
python main.py
```

The server will run locally at:

```txt
http://127.0.0.1:8000
```

Health check endpoint:

```txt
GET /health
```

Webhook endpoint:

```txt
POST /api/v1/webhooks/incoming-email
```

FastAPI interactive documentation:

```txt
http://127.0.0.1:8000/docs
```

## Running the Agent Worker

In a second terminal, run:

```bash
python agent/agent_core.py
```

The worker continuously checks the database for pending tickets and processes them using Gemini.

## Webhook Payload Example

Example JSON payload for the inbound email webhook:

```json
{
  "envelope": {
    "from": "customer@example.com"
  },
  "headers": {
    "subject": "Refund request"
  },
  "plain": "Hello, I would like to request a refund for my product."
}
```

Send this payload to:

```txt
POST http://127.0.0.1:8000/api/v1/webhooks/incoming-email
```

## RAG Policy Upload

The project includes a simple RAG pipeline for uploading policy documents to Pinecone.

### 1. Add Your Policy PDF

Place your policy PDF in the project directory.

### 2. Update the PDF Filename

Open:

```txt
scripts/rag_upload.py
```

Update this line if needed:

```python
pdf_file = "target_document.pdf"
```

### 3. Run the Upload Script

```bash
cd scripts
python rag_upload.py
```

This script extracts text from the PDF, chunks it, creates Gemini embeddings, and uploads the vectors to Pinecone.

## Agent Tools

The Gemini agent can use the following operational tools:

- `route_to_refunds` - Escalates a ticket to the refunds department
- `mark_as_spam
```
