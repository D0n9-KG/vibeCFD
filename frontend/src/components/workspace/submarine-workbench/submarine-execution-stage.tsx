"use client";

import { useMemo } from "react";

import type {
  SubmarineRuntimeSnapshotPayload,
  SubmarineRuntimeTimelineEventPayload,
} from "../submarine-runtime-panel.contract";
import {
  buildSubmarineStageTrack,
  groupSubmarineArtifacts,
} from "../submarine-runtime-panel.utils";

import type { SubmarineDetailModel } from "./submarine-detail-model";
import { SubmarineExperimentBoard } from "./submarine-experiment-board";
import { SubmarineOperatorBoard } from "./submarine-operator-board";
import type { SubmarineSessionModel } from "./submarine-session-model";

export function SubmarineExecutionStage({
  session,
  detail,
  runtime,
  artifactPaths,
}: {
  session: SubmarineSessionModel;
  detail: SubmarineDetailModel;
  runtime: SubmarineRuntimeSnapshotPayload | null;
  artifactPaths: string[];
}) {
  const stageTrack = useMemo(
    () =>
      buildSubmarineStageTrack({
        runtimePlan: runtime?.execution_plan ?? null,
        currentStage: runtime?.current_stage,
        nextRecommendedStage: runtime?.next_recommended_stage,
      }),
    [runtime?.current_stage, runtime?.execution_plan, runtime?.next_recommended_stage],
  );
  const groupedArtifacts = useMemo(
    () => groupSubmarineArtifacts(artifactPaths),
    [artifactPaths],
  );
  const timeline = useMemo(
    () => runtime?.activity_timeline ?? [],
    [runtime?.activity_timeline],
  );
  const executionAssets = [
    { label: "Case Directory", value: runtime?.workspace_case_dir_virtual_path ?? null },
    { label: "Run Script", value: runtime?.run_script_virtual_path ?? null },
    { label: "Dispatch Request", value: runtime?.request_virtual_path ?? null },
    { label: "Execution Log", value: runtime?.execution_log_virtual_path ?? null },
    { label: "Solver Results", value: runtime?.solver_results_virtual_path ?? null },
    { label: "Supervisor Report", value: runtime?.report_virtual_path ?? null },
  ].filter((item): item is { label: string; value: string } => Boolean(item.value));

  return (
    <section className="space-y-4 pb-4">
      <article className="rounded-2xl border border-slate-200/80 bg-white/92 p-5 shadow-[0_14px_30px_rgba(15,23,42,0.04)]">
        <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-sky-700">
          Execute Stage
        </div>
        <h2 className="mt-2 text-xl font-semibold tracking-tight text-slate-950">
          Live orchestration, actual runs, and handoff evidence
        </h2>
        <p className="mt-3 text-sm leading-7 text-slate-700">
          {session.summary.currentObjective}
        </p>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <Metric label="Current Stage" value={runtime?.current_stage ?? "pending"} />
          <Metric label="Runtime Status" value={runtime?.runtime_status ?? "pending"} />
          <Metric label="Review Status" value={runtime?.review_status ?? "pending"} />
          <Metric label="Timeline Events" value={String(timeline.length)} />
        </div>
        {(runtime?.runtime_summary || runtime?.blocker_detail || runtime?.recovery_guidance) ? (
          <div className="mt-4 rounded-xl border border-slate-200/80 bg-slate-50/85 px-4 py-3 text-sm text-slate-700">
            <div className="font-semibold text-slate-950">Execution Notes</div>
            {runtime?.runtime_summary ? <p className="mt-2">{runtime.runtime_summary}</p> : null}
            {runtime?.blocker_detail ? (
              <p className="mt-2 text-amber-700">{runtime.blocker_detail}</p>
            ) : null}
            {runtime?.recovery_guidance ? (
              <p className="mt-2 text-slate-600">{runtime.recovery_guidance}</p>
            ) : null}
          </div>
        ) : null}
      </article>

      <section className="rounded-2xl border border-slate-200/80 bg-white/92 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.04)]">
        <div className="flex items-center justify-between gap-3">
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-sky-700">
              Process Ledger
            </div>
            <p className="mt-1 text-sm text-slate-700">
              Keep the actual stage handoffs, actors, and skill usage visible while the run advances.
            </p>
          </div>
          <div className="text-sm font-semibold text-slate-950">{stageTrack.length} steps</div>
        </div>
        {stageTrack.length ? (
          <div className="mt-4 flex flex-wrap gap-2">
            {stageTrack.map((item) => (
              <div
                key={`${item.stageId}-${item.status}`}
                className="rounded-full border border-slate-200/80 bg-slate-50/85 px-3 py-2 text-xs text-slate-700"
              >
                <span className="font-semibold text-slate-900">{item.label}</span>
                <span className="ml-2 uppercase tracking-[0.14em] text-slate-500">
                  {item.status}
                </span>
              </div>
            ))}
          </div>
        ) : null}
        {timeline.length ? (
          <div className="mt-4 space-y-3">
            {timeline.slice(0, 10).map((event, index) => (
              <TimelineEntry
                key={`${event.timestamp ?? "no-time"}-${event.title ?? "event"}-${index}`}
                event={event}
              />
            ))}
          </div>
        ) : (
          <EmptyState
            className="mt-4"
            text="The lead agent has not recorded any execution timeline events yet."
          />
        )}
      </section>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(320px,0.92fr)]">
        <section className="rounded-2xl border border-slate-200/80 bg-white/92 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.04)]">
          <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-sky-700">
            Execution Assets
          </div>
          <div className="mt-4 space-y-3">
            {executionAssets.length ? (
              executionAssets.map((asset) => (
                <article
                  key={asset.label}
                  className="rounded-xl border border-slate-200/80 bg-slate-50/85 px-4 py-3"
                >
                  <div className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">
                    {asset.label}
                  </div>
                  <div className="mt-1 break-all text-sm text-slate-800">{asset.value}</div>
                </article>
              ))
            ) : (
              <EmptyState text="Execution artifacts will appear here once dispatch begins." />
            )}
          </div>
        </section>

        <section className="rounded-2xl border border-slate-200/80 bg-white/92 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.04)]">
          <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-sky-700">
            Artifact Groups
          </div>
          {groupedArtifacts.length ? (
            <div className="mt-4 space-y-3">
              {groupedArtifacts.map((group) => (
                <article
                  key={group.id}
                  className="rounded-xl border border-slate-200/80 bg-slate-50/85 px-4 py-3"
                >
                  <div className="flex items-center justify-between gap-3">
                    <div className="text-sm font-semibold text-slate-950">{group.label}</div>
                    <div className="text-xs uppercase tracking-[0.16em] text-slate-500">
                      {group.count} files
                    </div>
                  </div>
                  <ul className="mt-2 space-y-2 text-xs text-slate-600">
                    {group.paths.slice(0, 3).map((path) => (
                      <li key={path} className="break-all">
                        {path}
                      </li>
                    ))}
                  </ul>
                </article>
              ))}
            </div>
          ) : (
            <EmptyState text="No submarine-scoped artifacts have been recorded yet." />
          )}
        </section>
      </div>

      <SubmarineExperimentBoard experimentBoard={detail.experimentBoard} />
      <SubmarineOperatorBoard operatorBoard={detail.operatorBoard} />
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-slate-200/80 bg-slate-50/85 px-3 py-2">
      <div className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">
        {label}
      </div>
      <div className="mt-1 text-sm font-semibold text-slate-900">{value}</div>
    </div>
  );
}

function TimelineEntry({
  event,
}: {
  event: SubmarineRuntimeTimelineEventPayload;
}) {
  return (
    <article className="rounded-xl border border-slate-200/80 bg-slate-50/85 px-4 py-3">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="text-sm font-semibold text-slate-950">
            {event.title ?? "Pipeline event"}
          </div>
          <div className="mt-1 text-xs uppercase tracking-[0.16em] text-slate-500">
            {(event.stage ?? "unknown-stage").replaceAll("-", " ")}
          </div>
        </div>
        <div className="text-xs text-slate-500">
          {(event.status ?? "pending").replaceAll("_", " ")}
        </div>
      </div>
      {event.summary ? <p className="mt-2 text-sm text-slate-700">{event.summary}</p> : null}
      <div className="mt-2 flex flex-wrap gap-x-4 gap-y-2 text-xs text-slate-600">
        <span>Actor: {event.actor ?? "lead-agent"}</span>
        {event.role_id ? <span>Role: {event.role_id}</span> : null}
        {event.timestamp ? <span>Time: {event.timestamp}</span> : null}
      </div>
      {event.skill_names?.length ? (
        <p className="mt-2 text-xs text-slate-600">
          Skills: {event.skill_names.join(", ")}
        </p>
      ) : null}
    </article>
  );
}

function EmptyState({
  text,
  className,
}: {
  text: string;
  className?: string;
}) {
  return (
    <div
      className={`rounded-xl border border-dashed border-slate-200 bg-slate-50/70 px-4 py-6 text-sm text-slate-600 ${className ?? ""}`}
    >
      {text}
    </div>
  );
}
