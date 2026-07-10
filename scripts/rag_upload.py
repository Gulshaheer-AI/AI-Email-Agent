import os
from dotenv import load_dotenv
from google import genai
from pinecone import Pinecone
import time
# Import the custom parsing functions we wrote in Block 1
from rag_doc import extract_text_from_pdf, sliding_window_chunker

# 1. Initialize core system connections
load_dotenv()
client_gemini = genai.Client(api_key=os.getenv("GEMINI_KEY"))
pc = Pinecone(api_key=os.getenv("Pinecone_key"))
index = pc.Index("refund-policy-index") # Matches your 768-dim manual index

# 2. Extract and chunk your actual PDF
pdf_file = "target_document.pdf"
raw_text = extract_text_from_pdf(pdf_file)
chunks = sliding_window_chunker(raw_text, chunk_size=150, overlap=30)
print(f"Generating embeddings for {len(chunks)} chunks individually...")

payloads_to_upload = []

# Merge the API call and the Dictionary formatting into one loop
for idx, text_content in enumerate(chunks):
    
    # 1. Ask Gemini to embed just this ONE chunk
    response = client_gemini.models.embed_content(
        model="gemini-embedding-2",
        contents=text_content,
        config={"output_dimensionality": 768}
    )
    
    # 2. Extract the vector (Because we only sent one chunk, it's always at index [0])
    vector_coordinates = response.embeddings[0].values
    
    # 3. Build the Pinecone Dictionary Payload
    payloads_to_upload.append({
        "id": f"pdf_chunk_{idx}",
        "values": vector_coordinates,
        "metadata": {
            "source": pdf_file,
            "text": text_content 
        }
    })
    
    # 4. Pause for 1 second to prevent API rate-limit crashes
    time.sleep(1)

print("Executing cloud upload payload...")
# 5. Push the completed list of 24 dictionaries up to Pinecone
index.upsert(vectors=payloads_to_upload)
print("Database population complete. Your PDF is indexed and live!")
