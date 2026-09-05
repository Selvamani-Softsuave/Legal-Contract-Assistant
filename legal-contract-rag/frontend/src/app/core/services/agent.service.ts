import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
    AgentQueryRequest,
    AgentQueryResponse,
    RaceDatasetItem,
    RaceRunResponse,
    ToolDefinition
} from '../models';

@Injectable({
    providedIn: 'root'
})
export class AgentService {
    private apiUrl = '/api/v1/agent';

    constructor(private http: HttpClient) { }

    query(request: AgentQueryRequest): Observable<AgentQueryResponse> {
        return this.http.post<AgentQueryResponse>(`${this.apiUrl}/query`, request);
    }

    getTools(): Observable<ToolDefinition[]> {
        return this.http.get<ToolDefinition[]>(`${this.apiUrl}/tools`);
    }

    getRaceDataset(): Observable<RaceDatasetItem[]> {
        return this.http.get<RaceDatasetItem[]>(`${this.apiUrl}/race-dataset`);
    }

    runRace(useLiveLlm: boolean = false): Observable<RaceRunResponse> {
        return this.http.post<RaceRunResponse>(`${this.apiUrl}/run-race?use_live_llm=${useLiveLlm}`, {});
    }
}
