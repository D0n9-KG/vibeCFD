import {
  getAgenticWorkbenchLayout,
  type AgenticWorkbenchLayout,
} from "../../../components/workspace/agentic-workbench/agentic-workbench-layout.ts";

type SubmarineWorkbenchLayoutOptions = {
  mobileNegotiationRailVisible: boolean;
};

type SubmarineWorkbenchLayout = AgenticWorkbenchLayout;

export function getSubmarineWorkbenchLayout({
  mobileNegotiationRailVisible,
}: SubmarineWorkbenchLayoutOptions): SubmarineWorkbenchLayout {
  return getAgenticWorkbenchLayout({
    surface: "submarine",
    mobileNegotiationRailVisible,
  });
}

export type { SubmarineWorkbenchLayout, SubmarineWorkbenchLayoutOptions };
