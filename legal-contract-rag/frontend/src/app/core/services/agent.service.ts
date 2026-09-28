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
    InjectionAttackResponse,
    W10RaceResponse,
    HandoffLogResponse,
    WorkerFailureResponse,
    A2AAgentCardResponse
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

    // ─── Week 10 Endpoints (Multi-Agent Race, Failure Injection, A2A) ──────────

    runW10Race(): Observable<W10RaceResponse> {
        return this.http.post<W10RaceResponse>(`${this.apiUrl}/w10-race`, {});
    }

    injectWorkerFailure(
        caseId: string = 'RACE-005',
        question: string = 'What is the exact notice deadline for termination for Material Breach under the Final Executed Agreement?'
    ): Observable<WorkerFailureResponse> {
        return this.http.post<WorkerFailureResponse>(
            `${this.apiUrl}/w10-inject-failure?case_id=${encodeURIComponent(caseId)}&question=${encodeURIComponent(question)}`,
            {}
        );
    }

    getW10HandoffLogs(): Observable<HandoffLogResponse> {
        return this.http.get<HandoffLogResponse>(`${this.apiUrl}/w10-handoff-logs`);
    }

    getW10AgentCard(): Observable<A2AAgentCardResponse> {
        return this.http.get<A2AAgentCardResponse>(`${this.apiUrl}/w10-agent-card`);
    }
}

