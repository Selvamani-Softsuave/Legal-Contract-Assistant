import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AgentService } from '../../core/services/agent.service';
import { McpService } from '../../core/services/mcp.service';
import {
    AgentQueryResponse,
    RaceDatasetItem,
    RaceRunResponse,
    ToolDefinition,
    TrajectoryEvaluationResponse,
    TrajectoryCaseResult,
    MitigationBenchmarkResponse,
    InjectionAttackResponse,
    MCPDiscoveryResponse,
    MCPQueryResponse,
    MCPToolCallResponse,
    MCPWireTraceResponse,
    AuditLogEntry,
    MCPErrorDemoResponse,
    W10RaceResponse,
    W10CaseResult,
    HandoffLogResponse,
    WorkerFailureResponse,
    A2AAgentCardResponse
} from '../../core/models';

@Component({
    selector: 'app-agent-lab',
    standalone: true,
    imports: [CommonModule, FormsModule],
    templateUrl: './agent-lab.component.html',
    styleUrls: ['./agent-lab.component.scss']
})
export class AgentLabComponent implements OnInit {
    activeSubTab: 'playground' | 'race' | 'trajectory' | 'injection' | 'tools' | 'mcp' | 'w10-race' = 'playground';
    
    // Playground Form
    question: string = 'What is the exact notice deadline for termination for Material Breach under the Final Executed Agreement?';
    mode: 'both' | 'react' | 'workflow' = 'both';
    useLiveLlm: boolean = false;
    maxIterations: number = 5;
    maxTokens: number = 8000;
    maxCostUsd: number = 0.05;
    maxTimeoutSec: number = 20;

    // Loading & Data States
    isLoading: boolean = false;
    isRaceRunning: boolean = false;
    queryResponse: AgentQueryResponse | null = null;
    raceDataset: RaceDatasetItem[] = [];
    raceResponse: RaceRunResponse | null = null;
    tools: ToolDefinition[] = [];
    errorMessage: string | null = null;

    // ─── Week 8 Trajectory Evaluation & Prompt Injection States ───────────────
    isTrajectoryRunning: boolean = false;
    trajectoryResponse: TrajectoryEvaluationResponse | null = null;
    selectedTrajectoryCase: TrajectoryCaseResult | null = null;

    isMitigationRunning: boolean = false;
    mitigationResponse: MitigationBenchmarkResponse | null = null;

    isInjectionRunning: boolean = false;
    injectionQuestion: string = 'Under what conditions can the agreement be terminated?';
    injectionResponse: InjectionAttackResponse | null = null;

    // ─── Week 9 MCP (Model Context Protocol) & Gateway States ─────────────────
    mcpConfigMode: 'all' | 'server1_only' = 'all';
    mcpDiscovery: MCPDiscoveryResponse | null = null;
    isMcpLoading: boolean = false;

    mcpQueryText: string = 'Find dispute resolution procedures under Clause 12.4 of CNT-MAIN-2024';
    mcpQueryContractId: string = 'CNT-MAIN-2024';
    mcpQueryResponse: MCPQueryResponse | null = null;
    isMcpQueryRunning: boolean = false;

    mcpWireTrace: MCPWireTraceResponse | null = null;
    isWireLoading: boolean = false;

    mcpErrorDemo: MCPErrorDemoResponse | null = null;
    isErrorDemoLoading: boolean = false;

    mcpGatewayLogs: AuditLogEntry[] = [];
    selectedGatewayRole: string = 'legal_counsel';
    selectedGatewayTool: string = 'get_clause';
    gatewayContractId: string = 'CNT-MAIN-2024';
    gatewayClauseNum: string = '8.1';
    gatewayTestResult: MCPToolCallResponse | null = null;
    isGatewayTesting: boolean = false;

    // ─── Week 10 Multi-Agent Race & A2A States ────────────────────────────────
    isW10RaceRunning: boolean = false;
    w10RaceResponse: W10RaceResponse | null = null;
    selectedW10Case: W10CaseResult | null = null;

    isFailureInjecting: boolean = false;
    failureResponse: WorkerFailureResponse | null = null;
    failureCaseId: string = 'RACE-005';
    failureQuestion: string = 'What is the exact notice deadline for termination for Material Breach under the Final Executed Agreement?';

    isHandoffLogsLoading: boolean = false;
    handoffLogResponse: HandoffLogResponse | null = null;

    isAgentCardLoading: boolean = false;
    agentCardResponse: A2AAgentCardResponse | null = null;
    isAgentCardModalOpen: boolean = false;

    constructor(
        private agentService: AgentService,
        private mcpService: McpService
    ) {}

    ngOnInit(): void {
        this.loadDataset();
        this.loadTools();
        this.loadMcpDiscovery();
    }

    loadDataset(): void {
        this.agentService.getRaceDataset().subscribe({
            next: (data: RaceDatasetItem[]) => this.raceDataset = data,
            error: (err: any) => console.error('Failed to load race dataset', err)
        });
    }

    loadTools(): void {
        this.agentService.getTools().subscribe({
            next: (data: ToolDefinition[]) => this.tools = data,
            error: (err: any) => console.error('Failed to load agent tools', err)
        });
    }

    selectPresetQuestion(item: RaceDatasetItem): void {
        this.question = item.question;
        this.activeSubTab = 'playground';
    }

    selectDatasetItem(item: RaceDatasetItem): void {
        this.selectPresetQuestion(item);
    }

    runQuery(): void {
        if (!this.question.trim()) return;

        this.isLoading = true;
        this.errorMessage = null;
        this.queryResponse = null;

        this.agentService.query({
            question: this.question,
            mode: this.mode,
            use_live_llm: this.useLiveLlm,
            max_iterations: this.maxIterations,
            max_tokens: this.maxTokens,
            max_cost_usd: this.maxCostUsd,
            max_wall_clock_seconds: this.maxTimeoutSec
        }).subscribe({
            next: (res: AgentQueryResponse) => {
                this.queryResponse = res;
                this.isLoading = false;
            },
            error: (err: any) => {
                this.errorMessage = err.error?.detail || err.message || 'Agent query execution failed';
                this.isLoading = false;
            }
        });
    }

    runAgentQuery(): void {
        this.runQuery();
    }

    runFullRace(): void {
        this.isRaceRunning = true;
        this.errorMessage = null;
        this.raceResponse = null;

        this.agentService.runRace(this.useLiveLlm).subscribe({
            next: (res: RaceRunResponse) => {
                this.raceResponse = res;
                this.isRaceRunning = false;
            },
            error: (err: any) => {
                this.errorMessage = err.error?.detail || err.message || 'Benchmark race failed';
                this.isRaceRunning = false;
            }
        });
    }

    runRace(): void {
        this.runFullRace();
    }

    // ─── Week 8 Trajectory Evaluation Handlers ────────────────────────────────

    runTrajectoryEval(): void {
        this.isTrajectoryRunning = true;
        this.errorMessage = null;

        this.agentService.runTrajectoryEval().subscribe({
            next: (res) => {
                this.trajectoryResponse = res;
                if (res.cases && res.cases.length > 0) {
                    this.selectedTrajectoryCase = res.top_right_answer_wrong_path_case || res.cases[0];
                }
                this.isTrajectoryRunning = false;
            },
            error: (err) => {
                this.errorMessage = err.error?.detail || err.message || 'Failed to run trajectory evaluation';
                this.isTrajectoryRunning = false;
            }
        });
    }

    selectTrajectoryCase(c: TrajectoryCaseResult): void {
        this.selectedTrajectoryCase = c;
    }

    runMitigationBenchmark(): void {
        this.isMitigationRunning = true;
        this.errorMessage = null;

        this.agentService.runMitigationBenchmark().subscribe({
            next: (res) => {
                this.mitigationResponse = res;
                this.isMitigationRunning = false;
            },
            error: (err) => {
                this.errorMessage = err.error?.detail || err.message || 'Failed to run mitigation benchmark';
                this.isMitigationRunning = false;
            }
        });
    }

    runInjectionTest(): void {
        this.isInjectionRunning = true;
        this.errorMessage = null;

        this.agentService.runInjectionSimulation(this.injectionQuestion).subscribe({
            next: (res) => {
                this.injectionResponse = res;
                this.isInjectionRunning = false;
            },
            error: (err) => {
                this.errorMessage = err.error?.detail || err.message || 'Failed to run injection test';
                this.isInjectionRunning = false;
            }
        });
    }

    // ─── Week 9 MCP Protocol Handlers ────────────────────────────────────────

    loadMcpDiscovery(): void {
        this.isMcpLoading = true;
        this.mcpService.getDiscovery(this.mcpConfigMode).subscribe({
            next: (res) => {
                this.mcpDiscovery = res;
                this.isMcpLoading = false;
            },
            error: (err) => {
                console.error('Failed to load MCP discovery', err);
                this.isMcpLoading = false;
            }
        });
    }

    switchMcpConfig(mode: 'all' | 'server1_only'): void {
        this.mcpConfigMode = mode;
        this.loadMcpDiscovery();
    }

    runMcpAgentQuery(): void {
        if (!this.mcpQueryText.trim()) return;

        this.isMcpQueryRunning = true;
        this.errorMessage = null;
        this.mcpQueryResponse = null;

        this.mcpService.queryAgent({
            query: this.mcpQueryText,
            contract_id: this.mcpQueryContractId,
            server_config: this.mcpConfigMode
        }).subscribe({
            next: (res) => {
                this.mcpQueryResponse = res;
                this.isMcpQueryRunning = false;
                // Automatically refresh wire trace and audit logs
                this.loadWireTrace();
                this.loadGatewayAuditLogs();
            },
            error: (err) => {
                this.errorMessage = err.error?.detail || err.message || 'MCP Agent query failed';
                this.isMcpQueryRunning = false;
            }
        });
    }

    loadWireTrace(): void {
        this.isWireLoading = true;
        this.mcpService.getWireTrace().subscribe({
            next: (res) => {
                this.mcpWireTrace = res;
                this.isWireLoading = false;
            },
            error: (err) => {
                console.error('Failed to load wire trace', err);
                this.isWireLoading = false;
            }
        });
    }

    clearWireTrace(): void {
        this.mcpService.clearWireTrace().subscribe({
            next: () => {
                this.mcpWireTrace = null;
                this.loadWireTrace();
            }
        });
    }

    loadErrorDemo(): void {
        this.isErrorDemoLoading = true;
        this.mcpService.getErrorDemo().subscribe({
            next: (res) => {
                this.mcpErrorDemo = res;
                this.isErrorDemoLoading = false;
            },
            error: (err) => {
                console.error('Failed to load error demo', err);
                this.isErrorDemoLoading = false;
            }
        });
    }

    loadGatewayAuditLogs(): void {
        this.mcpService.getAuditLogs(30).subscribe({
            next: (res) => this.mcpGatewayLogs = res,
            error: (err) => console.error('Failed to load audit logs', err)
        });
    }

    testGatewayTool(): void {
        this.isGatewayTesting = true;
        this.gatewayTestResult = null;

        const args: Record<string, any> = { contract_id: this.gatewayContractId };
        if (this.selectedGatewayTool === 'get_clause') {
            args['clause_number'] = this.gatewayClauseNum;
        }

        this.mcpService.callToolGateway({
            tool_name: this.selectedGatewayTool,
            arguments: args,
            role: this.selectedGatewayRole,
            caller: `${this.selectedGatewayRole}_tester@enterprise.com`
        }).subscribe({
            next: (res) => {
                this.gatewayTestResult = res;
                this.isGatewayTesting = false;
                this.loadGatewayAuditLogs();
            },
            error: (err) => {
                this.errorMessage = err.error?.detail || err.message || 'Gateway call failed';
                this.isGatewayTesting = false;
            }
        });
    }

    getCategoryBadgeClass(category: string): string {
        switch (category) {
            case 'DIRECT_LOOKUP': return 'badge-direct';
            case 'MULTI_HOP_DEPENDENT': return 'badge-multihop';
            case 'VERSION_COMPARISON': return 'badge-version';
            case 'BUDGET_STRESS_CIRCULAR': return 'badge-stress';
            default: return 'badge-default';
        }
    }

    // ─── Week 10 Multi-Agent Methods ──────────────────────────────────────────

    runW10Race(): void {
        this.isW10RaceRunning = true;
        this.errorMessage = null;

        this.agentService.runW10Race().subscribe({
            next: (res) => {
                this.w10RaceResponse = res;
                this.isW10RaceRunning = false;
                if (res.cases && res.cases.length > 0) {
                    this.selectedW10Case = res.cases[0];
                }
            },
            error: (err) => {
                this.errorMessage = err.error?.detail || err.message || 'Week 10 race benchmark failed';
                this.isW10RaceRunning = false;
            }
        });
    }

    runFailureInjection(): void {
        this.isFailureInjecting = true;
        this.errorMessage = null;

        this.agentService.injectWorkerFailure(this.failureCaseId, this.failureQuestion).subscribe({
            next: (res) => {
                this.failureResponse = res;
                this.isFailureInjecting = false;
            },
            error: (err) => {
                this.errorMessage = err.error?.detail || err.message || 'Worker failure injection failed';
                this.isFailureInjecting = false;
            }
        });
    }

    loadW10HandoffLogs(): void {
        this.isHandoffLogsLoading = true;
        this.agentService.getW10HandoffLogs().subscribe({
            next: (res) => {
                this.handoffLogResponse = res;
                this.isHandoffLogsLoading = false;
            },
            error: (err) => {
                this.errorMessage = err.error?.detail || err.message || 'Failed to fetch handoff logs';
                this.isHandoffLogsLoading = false;
            }
        });
    }

    openAgentCardModal(): void {
        this.isAgentCardModalOpen = true;
        if (!this.agentCardResponse) {
            this.isAgentCardLoading = true;
            this.agentService.getW10AgentCard().subscribe({
                next: (res) => {
                    this.agentCardResponse = res;
                    this.isAgentCardLoading = false;
                },
                error: (err) => {
                    this.errorMessage = err.error?.detail || err.message || 'Failed to fetch A2A AgentCard';
                    this.isAgentCardLoading = false;
                }
            });
        }
    }

    closeAgentCardModal(): void {
        this.isAgentCardModalOpen = false;
    }

    selectW10Case(item: W10CaseResult): void {
        this.selectedW10Case = item;
    }
}
