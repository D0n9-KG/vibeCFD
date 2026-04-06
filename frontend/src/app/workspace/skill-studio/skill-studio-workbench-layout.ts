import {
  getAgenticWorkbenchLayout,
  type AgenticWorkbenchLayout,
} from "../../../components/workspace/agentic-workbench/agentic-workbench-layout.ts";

type SkillStudioWorkbenchLayoutOptions = {
  chatOpen: boolean;
};

type SkillStudioWorkbenchLayout = AgenticWorkbenchLayout;

export function getSkillStudioWorkbenchLayout({
  chatOpen,
}: SkillStudioWorkbenchLayoutOptions): SkillStudioWorkbenchLayout {
  return getAgenticWorkbenchLayout({
    chatOpen,
    desktopNegotiationRailWidthClassName: "minmax(340px,460px)",
    desktopWorkbenchPaddingClassName: "xl:pr-2",
  });
}

export type {
  SkillStudioWorkbenchLayout,
  SkillStudioWorkbenchLayoutOptions,
};
