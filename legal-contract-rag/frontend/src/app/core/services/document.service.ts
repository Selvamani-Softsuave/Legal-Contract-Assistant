import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Document, DocumentUploadResponse } from '../models';

@Injectable({
    providedIn: 'root'
})
export class DocumentService {
    private apiUrl = '/api/v1/documents';

    constructor(private http: HttpClient) { }

    uploadDocument(contractId: string, file: File): Observable<DocumentUploadResponse> {
        const formData = new FormData();
        formData.append('contract_id', contractId);
        formData.append('file', file);
        return this.http.post<DocumentUploadResponse>(`${this.apiUrl}/upload`, formData);
    }

    getContractDocuments(contractId: string): Observable<Document[]> {
        return this.http.get<Document[]>(`${this.apiUrl}/contract/${contractId}`);
    }

    reprocessDocument(documentId: string): Observable<DocumentUploadResponse> {
        return this.http.post<DocumentUploadResponse>(`${this.apiUrl}/${documentId}/reprocess`, {});
    }

    deleteDocument(documentId: string): Observable<any> {
        return this.http.delete<any>(`${this.apiUrl}/${documentId}`);
    }

    getJobStatus(jobId: string): Observable<any> {
        return this.http.get<any>(`/api/v1/processing/jobs/${jobId}`);
    }
}
