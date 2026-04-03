"use client";

import {
  CircleOffIcon,
  RefreshCcwIcon,
  ShieldXIcon,
  SparklesIcon,
} from "lucide-react";
import Link from "next/link";
import type { ComponentType } from "react";

import { Button } from "@/components/ui/button";
import { useI18n } from "@/core/i18n/hooks";
import { cn } from "@/lib/utils";

import {
  getWorkspaceStateCopy,
  type WorkspaceStatePanelId,
} from "./workspace-state-panel.state";

export type WorkspaceStatePanelAction = {
  label: string;
  href?: string;
  onClick?: () => void;
  ariaLabel?: string;
  variant?: "default" | "outline" | "ghost";
};

type WorkspaceStatePanelProps = {
  state: WorkspaceStatePanelId;
  label?: string;
  title?: string;
  description?: string;
  actions?: WorkspaceStatePanelAction[];
  className?: string;
};

const WORKSPACE_STATE_ICONS = {
  "first-run": SparklesIcon,
  "permissions-error": ShieldXIcon,
  "data-interrupted": CircleOffIcon,
  "update-failed": RefreshCcwIcon,
} satisfies Record<
  WorkspaceStatePanelId,
  ComponentType<{ className?: string }>
>;

const WORKSPACE_STATE_TONES = {
  "first-run":
    "border-amber-200/80 bg-[linear-gradient(135deg,rgba(255,251,235,0.96),rgba(255,255,255,0.98))] text-amber-950",
  "permissions-error":
    "border-rose-200/80 bg-[linear-gradient(135deg,rgba(255,241,242,0.96),rgba(255,255,255,0.98))] text-rose-950",
  "data-interrupted":
    "border-sky-200/80 bg-[linear-gradient(135deg,rgba(239,246,255,0.96),rgba(255,255,255,0.98))] text-sky-950",
  "update-failed":
    "border-stone-200/80 bg-[linear-gradient(135deg,rgba(250,245,235,0.96),rgba(255,255,255,0.98))] text-stone-950",
} satisfies Record<WorkspaceStatePanelId, string>;

export function WorkspaceStatePanel({
  state,
  label,
  title,
  description,
  actions,
  className,
}: WorkspaceStatePanelProps) {
  const { t } = useI18n();
  const copy = getWorkspaceStateCopy(t.workspaceStates, state);
  const Icon = WORKSPACE_STATE_ICONS[state];
  const resolvedLabel = label ?? copy.label;
  const resolvedTitle = title ?? copy.title;
  const resolvedDescription = description ?? copy.message;

  return (
    <section
      className={cn(
        "rounded-[28px] border p-5 shadow-[0_18px_44px_rgba(15,23,42,0.06)]",
        WORKSPACE_STATE_TONES[state],
        className,
      )}
      aria-live="polite"
    >
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div className="flex min-w-0 gap-4">
          <div className="flex size-12 shrink-0 items-center justify-center rounded-2xl border border-current/12 bg-white/72">
            <Icon className="size-5" />
          </div>
          <div className="min-w-0">
            <div className="text-[11px] font-semibold uppercase tracking-[0.24em] text-current/70">
              {resolvedLabel}
            </div>
            <h3 className="mt-2 text-lg font-semibold tracking-tight">
              {resolvedTitle}
            </h3>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-current/75">
              {resolvedDescription}
            </p>
          </div>
        </div>

        {actions?.length ? (
          <div className="flex flex-wrap gap-2">
            {actions.map((action) => {
              if (action.href) {
                return (
                  <Button
                    key={`${action.label}-${action.href}`}
                    asChild
                    variant={action.variant ?? "outline"}
                  >
                    <Link
                      href={action.href}
                      aria-label={action.ariaLabel ?? action.label}
                    >
                      {action.label}
                    </Link>
                  </Button>
                );
              }

              return (
                <Button
                  key={action.label}
                  type="button"
                  variant={action.variant ?? "outline"}
                  onClick={action.onClick}
                  aria-label={action.ariaLabel ?? action.label}
                >
                  {action.label}
                </Button>
              );
            })}
          </div>
        ) : null}
      </div>
    </section>
  );
}
