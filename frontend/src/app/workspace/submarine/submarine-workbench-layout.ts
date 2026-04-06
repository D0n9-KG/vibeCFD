import {
  getAgenticWorkbenchLayout,
  type AgenticWorkbenchLayout,
} from "../../../components/workspace/agentic-workbench/agentic-workbench-layout.ts";

type SubmarineWorkbenchLayoutOptions = {
  chatOpen: boolean;
};

type SubmarineWorkbenchLayout = AgenticWorkbenchLayout;

export function getSubmarineWorkbenchLayout({
  chatOpen,
}: SubmarineWorkbenchLayoutOptions): SubmarineWorkbenchLayout {
  return getAgenticWorkbenchLayout({
    chatOpen,
    desktopNegotiationRailWidthClassName: "minmax(320px,420px)",
    desktopWorkbenchPaddingClassName: "xl:pr-1",
  });
}

export type { SubmarineWorkbenchLayout, SubmarineWorkbenchLayoutOptions };
