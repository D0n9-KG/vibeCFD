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
}

export interface PublishSkillResponse {
  success: boolean;
  skill_name: string;
  message: string;
  published_path: string;
  enabled: boolean;
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
