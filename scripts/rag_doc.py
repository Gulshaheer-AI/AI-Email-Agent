import os
from pypdf import PdfReader

def extract_text_from_pdf(pdf_path: str) -> str:
    """Opens a local PDF and extracts all clean text layer data page by page."""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Could not locate PDF at: {pdf_path}")
        
    reader = PdfReader(pdf_path)
    full_text = []
    
    # Loop through every page object sequentially
    for page_num, page in enumerate(reader.pages):
        text = page.extract_text()
        if text: # Ensure the page isn't empty or an un-selectable image
            full_text.append(text)
            
    # Combine all pages using standard white spaces
    return "\n".join(full_text)

def sliding_window_chunker(raw_text: str, chunk_size: int = 150, overlap: int = 30) -> list[str]:
    """Splits text into clear strings of word blocks with explicit sliding overlaps."""
    words = raw_text.split()
    chunks = []
    
    # Define step movement (Size minus the overlap window)
    step = chunk_size - overlap
    
    # Prevent infinite loops if configuration parameters are invalid
    if step <= 0:
        raise ValueError("Chunk size must be significantly larger than the overlap.")

    for i in range(0, len(words), step):
        # Extract the slice slice of words
        segment = words[i : i + chunk_size]
        
        # Reconstruct into a coherent text chunk string
        chunk_string = " ".join(segment)
        chunks.append(chunk_string)
        
    return chunks

# Test the extraction block immediately
if __name__ == "__main__":
    print("Parsing target_document.pdf...")
    raw_document_content = extract_text_from_pdf("target_document.pdf")
    
    print("Processing chunk transformations...")
    processed_chunks = sliding_window_chunker(raw_document_content, chunk_size=100, overlap=25)
    
    print(f"Extraction Complete! Generated {len(processed_chunks)} individual text chunks.")
    print(f"Sample Chunk 0 Check:\n{processed_chunks[0][:150]}...")