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
    contract_name?: string;
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

export interface ToolDefinition {
    name: string;
    description: string;
    parameters: any;
}

export interface AgentTraceStep {
    lap: number;
    thought: string;
    action_tool?: string;
    action_args?: Record<string, any>;
    observation?: string;
}

export interface BudgetStatus {
    iterations: number;
    max_iterations: number;
    total_tokens: number;
    max_tokens: number;
    total_cost_usd: number;
    max_cost_usd: number;
    elapsed_seconds: number;
    max_wall_clock_seconds: number;
    is_breached: boolean;
    exceeded_reason?: string;
}

export interface ReActResult {
    answer: string;
    trace_log: AgentTraceStep[];
    budget: BudgetStatus;
    clean_termination_log?: string;
    tokens_used: number;
    cost_usd: number;
    latency_ms: number;
}

export interface FixedWorkflowStep {
    step: number;
    action: string;
    target: string;
    raw_response_snippet: string;
}

export interface WorkflowResult {
    answer: string;
    steps_executed: FixedWorkflowStep[];
    tokens_used: number;
    cost_usd: number;
    latency_ms: number;
    success: boolean;
}

export interface ComparisonSummary {
    latency_diff_ms: number;
    token_diff: number;
    cost_diff_usd: number;
    winner: string;
    reason: string;
}

export interface AgentQueryRequest {
    question: string;
    contract_id?: string;
    mode?: 'react' | 'workflow' | 'both';
    use_live_llm?: boolean;
    max_iterations?: number;
    max_tokens?: number;
    max_cost_usd?: number;
    max_wall_clock_seconds?: number;
}

export interface AgentQueryResponse {
    question: string;
    contract_id: string;
    mode: string;
    react_result?: ReActResult;
    workflow_result?: WorkflowResult;
    comparison?: ComparisonSummary;
}

export interface RaceDatasetItem {
    id: string;
    category: string;
    question: string;
    expected_answer: string;
    rationale: string;
}

export interface RaceItemResult {
    id: string;
    category: string;
    question: string;
    expected_answer: string;
    agent_answer: string;
    agent_passed: boolean;
    agent_tokens: number;
    agent_latency_ms: number;
    agent_cost_usd: number;
    agent_iterations: number;
    workflow_answer: string;
    workflow_passed: boolean;
    workflow_tokens: number;
    workflow_latency_ms: number;
    workflow_cost_usd: number;
}

export interface RaceRunResponse {
    total_cases: number;
    agent_pass_rate_pct: number;
    workflow_pass_rate_pct: number;
    agent_total_tokens: number;
    workflow_total_tokens: number;
    agent_total_cost_usd: number;
    workflow_total_cost_usd: number;
    results: RaceItemResult[];
    verdict: string;
}

// ─── Week 8 Trajectory Evaluation & Prompt Injection Interfaces ───────────────

export interface TrajectoryStepAnalysis {
    lap: number;
    tool_called?: string;
    args: Record<string, any>;
    is_tool_legitimate: boolean;
    are_args_valid: boolean;
    invalid_arg_reason?: string;
    failure_mode: string;
}

export interface TrajectoryCaseResult {
    case_id: string;
    question: string;
    outcome_passed: boolean;
    trajectory_passed: boolean;
    is_right_answer_wrong_path: boolean;
    actual_sequence: string[];
    allowed_sequences: string[][];
    tool_choice_accuracy: number;
    argument_validity_rate: number;
    step_efficiency: number;
    latency_seconds: number;
    total_tokens: number;
    cost_usd: number;
    detected_failure_modes: string[];
    step_details: TrajectoryStepAnalysis[];
    notes?: string;
}

export interface CostVariance {
    mean: number;
    p50: number;
    max: number;
    total: number;
}

export interface LatencyVariance {
    p50: number;
    max: number;
}

export interface TrajectoryEvaluationResponse {
    total_cases: number;
    outcome_pass_rate_pct: number;
    trajectory_pass_rate_pct: number;
    outcome_vs_trajectory_gap_pct: number;
    right_answer_wrong_path_count: number;
    tool_choice_accuracy_pct: number;
    argument_validity_rate_pct: number;
    step_efficiency: number;
    cost_usd: CostVariance;
    latency_seconds: LatencyVariance;
    total_tokens_sum: number;
    failure_mode_counts: Record<string, number>;
    cases: TrajectoryCaseResult[];
    top_right_answer_wrong_path_case?: TrajectoryCaseResult;
}

export interface RegressionRow {
    failure_mode: string;
    before_count: number;
    after_count: number;
    status: 'IMPROVED' | 'REGRESSED' | 'UNCHANGED';
}

export interface MitigationPricePaid {
    added_p50_latency_seconds: number;
    added_cumulative_tokens: number;
    added_cost_per_question_usd: number;
}

export interface MitigationBenchmarkResponse {
    mitigation_applied: string;
    top_failure_mode: string;
    top_mode_count_before: number;
    top_mode_count_after: number;
    price_paid: MitigationPricePaid;
    baseline_summary: any;
    mitigated_summary: any;
    regression_table: RegressionRow[];
}

export interface InjectionAttackResponse {
    attack_payload: string;
    target_question: string;
    unprotected_response: string;
    unprotected_hijacked: boolean;
    defended_response: string;
    defended_hijacked: boolean;
    defense_interceptions: string[];
    guardrail_latency_ms: number;
    guardrail_overhead_tokens: number;
    security_verdict: string;
}
