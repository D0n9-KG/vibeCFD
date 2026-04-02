export type SubmarineSimulationRequirements = {
  inlet_velocity_mps?: number | null;
  fluid_density_kg_m3?: number | null;
  kinematic_viscosity_m2ps?: number | null;
  end_time_seconds?: number | null;
  delta_t_seconds?: number | null;
  write_interval_steps?: number | null;
};

export type SubmarineExecutionOutlineItem = {
  role_id?: string | null;
  owner?: string | null;
  goal?: string | null;
  status?: string | null;
  target_skills?: string[] | null;
};

export type SubmarineScientificVerificationRequirementPayload = {
  requirement_id?: string | null;
  label?: string | null;
  summary_zh?: string | null;
  check_type?: string | null;
  required_artifacts?: string[] | null;
  force_coefficient?: string | null;
  minimum_history_samples?: number | null;
  max_tail_relative_spread?: number | null;
  max_value?: number | null;
};

export type SubmarineRequestedOutputPayload = {
  output_id?: string | null;
  label?: string | null;
  requested_label?: string | null;
  status?: string | null;
  support_level?: string | null;
  postprocess_spec?: Record<string, unknown> | null;
  notes?: string | null;
};

export type SubmarineGeometryFinding = {
  finding_id?: string | null;
  category?: string | null;
  severity?: string | null;
  summary_zh?: string | null;
  evidence?: Record<string, unknown> | null;
};

export type SubmarineGeometryScaleAssessment = {
  raw_length_value?: number | null;
  normalized_length_m?: number | null;
  applied_scale_factor?: number | null;
  heuristic?: string | null;
  severity?: string | null;
  summary_zh?: string | null;
  family_default_length_m?: number | null;
  relative_difference?: number | null;
  evidence?: Record<string, unknown> | null;
};

export type SubmarineGeometryReferenceValueSuggestion = {
  suggestion_id?: string | null;
  quantity?: string | null;
  value?: number | null;
  unit?: string | null;
  confidence?: string | null;
  source?: string | null;
  justification?: string | null;
  summary_zh?: string | null;
  is_low_risk?: boolean | null;
  requires_confirmation?: boolean | null;
  evidence?: Record<string, unknown> | null;
};

export type SubmarineCalculationPlanItem = {
  item_id?: string | null;
  category?: string | null;
  label?: string | null;
  proposed_value?: unknown;
  proposed_range?: unknown[] | Record<string, unknown> | null;
  unit?: string | null;
  source_label?: string | null;
  source_url?: string | null;
  confidence?: string | null;
  applicability_conditions?: string[] | null;
  evidence_gap_note?: string | null;
  origin?: string | null;
  approval_state?: string | null;
  requires_immediate_confirmation?: boolean | null;
  researcher_note?: string | null;
};

export type SubmarineSelectedCaseProvenanceSummary = {
  case_id?: string | null;
  title?: string | null;
  source_label?: string | null;
  source_url?: string | null;
  source_type?: string | null;
  applicability_conditions?: string[] | null;
  confidence_note?: string | null;
  is_placeholder?: boolean | null;
  evidence_gap_note?: string | null;
  acceptance_profile_summary_zh?: string | null;
  benchmark_metric_ids?: string[] | null;
};

export type SubmarineDesignBriefPayload = {
  report_title?: string;
  summary_zh?: string;
  task_description?: string;
  task_type?: string;
  confirmation_status?: "draft" | "confirmed" | string;
  geometry_virtual_path?: string | null;
  geometry_family_hint?: string | null;
  selected_case_id?: string | null;
  simulation_requirements?: SubmarineSimulationRequirements | null;
  expected_outputs?: string[] | null;
  scientific_verification_requirements?:
    | SubmarineScientificVerificationRequirementPayload[]
    | null;
  requested_outputs?: SubmarineRequestedOutputPayload[] | null;
  user_constraints?: string[] | null;
  open_questions?: string[] | null;
  execution_outline?: SubmarineExecutionOutlineItem[] | null;
  calculation_plan?: SubmarineCalculationPlanItem[] | null;
  requires_immediate_confirmation?: boolean | null;
  review_status?: string | null;
  next_recommended_stage?: string | null;
};

export type SubmarineBenchmarkComparisonPayload = {
  metric_id?: string | null;
  quantity?: string | null;
  status?: string | null;
  summary_zh?: string | null;
  detail?: string | null;
  observed_value?: number | null;
  reference_value?: number | null;
  absolute_error?: number | null;
  relative_error?: number | null;
  relative_tolerance?: number | null;
  target_inlet_velocity_mps?: number | null;
  observed_inlet_velocity_mps?: number | null;
  source_label?: string | null;
  source_url?: string | null;
};

export type SubmarineAcceptanceAssessment = {
  status?: string | null;
  confidence?: string | null;
  blocking_issues?: string[] | null;
  warnings?: string[] | null;
  passed_checks?: string[] | null;
  benchmark_comparisons?: SubmarineBenchmarkComparisonPayload[] | null;
};

export type SubmarineScientificVerificationRequirementAssessmentPayload = {
  requirement_id?: string | null;
  label?: string | null;
  status?: string | null;
  detail?: string | null;
};

export type SubmarineScientificVerificationAssessment = {
  status?: string | null;
  confidence?: string | null;
  blocking_issues?: string[] | null;
  missing_evidence?: string[] | null;
  passed_requirements?: string[] | null;
  requirements?:
    | SubmarineScientificVerificationRequirementAssessmentPayload[]
    | null;
};

export type SubmarineStabilityEvidenceForceTailSamplePayload = {
  time?: number | null;
  value?: number | null;
};

export type SubmarineStabilityEvidenceForceTailPayload = {
  coefficient?: string | null;
  status?: string | null;
  detail?: string | null;
  observed_sample_count?: number | null;
  required_sample_count?: number | null;
  relative_spread?: number | null;
  max_tail_relative_spread?: number | null;
  tail_samples?: SubmarineStabilityEvidenceForceTailSamplePayload[] | null;
};

export type SubmarineStabilityEvidenceRequirementPayload = {
  requirement_id?: string | null;
  label?: string | null;
  summary_zh?: string | null;
  check_type?: string | null;
  status?: string | null;
  detail?: string | null;
  force_coefficient?: string | null;
  observed_value?: number | null;
  limit_value?: number | null;
  observed_sample_count?: number | null;
  required_sample_count?: number | null;
  relative_spread?: number | null;
  max_tail_relative_spread?: number | null;
};

export type SubmarineStabilityEvidencePayload = {
  status?: string | null;
  summary_zh?: string | null;
  source_solver_results_virtual_path?: string | null;
  artifact_virtual_path?: string | null;
  residual_summary?: Record<string, unknown> | null;
  force_coefficient_tail?: SubmarineStabilityEvidenceForceTailPayload | null;
  requirements?: SubmarineStabilityEvidenceRequirementPayload[] | null;
  blocking_issues?: string[] | null;
  missing_evidence?: string[] | null;
  passed_requirements?: string[] | null;
};

export type SubmarineCandidateCase = {
  case_id: string;
  title: string;
  score?: number;
  rationale?: string;
  geometry_family?: string;
  task_type?: string;
  source_label?: string | null;
  source_url?: string | null;
  source_type?: string | null;
  applicability_conditions?: string[] | null;
  confidence_note?: string | null;
  is_placeholder?: boolean | null;
  evidence_gap_note?: string | null;
  acceptance_profile_summary_zh?: string | null;
  benchmark_metric_ids?: string[] | null;
};

export type SubmarineLatestForcesPayload = {
  total_force?: number[] | null;
  total_moment?: number[] | null;
};

export type SubmarineForceHistoryEntry = {
  Time?: number | null;
  total_force?: number[] | null;
  total_moment?: number[] | null;
};

export type SubmarineSolverReferenceValues = {
  reference_length_m?: number | null;
  reference_area_m2?: number | null;
  inlet_velocity_mps?: number | null;
  fluid_density_kg_m3?: number | null;
};

export type SubmarineSolverMetrics = {
  solver_completed?: boolean;
  final_time_seconds?: number | null;
  workspace_postprocess_virtual_path?: string | null;
  latest_force_coefficients?: Record<string, number | null> | null;
  force_coefficients_history?: Array<Record<string, number | null>> | null;
  latest_forces?: SubmarineLatestForcesPayload | null;
  forces_history?: SubmarineForceHistoryEntry[] | null;
  reference_values?: SubmarineSolverReferenceValues | null;
};

export type SubmarineDispatchPayload = {
  summary_zh?: string;
  candidate_cases?: SubmarineCandidateCase[];
  selected_case?: SubmarineCandidateCase | null;
  selected_case_provenance_summary?:
    | SubmarineSelectedCaseProvenanceSummary
    | null;
  geometry_findings?: SubmarineGeometryFinding[] | null;
  scale_assessment?: SubmarineGeometryScaleAssessment | null;
  reference_value_suggestions?:
    | SubmarineGeometryReferenceValueSuggestion[]
    | null;
  clarification_required?: boolean | null;
  calculation_plan?: SubmarineCalculationPlanItem[] | null;
  requires_immediate_confirmation?: boolean | null;
  selected_reference_inputs?: Record<string, unknown> | null;
  solver_results?: SubmarineSolverMetrics | null;
  stability_evidence_virtual_path?: string | null;
  stability_evidence?: SubmarineStabilityEvidencePayload | null;
  scientific_verification_assessment?:
    | SubmarineScientificVerificationAssessment
    | null;
  requested_outputs?: SubmarineRequestedOutputPayload[] | null;
  output_delivery_plan?: SubmarineOutputDeliveryPlanItem[] | null;
  artifact_virtual_paths?: string[] | null;
  request_virtual_path?: string | null;
  report_virtual_path?: string | null;
  execution_log_virtual_path?: string | null;
  solver_results_virtual_path?: string | null;
  solver_results_markdown_virtual_path?: string | null;
  requires_geometry_conversion?: boolean;
};

export type SubmarineGeometryPayload = {
  summary_zh?: string;
  candidate_cases?: SubmarineCandidateCase[];
  geometry_findings?: SubmarineGeometryFinding[] | null;
  scale_assessment?: SubmarineGeometryScaleAssessment | null;
  reference_value_suggestions?:
    | SubmarineGeometryReferenceValueSuggestion[]
    | null;
  clarification_required?: boolean | null;
  calculation_plan?: SubmarineCalculationPlanItem[] | null;
  requires_immediate_confirmation?: boolean | null;
};

export type SubmarineOutputDeliveryPlanItem = {
  output_id?: string | null;
  label?: string | null;
  delivery_status?: string | null;
  detail?: string | null;
  artifact_virtual_paths?: string[] | null;
};

export type SubmarineRuntimeTimelineEventPayload = {
  stage?: string | null;
  actor?: string | null;
  role_id?: string | null;
  title?: string | null;
  summary?: string | null;
  status?: string | null;
  skill_names?: string[] | null;
  timestamp?: string | null;
};

export type SubmarineRuntimeSnapshotPayload = {
  current_stage?: string | null;
  task_summary?: string | null;
  confirmation_status?: string | null;
  execution_preference?: string | null;
  task_type?: string | null;
  geometry_virtual_path?: string | null;
  geometry_family?: string | null;
  execution_readiness?: string | null;
  geometry_findings?: SubmarineGeometryFinding[] | null;
  scale_assessment?: SubmarineGeometryScaleAssessment | null;
  reference_value_suggestions?:
    | SubmarineGeometryReferenceValueSuggestion[]
    | null;
  clarification_required?: boolean | null;
  calculation_plan?: SubmarineCalculationPlanItem[] | null;
  requires_immediate_confirmation?: boolean | null;
  selected_case_id?: string | null;
  simulation_requirements?: SubmarineSimulationRequirements | null;
  requested_outputs?: SubmarineRequestedOutputPayload[] | null;
  output_delivery_plan?: SubmarineOutputDeliveryPlanItem[] | null;
  stage_status?: string | null;
  runtime_status?: string | null;
  runtime_summary?: string | null;
  recovery_guidance?: string | null;
  blocker_detail?: string | null;
  workspace_case_dir_virtual_path?: string | null;
  run_script_virtual_path?: string | null;
  request_virtual_path?: string | null;
  execution_log_virtual_path?: string | null;
  solver_results_virtual_path?: string | null;
  stability_evidence_virtual_path?: string | null;
  stability_evidence?: SubmarineStabilityEvidencePayload | null;
  supervisor_handoff_virtual_path?: string | null;
  scientific_followup_history_virtual_path?: string | null;
  review_status?: string | null;
  scientific_verification_assessment?:
    | SubmarineScientificVerificationAssessment
    | null;
  scientific_gate_status?: string | null;
  allowed_claim_level?: string | null;
  scientific_gate_virtual_path?: string | null;
  next_recommended_stage?: string | null;
  report_virtual_path?: string | null;
  artifact_virtual_paths?: string[] | null;
  execution_plan?: SubmarineExecutionOutlineItem[] | null;
  activity_timeline?: SubmarineRuntimeTimelineEventPayload[] | null;
};

export type SubmarineResearchEvidenceSummaryPayload = {
  readiness_status?: string | null;
  verification_status?: string | null;
  validation_status?: string | null;
  provenance_status?: string | null;
  confidence?: string | null;
  blocking_issues?: string[] | null;
  evidence_gaps?: string[] | null;
  passed_evidence?: string[] | null;
  benchmark_highlights?: string[] | null;
  provenance_highlights?: string[] | null;
  artifact_virtual_paths?: string[] | null;
};

export type SubmarineScientificSupervisorGatePayload = {
  gate_status?: string | null;
  allowed_claim_level?: string | null;
  source_readiness_status?: string | null;
  recommended_stage?: string | null;
  remediation_stage?: string | null;
  blocking_reasons?: string[] | null;
  advisory_notes?: string[] | null;
  artifact_virtual_paths?: string[] | null;
};

export type SubmarineScientificRemediationActionPayload = {
  action_id?: string | null;
  title?: string | null;
  summary?: string | null;
  owner_stage?: string | null;
  priority?: string | null;
  execution_mode?: string | null;
  status?: string | null;
  evidence_gap?: string | null;
  required_artifacts?: string[] | null;
};

export type SubmarineScientificRemediationSummaryPayload = {
  plan_status?: string | null;
  current_claim_level?: string | null;
  target_claim_level?: string | null;
  recommended_stage?: string | null;
  artifact_virtual_paths?: string[] | null;
  actions?: SubmarineScientificRemediationActionPayload[] | null;
};

export type SubmarineScientificRemediationManualActionPayload = {
  action_id?: string | null;
  title?: string | null;
  owner_stage?: string | null;
  evidence_gap?: string | null;
};

export type SubmarineScientificRemediationHandoffPayload = {
  handoff_status?: string | null;
  recommended_action_id?: string | null;
  tool_name?: string | null;
  tool_args?: Record<string, unknown> | null;
  reason?: string | null;
  artifact_virtual_paths?: string[] | null;
  manual_actions?: SubmarineScientificRemediationManualActionPayload[] | null;
};

export type SubmarineScientificFollowupSummaryPayload = {
  history_virtual_path?: string | null;
  entry_count?: number | null;
  latest_outcome_status?: string | null;
  latest_handoff_status?: string | null;
  latest_recommended_action_id?: string | null;
  latest_tool_name?: string | null;
  latest_dispatch_stage_status?: string | null;
  report_refreshed?: boolean | null;
  latest_result_report_virtual_path?: string | null;
  latest_result_supervisor_handoff_virtual_path?: string | null;
  latest_notes?: string[] | null;
  artifact_virtual_paths?: string[] | null;
};

export type SubmarineExperimentSummaryPayload = {
  experiment_id?: string | null;
  experiment_status?: string | null;
  workflow_status?: string | null;
  workflow_detail?: string | null;
  baseline_run_id?: string | null;
  run_count?: number | null;
  compare_count?: number | null;
  study_manifest_virtual_path?: string | null;
  manifest_virtual_path?: string | null;
  compare_virtual_path?: string | null;
  artifact_virtual_paths?: string[] | null;
  compare_notes?: string[] | null;
  linkage_status?: string | null;
  linkage_issue_count?: number | null;
  linkage_issues?: string[] | null;
  expected_variant_run_ids?: string[] | null;
  recorded_variant_run_ids?: string[] | null;
  compared_variant_run_ids?: string[] | null;
  additional_variant_run_ids?: string[] | null;
  missing_variant_run_record_ids?: string[] | null;
  missing_compare_entry_ids?: string[] | null;
  orphan_compare_entry_ids?: string[] | null;
  run_status_counts?: Record<string, number> | null;
  compare_status_counts?: Record<string, number> | null;
  planned_variant_run_ids?: string[] | null;
  in_progress_variant_run_ids?: string[] | null;
  completed_variant_run_ids?: string[] | null;
  blocked_variant_run_ids?: string[] | null;
  planned_compare_variant_run_ids?: string[] | null;
  completed_compare_variant_run_ids?: string[] | null;
  blocked_compare_variant_run_ids?: string[] | null;
  missing_metrics_variant_run_ids?: string[] | null;
};

export type SubmarineExperimentCompareEntryPayload = {
  candidate_run_id?: string | null;
  study_type?: string | null;
  variant_id?: string | null;
  compare_status?: string | null;
  candidate_execution_status?: string | null;
  notes?: string | null;
  metric_deltas?: Record<string, unknown> | null;
  baseline_solver_results_virtual_path?: string | null;
  candidate_solver_results_virtual_path?: string | null;
  baseline_run_record_virtual_path?: string | null;
  candidate_run_record_virtual_path?: string | null;
};

export type SubmarineExperimentCompareSummaryPayload = {
  experiment_id?: string | null;
  baseline_run_id?: string | null;
  compare_count?: number | null;
  compare_virtual_path?: string | null;
  workflow_status?: string | null;
  compare_status_counts?: Record<string, number> | null;
  planned_candidate_run_ids?: string[] | null;
  completed_candidate_run_ids?: string[] | null;
  blocked_candidate_run_ids?: string[] | null;
  missing_metrics_candidate_run_ids?: string[] | null;
  artifact_virtual_paths?: string[] | null;
  comparisons?: SubmarineExperimentCompareEntryPayload[] | null;
};

export type SubmarineFigureDeliveryFigurePayload = {
  figure_id?: string | null;
  output_id?: string | null;
  title?: string | null;
  caption?: string | null;
  render_status?: string | null;
  selector_summary?: string | null;
  field?: string | null;
  artifact_virtual_paths?: string[] | null;
  source_csv_virtual_path?: string | null;
};

export type SubmarineFigureDeliverySummaryPayload = {
  figure_count?: number | null;
  manifest_virtual_path?: string | null;
  artifact_virtual_paths?: string[] | null;
  figures?: SubmarineFigureDeliveryFigurePayload[] | null;
};

export type SubmarineScientificStudyEntryPayload = {
  study_type?: string | null;
  summary_label?: string | null;
  monitored_quantity?: string | null;
  variant_count?: number | null;
  study_execution_status?: string | null;
  workflow_status?: string | null;
  workflow_detail?: string | null;
  variant_status_counts?: Record<string, number> | null;
  compare_status_counts?: Record<string, number> | null;
  expected_variant_run_ids?: string[] | null;
  planned_variant_run_ids?: string[] | null;
  in_progress_variant_run_ids?: string[] | null;
  completed_variant_run_ids?: string[] | null;
  blocked_variant_run_ids?: string[] | null;
  planned_compare_variant_run_ids?: string[] | null;
  completed_compare_variant_run_ids?: string[] | null;
  blocked_compare_variant_run_ids?: string[] | null;
  missing_metrics_variant_run_ids?: string[] | null;
  verification_status?: string | null;
  verification_detail?: string | null;
};

export type SubmarineScientificStudySummaryPayload = {
  study_execution_status?: string | null;
  workflow_status?: string | null;
  study_status_counts?: Record<string, number> | null;
  manifest_virtual_path?: string | null;
  artifact_virtual_paths?: string[] | null;
  studies?: SubmarineScientificStudyEntryPayload[] | null;
};

export type SubmarineFinalReportPayload = {
  summary_zh?: string;
  solver_metrics?: SubmarineSolverMetrics | null;
  selected_case_acceptance_profile?: Record<string, unknown> | null;
  selected_case_provenance_summary?:
    | SubmarineSelectedCaseProvenanceSummary
    | null;
  stability_evidence_virtual_path?: string | null;
  stability_evidence?: SubmarineStabilityEvidencePayload | null;
  acceptance_assessment?: SubmarineAcceptanceAssessment | null;
  research_evidence_summary?: SubmarineResearchEvidenceSummaryPayload | null;
  scientific_supervisor_gate?: SubmarineScientificSupervisorGatePayload | null;
  scientific_gate_status?: string | null;
  allowed_claim_level?: string | null;
  scientific_remediation_summary?:
    | SubmarineScientificRemediationSummaryPayload
    | null;
  scientific_remediation_handoff?:
    | SubmarineScientificRemediationHandoffPayload
    | null;
  scientific_followup_summary?: SubmarineScientificFollowupSummaryPayload | null;
  experiment_summary?: SubmarineExperimentSummaryPayload | null;
  experiment_compare_summary?: SubmarineExperimentCompareSummaryPayload | null;
  figure_delivery_summary?: SubmarineFigureDeliverySummaryPayload | null;
  scientific_study_summary?: SubmarineScientificStudySummaryPayload | null;
  scientific_verification_assessment?:
    | SubmarineScientificVerificationAssessment
    | null;
  output_delivery_plan?: SubmarineOutputDeliveryPlanItem[] | null;
  requested_outputs?: SubmarineRequestedOutputPayload[] | null;
};
