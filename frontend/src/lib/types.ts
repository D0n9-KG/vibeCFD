export type TaskType =
  | "resistance"
  | "pressure_distribution"
  | "wake_field"
  | "drift_angle_force"
  | "near_free_surface"
  | "self_propulsion";

export type RunStatus =
  | "draft"
  | "awaiting_confirmation"
  | "queued"
  | "running"
  | "completed"
  | "cancelled"
  | "failed";

export type EventDetailValue = string | number | boolean | null;
export type ExecutionAttemptStatus = "running" | "completed" | "failed";

export interface CaseReference {
  title: string;
  source: string;
  url?: string | null;
}

export interface CaseCandidate {
  case_id: string;
  title: string;
  geometry_family: string;
  geometry_description: string;
  task_type: string;
  condition_tags: string[];
  input_requirements: string[];
  expected_outputs: string[];
  recommended_solver: string;
  mesh_strategy: string;
  bc_strategy: string;
  postprocess_steps: string[];
  validation_targets: string[];
  reference_sources: CaseReference[];
  reuse_role: string;
  linked_skills: string[];
  score: number;
  rationale: string;
}

export interface WorkflowStage {
  stage_id: string;
  title: string;
  description: string;
}

export interface WorkflowDraft {
  summary: string;
  assumptions: string[];
  recommended_case_ids: string[];
  linked_skills: string[];
  allowed_tools: string[];
  required_artifacts: string[];
  stages: WorkflowStage[];
}

export interface TimelineEvent {
  timestamp: string;
  stage: string;
  message: string;
  status: string;
}

export interface RunEvent {
  event_id: string;
  timestamp: string;
  event_type: string;
  stage: string;
  status: string;
  message: string;
  details: Record<string, EventDetailValue>;
}

export interface ExecutionAttempt {
  attempt_id: string;
  attempt_number: number;
  engine_name: string;
  status: ExecutionAttemptStatus;
  started_at: string;
  finished_at?: string | null;
  duration_seconds?: number | null;
  summary?: string | null;
  error_message?: string | null;
  failure_category?: string | null;
  failure_source?: string | null;
}

export interface ArtifactItem {
  label: string;
  category: string;
  relative_path: string;
  mime_type: string;
  url: string;
}

export interface TaskSubmission {
  task_description: string;
  task_type: TaskType;
  geometry_family_hint?: string | null;
  geometry_file_name?: string | null;
  operating_notes: string;
}

export interface RunSummary {
  run_id: string;
  status: RunStatus;
  current_stage: string;
  stage_label: string;
  created_at: string;
  updated_at: string;
  request: TaskSubmission;
  run_directory: string;
  geometry_check: string;
  candidate_cases: CaseCandidate[];
  selected_case?: CaseCandidate | null;
  workflow_draft?: WorkflowDraft | null;
  confirmed_at?: string | null;
  reviewer_notes?: string | null;
  timeline: TimelineEvent[];
  artifacts: ArtifactItem[];
  report_markdown?: string | null;
  metrics: Record<string, string | number>;
}
