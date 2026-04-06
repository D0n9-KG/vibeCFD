"use client";

import { type ReactNode } from "react";

import { cn } from "@/lib/utils";

import {
  getWorkbenchShellZoneClassNames,
  type WorkbenchShellZone,
  WORKBENCH_SHELL_ZONE_ORDER,
} from "./workbench-shell.contract";

export { getWorkbenchShellZoneClassNames, WORKBENCH_SHELL_ZONE_ORDER };
export type { WorkbenchShellZone };

export type WorkbenchShellProps = {
  className?: string;
  mobileNegotiationRailVisible?: boolean;
  main: ReactNode;
  negotiation: ReactNode;
};

export function WorkbenchShell({
  className,
  mobileNegotiationRailVisible = true,
  main,
  negotiation,
}: WorkbenchShellProps) {
  const classes = getWorkbenchShellZoneClassNames({
    mobileNegotiationRailVisible,
  });

  return (
    <section className={cn(classes.root, className)}>
      <main data-workbench-zone="main" className={classes.main}>
        {main}
      </main>

      <aside data-workbench-zone="negotiation" className={classes.negotiation}>
        {negotiation}
      </aside>
    </section>
  );
}
