import { getSubmarineArtifactMeta } from "../submarine-runtime-panel.utils.ts";

function getFileName(filepath: string) {
  return filepath.split("/").at(-1) ?? filepath;
}

export type ArtifactListSectionId =
  | "delivery"
  | "execution"
  | "preparation"
  | "skill-draft"
  | "skill-validation"
  | "skill-publish"
  | "other";

export type ArtifactListSection = {
  id: ArtifactListSectionId;
  title: string;
  description: string;
  files: string[];
};

type ArtifactSectionDefinition = {
  id: ArtifactListSectionId;
  title: string;
  description: string;
  priority: number;
};

const SECTION_DEFINITIONS: Record<ArtifactListSectionId, ArtifactSectionDefinition> = {
  delivery: {
    id: "delivery",
    title: "关键交付",
    description: "优先查看最终报告、交付判断和关键结论文件。",
    priority: 0,
  },
  execution: {
    id: "execution",
    title: "求解与验证",
    description: "包含求解摘要、验证结果、实验对比和运行日志。",
    priority: 1,
  },
  preparation: {
    id: "preparation",
    title: "任务准备",
    description: "包含几何预检、设计简报和任务准备材料。",
    priority: 2,
  },
  "skill-draft": {
    id: "skill-draft",
    title: "技能草稿",
    description: "先看技能定义、说明和参考内容。",
    priority: 0,
  },
  "skill-validation": {
    id: "skill-validation",
    title: "验证与试跑",
    description: "包含校验结果、测试矩阵和试跑证据。",
    priority: 1,
  },
  "skill-publish": {
    id: "skill-publish",
    title: "发布与生命周期",
    description: "包含生命周期设置、发布准备和安装包。",
    priority: 2,
  },
  other: {
    id: "other",
    title: "其他文件",
    description: "其余相关文件与辅助产物。",
    priority: 9,
  },
};

function classifyArtifactSection(path: string): ArtifactSectionDefinition {
  const fileName = getFileName(path);

  if (path.includes("/submarine/skill-studio/")) {
    if (
      fileName === "skill-draft.json" ||
      fileName === "SKILL.md" ||
      path.includes("/references/")
    ) {
      return SECTION_DEFINITIONS["skill-draft"];
    }

    if (
      fileName.startsWith("validation-report.") ||
      fileName.startsWith("test-matrix.") ||
      fileName === "dry-run-evidence.json"
    ) {
      return SECTION_DEFINITIONS["skill-validation"];
    }

    if (
      fileName.startsWith("publish-readiness.") ||
      fileName === "skill-lifecycle.json" ||
      fileName === "skill-package.json" ||
      fileName.endsWith(".skill")
    ) {
      return SECTION_DEFINITIONS["skill-publish"];
    }

    return SECTION_DEFINITIONS.other;
  }

  if (path.includes("/submarine/reports/")) {
    return SECTION_DEFINITIONS.delivery;
  }

  if (
    path.includes("/submarine/design-brief/") ||
    path.includes("/submarine/geometry-check/")
  ) {
    return SECTION_DEFINITIONS.preparation;
  }

  if (
    path.includes("/submarine/solver-dispatch/") ||
    fileName === "openfoam-run.log" ||
    fileName === "openfoam-request.json"
  ) {
    return SECTION_DEFINITIONS.execution;
  }

  return SECTION_DEFINITIONS.other;
}

function artifactFilePriority(path: string, sectionId: ArtifactListSectionId): number {
  const fileName = getFileName(path);

  if (sectionId === "delivery") {
    const rank = [
      "final-report.md",
      "final-report.html",
      "final-report.json",
      "delivery-readiness.md",
      "delivery-readiness.json",
      "research-evidence-summary.json",
      "supervisor-scientific-gate.json",
      "scientific-remediation-plan.json",
      "scientific-remediation-handoff.json",
      "scientific-followup-history.json",
    ].indexOf(fileName);

    return rank >= 0 ? rank : 99;
  }

  if (sectionId === "execution") {
    const rank = [
      "solver-results.md",
      "solver-results.json",
      "dispatch-summary.md",
      "dispatch-summary.html",
      "verification-mesh-independence.json",
      "verification-domain-sensitivity.json",
      "verification-time-step-sensitivity.json",
      "run-compare-summary.json",
      "experiment-manifest.json",
      "study-manifest.json",
      "study-plan.json",
      "provenance-manifest.json",
      "openfoam-request.json",
      "openfoam-run.log",
    ].indexOf(fileName);

    return rank >= 0 ? rank : 99;
  }

  if (sectionId === "preparation") {
    const rank = ["cfd-design-brief.md", "cfd-design-brief.html", "cfd-design-brief.json"].indexOf(
      fileName,
    );

    if (rank >= 0) {
      return rank;
    }

    if (fileName.startsWith("geometry-check.")) {
      return 10;
    }

    return 99;
  }

  if (sectionId === "skill-draft") {
    const rank = ["skill-draft.json", "SKILL.md"].indexOf(fileName);
    return rank >= 0 ? rank : 99;
  }

  if (sectionId === "skill-validation") {
    const rank = [
      "validation-report.md",
      "validation-report.html",
      "validation-report.json",
      "test-matrix.md",
      "test-matrix.json",
      "dry-run-evidence.json",
    ].indexOf(fileName);

    return rank >= 0 ? rank : 99;
  }

  if (sectionId === "skill-publish") {
    const rank = [
      "publish-readiness.md",
      "publish-readiness.html",
      "publish-readiness.json",
      "skill-lifecycle.json",
      "skill-package.json",
    ].indexOf(fileName);

    if (rank >= 0) {
      return rank;
    }

    if (fileName.endsWith(".skill")) {
      return 20;
    }
  }

  return 99;
}

export function getArtifactDisplayName(filepath: string) {
  if (filepath.includes("/submarine/")) {
    return getSubmarineArtifactMeta(filepath).label;
  }

  return getFileName(filepath);
}

export function buildArtifactListSections(files: string[]): ArtifactListSection[] {
  const groups = new Map<ArtifactListSectionId, string[]>();

  for (const file of files) {
    const section = classifyArtifactSection(file);
    const existing = groups.get(section.id) ?? [];
    existing.push(file);
    groups.set(section.id, existing);
  }

  return [...groups.entries()]
    .map(([sectionId, sectionFiles]) => {
      const definition = SECTION_DEFINITIONS[sectionId];
      return {
        id: definition.id,
        title: definition.title,
        description: definition.description,
        files: [...sectionFiles].sort((left, right) => {
          const priorityDelta =
            artifactFilePriority(left, sectionId) - artifactFilePriority(right, sectionId);
          if (priorityDelta !== 0) {
            return priorityDelta;
          }

          return getArtifactDisplayName(left).localeCompare(getArtifactDisplayName(right));
        }),
      };
    })
    .sort(
      (left, right) =>
        SECTION_DEFINITIONS[left.id].priority - SECTION_DEFINITIONS[right.id].priority,
    );
}
