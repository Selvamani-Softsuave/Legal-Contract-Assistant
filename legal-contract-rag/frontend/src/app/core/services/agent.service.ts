import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
    AgentQueryRequest,
    AgentQueryResponse,
    RaceDatasetItem,
    RaceRunResponse,
    ToolDefinition,
    TrajectoryEvaluationResponse,
    MitigationBenchmarkResponse,
    InjectionAttackResponse
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

    // ─── Week 8 Endpoints ────────────────────────────────────────────────────

    runTrajectoryEval(): Observable<TrajectoryEvaluationResponse> {
        return this.http.get<TrajectoryEvaluationResponse>(`${this.apiUrl}/trajectory-eval`);
    }

    runMitigationBenchmark(): Observable<MitigationBenchmarkResponse> {
        return this.http.post<MitigationBenchmarkResponse>(`${this.apiUrl}/mitigation-benchmark`, {});
    }

    runInjectionSimulation(question: string = 'Under what conditions can the agreement be terminated?'): Observable<InjectionAttackResponse> {
        return this.http.post<InjectionAttackResponse>(`${this.apiUrl}/injection-attack?question=${encodeURIComponent(question)}`, {});
    }
}
