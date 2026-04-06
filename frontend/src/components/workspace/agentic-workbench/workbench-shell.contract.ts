export const WORKBENCH_SHELL_ZONE_ORDER = [
  "main",
  "negotiation",
] as const;

export type WorkbenchShellZone = (typeof WORKBENCH_SHELL_ZONE_ORDER)[number];

export type WorkbenchShellZoneClassNames = {
  root: string;
  main: string;
  negotiation: string;
};

export type GetWorkbenchShellZoneClassNamesOptions = {
  mobileNegotiationRailVisible?: boolean;
};

export function getWorkbenchShellZoneClassNames({
  mobileNegotiationRailVisible = true,
}: GetWorkbenchShellZoneClassNamesOptions = {}): WorkbenchShellZoneClassNames {
  return {
    root: [
      "agentic-workbench-shell",
      "grid",
      "min-h-0",
      "w-full",
      "grid-cols-1",
      "gap-4",
      "xl:grid-cols-[minmax(0,1fr)_minmax(360px,420px)]",
    ].join(" "),
    main: [
      "agentic-workbench-zone-main",
      "min-h-0",
      "rounded-[30px]",
      "border",
      "border-slate-200/80",
      "bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(246,249,252,0.96))]",
      "p-4",
      "md:p-5",
      "xl:overflow-hidden",
    ].join(" "),
    negotiation: [
      "agentic-workbench-zone-negotiation",
      mobileNegotiationRailVisible ? "block" : "hidden",
      "min-h-[420px]",
      "rounded-[30px]",
      "border",
      "border-slate-200/80",
      "bg-white/94",
      "p-3",
      "xl:block",
      "xl:min-h-0",
      "xl:overflow-hidden",
    ].join(" "),
  };
}
