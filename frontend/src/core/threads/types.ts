import type { Message, Thread } from "@langchain/langgraph-sdk";

import type { Todo } from "../todos";

export interface AgentThreadState extends Record<string, unknown> {
  title: string;
  messages: Message[];
  artifacts: string[];
  todos?: Todo[];
  workspace_kind?: "submarine" | "skill-studio";
  submarine_runtime?: Record<string, unknown>;
  submarine_skill_studio?: {
    skill_name?: string;
    assistant_mode?: string;
    assistant_label?: string;
    builtin_skills?: string[];
    validation_status?: string;
    test_status?: string;
    publish_status?: string;
    error_count?: number;
    warning_count?: number;
    report_virtual_path?: string;
    package_virtual_path?: string;
    package_archive_virtual_path?: string;
    test_virtual_path?: string;
    publish_virtual_path?: string;
    ui_metadata_virtual_path?: string;
    artifact_virtual_paths?: string[];
  };
}

export interface AgentThread extends Thread<AgentThreadState> {}

export interface AgentThreadContext extends Record<string, unknown> {
  thread_id: string;
  model_name: string | undefined;
  thinking_enabled: boolean;
  is_plan_mode: boolean;
  subagent_enabled: boolean;
  reasoning_effort?: "minimal" | "low" | "medium" | "high";
  agent_name?: string;
}
