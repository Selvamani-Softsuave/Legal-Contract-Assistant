import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AgentService } from '../../core/services/agent.service';
import {
    AgentQueryResponse,
    RaceDatasetItem,
    RaceRunResponse,
    ToolDefinition,
    TrajectoryEvaluationResponse,
    TrajectoryCaseResult,
    MitigationBenchmarkResponse,
    InjectionAttackResponse
} from '../../core/models';

@Component({
    selector: 'app-agent-lab',
    standalone: true,
    imports: [CommonModule, FormsModule],
    templateUrl: './agent-lab.component.html',
    styleUrls: ['./agent-lab.component.scss']
})
export class AgentLabComponent implements OnInit {
    activeSubTab: 'playground' | 'race' | 'trajectory' | 'injection' | 'tools' = 'playground';
    
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

    constructor(private agentService: AgentService) {}

    ngOnInit(): void {
        this.loadDataset();
        this.loadTools();
    }

    loadDataset(): void {
        this.agentService.getRaceDataset().subscribe({
            next: (data) => (this.raceDataset = data),
            error: (err) => console.error('Failed to load race dataset:', err)
        });
    }

    loadTools(): void {
        this.agentService.getTools().subscribe({
            next: (data) => (this.tools = data),
            error: (err) => console.error('Failed to load tools:', err)
        });
    }

    selectPresetQuestion(item: RaceDatasetItem): void {
        this.question = item.question;
        this.errorMessage = null;
    }

    runQuery(): void {
        if (!this.question.trim()) return;

        this.isLoading = true;
        this.errorMessage = null;

        this.agentService.query({
            question: this.question,
            mode: this.mode,
            use_live_llm: this.useLiveLlm,
            max_iterations: this.maxIterations,
            max_tokens: this.maxTokens,
            max_cost_usd: this.maxCostUsd,
            max_wall_clock_seconds: this.maxTimeoutSec
        }).subscribe({
            next: (res) => {
                this.queryResponse = res;
                this.isLoading = false;
            },
            error: (err) => {
                this.errorMessage = err.error?.detail || err.message || 'Failed to execute query';
                this.isLoading = false;
            }
        });
    }

    runFullRace(): void {
        this.isRaceRunning = true;
        this.errorMessage = null;

        this.agentService.runRace(this.useLiveLlm).subscribe({
            next: (res) => {
                this.raceResponse = res;
                this.isRaceRunning = false;
            },
            error: (err) => {
                this.errorMessage = err.error?.detail || err.message || 'Failed to run race benchmark';
                this.isRaceRunning = false;
            }
        });
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

    getCategoryBadgeClass(category: string): string {
        switch (category) {
            case 'DIRECT_LOOKUP': return 'badge-direct';
            case 'MULTI_HOP_DEPENDENT': return 'badge-multihop';
            case 'VERSION_COMPARISON': return 'badge-version';
            case 'BUDGET_STRESS_CIRCULAR': return 'badge-stress';
            default: return 'badge-default';
        }
    }
}
