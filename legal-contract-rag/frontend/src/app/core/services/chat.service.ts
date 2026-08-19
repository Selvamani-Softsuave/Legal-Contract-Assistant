import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Conversation, ChatResponse } from '../models';

@Injectable({
    providedIn: 'root'
})
export class ChatService {
    private apiUrl = '/api/v1/chat';

    constructor(private http: HttpClient) { }

    createConversation(title?: string, scopedContractIds?: string[]): Observable<Conversation> {
        return this.http.post<Conversation>(`${this.apiUrl}/conversations`, {
            title: title || 'New Conversation',
            scoped_contract_ids: scopedContractIds
        });
    }

    getConversations(): Observable<Conversation[]> {
        return this.http.get<Conversation[]>(`${this.apiUrl}/conversations`);
    }

    sendMessage(conversationId: string, question: string, scopedContractIds?: string[]): Observable<ChatResponse> {
        return this.http.post<ChatResponse>(`${this.apiUrl}/conversations/${conversationId}/messages`, {
            question,
            scoped_contract_ids: scopedContractIds
        });
    }
}
