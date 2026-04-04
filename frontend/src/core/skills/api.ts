import { getBackendBaseURL } from "@/core/config";
import { env } from "@/env";

import type { Skill } from "./type";

export async function loadSkills() {
  const skills = await fetch(`${getBackendBaseURL()}/api/skills`);
  const json = await skills.json();
  return json.skills as Skill[];
}

export async function enableSkill(skillName: string, enabled: boolean) {
  const response = await fetch(
    `${getBackendBaseURL()}/api/skills/${skillName}`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        enabled,
      }),
    },
  );
  return response.json();
}

export interface InstallSkillRequest {
  thread_id: string;
  path: string;
}

export interface InstallSkillResponse {
  success: boolean;
  skill_name: string;
  message: string;
}

export interface PublishSkillRequest {
  thread_id: string;
  path: string;
  overwrite?: boolean;
  enable?: boolean;
  version_note?: string;
  binding_targets?: SkillLifecycleBindingTarget[];
}

export interface PublishSkillResponse {
  success: boolean;
  skill_name: string;
  message: string;
  published_path: string;
  enabled: boolean;
}

export interface SkillLifecycleBindingTarget {
  role_id: string;
  mode: string;
  target_skills: string[];
}

export interface SkillLifecycleRevision {
  revision_id: string;
  published_at: string;
  archive_path: string;
  published_path: string;
  version_note: string;
  binding_targets: SkillLifecycleBindingTarget[];
  enabled: boolean;
  source_thread_id?: string | null;
}

export interface SkillLifecycleSummary {
  skill_name: string;
  enabled: boolean;
  binding_targets: SkillLifecycleBindingTarget[];
  active_revision_id?: string | null;
  published_revision_id?: string | null;
  draft_status: string;
  published_path?: string | null;
  last_published_at?: string | null;
  version_note?: string;
}

export interface SkillLifecycleRecord extends SkillLifecycleSummary {
  skill_asset_id: string;
  source_thread_id?: string | null;
  draft_updated_at?: string | null;
  package_archive_virtual_path?: string | null;
  artifact_virtual_paths: string[];
  bindings: SkillLifecycleBindingTarget[];
  published_revisions: SkillLifecycleRevision[];
  last_published_from_thread_id?: string | null;
  rollback_target_id?: string | null;
}

export interface UpdateSkillLifecycleRequest {
  enabled: boolean;
  version_note?: string;
  binding_targets: SkillLifecycleBindingTarget[];
}

export interface SkillGraphNode {
  name: string;
  description: string;
  category: string;
  enabled: boolean;
  related_count: number;
  stage?: string | null;
}

export interface SkillGraphRelationship {
  source: string;
  target: string;
  relationship_type: string;
  score: number;
  reason: string;
}

export interface SkillGraphFocusItem {
  skill_name: string;
  category: string;
  enabled: boolean;
  description: string;
  relationship_types: string[];
  strongest_score: number;
  reasons: string[];
}

export interface SkillGraphFocus {
  skill_name: string;
  related_skill_count: number;
  related_skills: SkillGraphFocusItem[];
}

export interface SkillGraphResponse {
  summary: {
    skill_count: number;
    enabled_skill_count: number;
    public_skill_count: number;
    custom_skill_count: number;
    edge_count: number;
    relationship_counts: Record<string, number>;
  };
  skills: SkillGraphNode[];
  relationships: SkillGraphRelationship[];
  focus?: SkillGraphFocus | null;
}

export async function installSkill(
  request: InstallSkillRequest,
): Promise<InstallSkillResponse> {
  const response = await fetch(`${getBackendBaseURL()}/api/skills/install`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    // Handle HTTP error responses (4xx, 5xx)
    const errorData = await response.json().catch(() => ({}));
    const errorMessage =
      errorData.detail ?? `HTTP ${response.status}: ${response.statusText}`;
    return {
      success: false,
      skill_name: "",
      message: errorMessage,
    };
  }

  return response.json();
}

export async function publishSkill(
  request: PublishSkillRequest,
): Promise<PublishSkillResponse> {
  const response = await fetch(`${getBackendBaseURL()}/api/skills/publish`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      overwrite: false,
      enable: true,
      ...request,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    const errorMessage =
      errorData.detail ?? `HTTP ${response.status}: ${response.statusText}`;
    throw new Error(errorMessage);
  }

  return response.json();
}

export async function loadSkillLifecycleSummaries(): Promise<
  SkillLifecycleSummary[]
> {
  const response = await fetch(`${getBackendBaseURL()}/api/skills/lifecycle`);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    const errorMessage =
      errorData.detail ?? `HTTP ${response.status}: ${response.statusText}`;
    throw new Error(errorMessage);
  }

  const json = (await response.json()) as { skills: SkillLifecycleSummary[] };
  return json.skills;
}

export async function loadSkillLifecycle(
  skillName: string,
): Promise<SkillLifecycleRecord> {
  const response = await fetch(
    `${getBackendBaseURL()}/api/skills/lifecycle/${skillName}`,
  );

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    const errorMessage =
      errorData.detail ?? `HTTP ${response.status}: ${response.statusText}`;
    throw new Error(errorMessage);
  }

  return response.json();
}

export async function updateSkillLifecycle(
  skillName: string,
  request: UpdateSkillLifecycleRequest,
): Promise<SkillLifecycleRecord> {
  const response = await fetch(
    `${getBackendBaseURL()}/api/skills/lifecycle/${skillName}`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        version_note: "",
        ...request,
      }),
    },
  );

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    const errorMessage =
      errorData.detail ?? `HTTP ${response.status}: ${response.statusText}`;
    throw new Error(errorMessage);
  }

  return response.json();
}

export async function loadSkillGraph({
  skillName,
  isMock = false,
}: {
  skillName?: string;
  isMock?: boolean;
} = {}): Promise<SkillGraphResponse> {
  if (env.NEXT_PUBLIC_STATIC_WEBSITE_ONLY === "true" || isMock) {
    const response = await fetch("/demo/skill-studio/skill-graph.json");
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    const json = (await response.json()) as SkillGraphResponse;
    if (!skillName) {
      return json;
    }
    if (json.focus?.skill_name === skillName) {
      return json;
    }
    return {
      ...json,
      focus:
        skillName === "submarine-result-acceptance"
          ? json.focus ?? null
          : null,
    };
  }

  const url = new URL(`${getBackendBaseURL()}/api/skills/graph`);
  if (skillName) {
    url.searchParams.set("skill_name", skillName);
  }
  const response = await fetch(url.toString());

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    const errorMessage =
      errorData.detail ?? `HTTP ${response.status}: ${response.statusText}`;
    throw new Error(errorMessage);
  }

  return response.json();
}
