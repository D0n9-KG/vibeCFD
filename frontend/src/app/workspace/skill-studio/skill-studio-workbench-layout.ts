import {
  getAgenticWorkbenchLayout,
  type AgenticWorkbenchLayout,
} from "../../../components/workspace/agentic-workbench/agentic-workbench-layout.ts";

type SkillStudioWorkbenchLayoutOptions = {
  mobileNegotiationRailVisible: boolean;
};

type SkillStudioWorkbenchLayout = AgenticWorkbenchLayout;

export function getSkillStudioWorkbenchLayout({
  mobileNegotiationRailVisible,
}: SkillStudioWorkbenchLayoutOptions): SkillStudioWorkbenchLayout {
  return getAgenticWorkbenchLayout({
    surface: "skill-studio",
    mobileNegotiationRailVisible,
  });
}

export type {
  SkillStudioWorkbenchLayout,
  SkillStudioWorkbenchLayoutOptions,
};
