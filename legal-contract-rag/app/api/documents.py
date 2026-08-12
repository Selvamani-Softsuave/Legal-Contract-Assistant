from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from typing import List
import shutil
import os
import uuid
from app.services.pdf_service import extract_text_from_pdf
from app.services.chunking_service import chunk_text
from app.services.embedding_service import EmbeddingService
from app.services.chroma_service import ChromaService
from app.models.schemas import UploadResponse, DocumentInfo
from app.config import config
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services (singleton pattern)
embedding_service = EmbeddingService()
chroma_service = ChromaService()

@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a PDF document, extract text, chunk, embed, and store in ChromaDB.
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Generate a unique document ID
    document_id = str(uuid.uuid4())
    
    # Save the file temporarily
    temp_file_path = f"./documents/{document_id}_{file.filename}"
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Error saving uploaded file: {e}")
        raise HTTPException(status_code=500, detail="Could not save uploaded file")
    finally:
        file.file.close()
    
    try:
        # Extract text from PDF
        text_by_page = extract_text_from_pdf(temp_file_path)
        if not text_by_page:
            raise HTTPException(status_code=400, detail="No text could be extracted from the PDF")
        
        # Count pages
        pages = len(text_by_page)
        
        # Chunk the text
        chunks = chunk_text(text_by_page)
        if not chunks:
            raise HTTPException(status_code=400, detail="No chunks created from the document")
        
        chunks_created = len(chunks)
        
        # Extract just the text for embedding
        chunk_texts = [chunk["text"] for chunk in chunks]
        
        # Generate embeddings
        try:
            embeddings = embedding_service.get_embeddings(chunk_texts)
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to generate embeddings: {str(e)}")
        
        # Store in ChromaDB
        try:
            chroma_service.add_document_chunks(
                chunks=chunks,
                embeddings=embeddings,
                document_id=document_id,
                document_name=file.filename
            )
        except Exception as e:
            logger.error(f"Error storing in ChromaDB: {e}")
            raise HTTPException(status_code=500, detail="Failed to store document in database")
        
        # Clean up the temporary file (optional: we might want to keep it)
        # For now, we'll keep it in the documents folder as per requirement
        # os.remove(temp_file_path)
        
        return UploadResponse(
            documentId=document_id,
            fileName=file.filename,
            pages=pages,
            chunksCreated=chunks_created,
            status="success"
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error during document upload: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
    finally:
        # Optionally remove the temporary file if we don't want to keep it
        # if os.path.exists(temp_file_path):
        #     os.remove(temp_file_path)
        pass

@router.get("/", response_model=List[DocumentInfo])
async def list_documents():
    """
    List all indexed documents.
    """
    try:
        documents = chroma_service.get_documents()
        return documents
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail="Could not retrieve documents")