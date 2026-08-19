export interface Contract {
    id: string;
    name: string;
    contract_number?: string;
    contract_type?: string;
    status: string;
    effective_date?: string;
    expiration_date?: string;
    governing_law?: string;
    jurisdiction?: string;
    version: number;
    description?: string;
    created_at: string;
    updated_at: string;
}

export interface ContractCreate {
    name: string;
    contract_number?: string;
    contract_type?: string;
    effective_date?: string;
    expiration_date?: string;
    governing_law?: string;
    jurisdiction?: string;
    description?: string;
}

export interface Document {
    id: string;
    contract_id: string;
    file_name: string;
    file_size: number;
    file_type: string;
    blob_path: string;
    page_count: number;
    status: string;
    created_at: string;
    updated_at: string;
}

export interface DocumentUploadResponse {
    documentId: string;
    contractId: string;
    fileName: string;
    fileSize: number;
    status: string;
    jobId: string;
    correlationId: string;
    message: string;
}

export interface SourceDTO {
    chunk_id?: string;
    document_name: string;
    page_number?: number;
    section?: string;
    clause?: string;
    relevance_score?: number;
}

export interface MessageResponse {
    id: string;
    conversation_id: string;
    role: 'user' | 'assistant';
    content: string;
    sources: SourceDTO[];
    created_at: string;
}

export interface Conversation {
    id: string;
    title: string;
    scoped_contract_ids?: string[];
    created_at: string;
    updated_at: string;
}

export interface ChatResponse {
    conversation_id: string;
    message: MessageResponse;
    answer: string;
    sources: SourceDTO[];
}
