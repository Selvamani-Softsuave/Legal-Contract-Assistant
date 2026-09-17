import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  MCPDiscoveryResponse,
  MCPQueryRequest,
  MCPQueryResponse,
  MCPToolCallRequest,
  MCPToolCallResponse,
  MCPWireTraceResponse,
  AuditLogEntry,
  MCPErrorDemoResponse
} from '../models';

@Injectable({
  providedIn: 'root'
})
export class McpService {
  private apiUrl = '/api/v1/mcp';

  constructor(private http: HttpClient) {}

  getDiscovery(configMode: string = 'all'): Observable<MCPDiscoveryResponse> {
    const params = new HttpParams().set('config_mode', configMode);
    return this.http.get<MCPDiscoveryResponse>(`${this.apiUrl}/discovery`, { params });
  }

  queryAgent(req: MCPQueryRequest): Observable<MCPQueryResponse> {
    return this.http.post<MCPQueryResponse>(`${this.apiUrl}/query`, req);
  }

  callToolGateway(req: MCPToolCallRequest): Observable<MCPToolCallResponse> {
    return this.http.post<MCPToolCallResponse>(`${this.apiUrl}/call-tool`, req);
  }

  getWireTrace(): Observable<MCPWireTraceResponse> {
    return this.http.get<MCPWireTraceResponse>(`${this.apiUrl}/wire-trace`);
  }

  clearWireTrace(): Observable<any> {
    return this.http.delete(`${this.apiUrl}/wire-trace`);
  }

  getAuditLogs(limit: number = 50): Observable<AuditLogEntry[]> {
    const params = new HttpParams().set('limit', limit.toString());
    return this.http.get<AuditLogEntry[]>(`${this.apiUrl}/audit-logs`, { params });
  }

  getErrorDemo(): Observable<MCPErrorDemoResponse> {
    return this.http.get<MCPErrorDemoResponse>(`${this.apiUrl}/error-demo`);
  }
}
