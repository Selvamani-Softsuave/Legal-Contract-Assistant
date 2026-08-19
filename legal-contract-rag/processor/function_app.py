import os
import sys
# Add parent dir to sys.path so 'processor' is recognized as a module locally
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import azure.functions as func
import json
import logging
import os
from processor.services.chroma_service import ProcessorChromaService
from processor.services.document_processing_service import DocumentProcessingService
from azure.storage.blob import BlobServiceClient
import httpx

logger = logging.getLogger("document_processor")
app = func.FunctionApp()
chroma_service = ProcessorChromaService()

@app.function_name(name="VectorSearch")
@app.route(route="vector/search", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
def vector_search(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
        query_embedding = body.get("query_embedding")
        top_k = body.get("top_k", 5)
        contract_ids = body.get("contract_ids")
        document_id = body.get("document_id")

        if not query_embedding:
            return func.HttpResponse(
                json.dumps({"error": "query_embedding is required"}),
                status_code=400,
                mimetype="application/json"
            )

        results = chroma_service.similarity_search(
            query_embedding=query_embedding,
            top_k=top_k,
            contract_ids=contract_ids,
            document_id=document_id
        )
        return func.HttpResponse(
            json.dumps({"results": results}),
            status_code=200,
            mimetype="application/json"
        )
    except Exception as e:
        logger.error(f"Error in vector search API: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )

@app.function_name(name="VectorDelete")
@app.route(route="vector/delete", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
def vector_delete(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
        document_id = body.get("document_id")
        if not document_id:
            return func.HttpResponse(
                json.dumps({"error": "document_id is required"}),
                status_code=400,
                mimetype="application/json"
            )

        success = chroma_service.delete_document_vectors(document_id)
        return func.HttpResponse(
            json.dumps({"status": "success" if success else "not_found", "document_id": document_id}),
            status_code=200,
            mimetype="application/json"
        )
    except Exception as e:
        logger.error(f"Error in vector delete API: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )

@app.function_name(name="VectorHealth")
@app.route(route="vector/health", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET"])
def vector_health(req: func.HttpRequest) -> func.HttpResponse:
    health_info = chroma_service.get_health()
    return func.HttpResponse(
        json.dumps(health_info),
        status_code=200,
        mimetype="application/json"
    )

@app.function_name(name="LegalDocumentQueueTrigger")
@app.queue_trigger(arg_name="msg", queue_name="%QUEUE_NAME%", connection="AZURE_STORAGE_CONNECTION_STRING")
def process_document_queue(msg: func.QueueMessage) -> None:
    message_body = msg.get_body().decode('utf-8')
    logger.info(f"Received document processing queue message: {message_body}")
    
    payload = {}
    backend_url = os.environ.get("BACKEND_API_URL", "http://backend:8080")
    job_id = None
    document_id = None
    
    try:
        payload = json.loads(message_body)
        document_id = payload.get("documentId")
        operation = payload.get("operation", "PROCESS")
        job_id = payload.get("job_id")
        contract_id = payload.get("contract_id")
        blob_path = payload.get("blob_path")
        file_name = payload.get("file_name")
        
        logger.info(f"Processing document {document_id} (job {job_id}) with operation {operation}")

        if operation in ["PROCESS", "REPROCESS"]:
            # 1. Download file from blob storage
            conn_str = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
            blob_service_client = BlobServiceClient.from_connection_string(conn_str, api_version="2023-11-03")
            
            container_name = blob_path.split("/")[0] if "/" in blob_path else "legal-contracts"
            blob_name = blob_path.replace(f"{container_name}/", "")
            
            blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
            file_bytes = blob_client.download_blob().readall()
            
            # 2. Run Processing Service
            doc_service = DocumentProcessingService()
            doc_service.process_document(
                document_id=document_id,
                contract_id=contract_id,
                file_name=file_name,
                file_bytes=file_bytes,
                operation=operation
            )
            
        elif operation == "DELETE_INDEX":
            doc_service = DocumentProcessingService()
            doc_service.process_document(
                document_id=document_id,
                contract_id="", file_name="", file_bytes=b"", operation="DELETE_INDEX"
            )

        # 3. Notify backend of success
        if job_id:
            with httpx.Client() as client:
                client.patch(
                    f"{backend_url}/api/v1/processing/jobs/{job_id}/status",
                    json={"status": "Completed", "document_id": document_id}
                )
                
    except Exception as e:
        logger.error(f"Failed to process queue message: {e}")
        # Notify backend of failure
        if job_id:
            try:
                with httpx.Client() as client:
                    client.patch(
                        f"{backend_url}/api/v1/processing/jobs/{job_id}/status",
                        json={"status": "Failed", "error_message": str(e), "document_id": document_id}
                    )
            except Exception as patch_e:
                logger.error(f"Failed to send failure patch: {patch_e}")
