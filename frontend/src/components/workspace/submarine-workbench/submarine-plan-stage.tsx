"use client";

import { MessageSquareIcon } from "lucide-react";
import { useMemo } from "react";

import { Button } from "@/components/ui/button";

import type {
  SubmarineDesignBriefPayload,
  SubmarineRuntimeSnapshotPayload,
} from "../submarine-runtime-panel.contract";
import {
  buildSubmarineDesignBriefSummary,
  buildSubmarineExecutionOutline,
} from "../submarine-runtime-panel.utils";

import type { SubmarineSessionModel } from "./submarine-session-model";

export function SubmarinePlanStage({
  session,
  runtime,
  designBrief,
  onOpenChat,
}: {
  session: SubmarineSessionModel;
  runtime: SubmarineRuntimeSnapshotPayload | null;
  designBrief: SubmarineDesignBriefPayload | null;
  onOpenChat: () => void;
}) {
  const designBriefSummary = useMemo(
    () => buildSubmarineDesignBriefSummary(designBrief),
    [designBrief],
  );
  const executionOutline = useMemo(
    () =>
      buildSubmarineExecutionOutline({
        designBrief,
        runtimePlan: runtime?.execution_plan ?? null,
      }),
    [designBrief, runtime?.execution_plan],
  );

  return (
    <section className="space-y-4 pb-4">
      <article className="rounded-2xl border border-slate-200/80 bg-white/92 p-5 shadow-[0_14px_30px_rgba(15,23,42,0.04)]">
        <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-sky-700">
          Plan Stage
        </div>
        <h2 className="mt-2 text-xl font-semibold tracking-tight text-slate-950">
          Define objective, constraints, and approval boundaries
        </h2>
        <p className="mt-3 text-sm leading-7 text-slate-700">
          {session.summary.currentObjective}
        </p>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <PlanMetric
            label="Pending Approvals"
            value={String(session.negotiation.pendingApprovalCount)}
          />
          <PlanMetric label="Messages" value={String(session.summary.messageCount)} />
          <PlanMetric label="Artifacts" value={String(session.summary.artifactCount)} />
          <PlanMetric
            label="Execution Readiness"
            value={runtime?.execution_readiness ?? "pending"}
          />
        </div>
        <Button className="mt-4" onClick={onOpenChat}>
          <MessageSquareIcon className="size-4" />
          Continue Negotiation
        </Button>
      </article>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.1fr)_minmax(320px,0.9fr)]">
        <section className="rounded-2xl border border-slate-200/80 bg-white/92 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.04)]">
          <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-sky-700">
            Work Agreement
          </div>
          <div className="mt-3 grid gap-3 sm:grid-cols-2">
            <DetailRow
              label="Confirmation"
              value={designBriefSummary?.confirmationStatusLabel ?? "draft"}
            />
            <DetailRow
              label="Pre-compute Approval"
              value={designBriefSummary?.precomputeApprovalLabel ?? "pending"}
            />
            <DetailRow
              label="Pending Plan Items"
              value={String(designBriefSummary?.pendingCalculationPlanCount ?? 0)}
            />
            <DetailRow
              label="Immediate Clarifications"
              value={String(designBriefSummary?.immediateClarificationCount ?? 0)}
            />
          </div>
          {designBriefSummary?.requirementPairs?.length ? (
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              {designBriefSummary.requirementPairs
                .filter((pair) => pair.value && pair.value !== "--")
                .slice(0, 6)
                .map((pair) => (
                  <DetailRow key={pair.label} label={pair.label} value={pair.value} />
                ))}
            </div>
          ) : null}
          {designBriefSummary?.openQuestions?.length ? (
            <ListCard
              className="mt-4"
              title="Open Questions"
              items={designBriefSummary.openQuestions}
            />
          ) : null}
          {designBriefSummary?.userConstraints?.length ? (
            <ListCard
              className="mt-4"
              title="User Constraints"
              items={designBriefSummary.userConstraints}
            />
          ) : null}
        </section>

        <section className="rounded-2xl border border-slate-200/80 bg-white/92 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.04)]">
          <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-sky-700">
            Requested Outputs
          </div>
          <div className="mt-3 space-y-3">
            {designBriefSummary?.requestedOutputs?.length ? (
              designBriefSummary.requestedOutputs.slice(0, 4).map((output) => (
                <article
                  key={output.outputId}
                  className="rounded-xl border border-slate-200/80 bg-slate-50/85 px-3 py-3"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="text-sm font-semibold text-slate-950">
                        {output.label}
                      </div>
                      <div className="mt-1 text-xs uppercase tracking-[0.16em] text-slate-500">
                        {output.supportLevel}
                      </div>
                    </div>
                    <div className="text-xs text-slate-500">{output.requestedLabel}</div>
                  </div>
                  <p className="mt-2 text-sm text-slate-700">{output.specSummary}</p>
                  {output.notes ? (
                    <p className="mt-2 text-xs text-slate-600">{output.notes}</p>
                  ) : null}
                </article>
              ))
            ) : (
              <EmptyState text="Requested outputs will appear here once the plan snapshot is written." />
            )}
          </div>
          {designBriefSummary?.scientificVerificationRequirements?.length ? (
            <ListCard
              className="mt-4"
              title="Scientific Verification"
              items={designBriefSummary.scientificVerificationRequirements.map(
                (requirement) =>
                  `${requirement.label} | ${requirement.checkType} | ${requirement.detail}`,
              )}
            />
          ) : null}
        </section>
      </div>

      <section className="rounded-2xl border border-slate-200/80 bg-white/92 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.04)]">
        <div className="flex items-center justify-between gap-3">
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-sky-700">
              Execution Outline
            </div>
            <p className="mt-1 text-sm text-slate-700">
              Show the roles, intended tools, and handoff shape before execution starts.
            </p>
          </div>
          <div className="text-sm font-semibold text-slate-950">
            {executionOutline.length} roles
          </div>
        </div>
        {executionOutline.length ? (
          <div className="mt-4 grid gap-3 xl:grid-cols-2">
            {executionOutline.map((item) => (
              <article
                key={`${item.roleId}-${item.owner}-${item.goal}`}
                className="rounded-xl border border-slate-200/80 bg-slate-50/85 px-4 py-3"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="text-sm font-semibold text-slate-950">
                      {item.roleLabel}
                    </div>
                    <div className="mt-1 text-xs uppercase tracking-[0.16em] text-slate-500">
                      {item.owner || "Unassigned"}
                    </div>
                  </div>
                  <div className="text-xs text-slate-500">{item.status || "pending"}</div>
                </div>
                <p className="mt-2 text-sm text-slate-700">{item.goal || "No goal captured yet."}</p>
                {item.targetSkills.length ? (
                  <p className="mt-2 text-xs text-slate-600">
                    Skills: {item.targetSkills.join(", ")}
                  </p>
                ) : null}
              </article>
            ))}
          </div>
        ) : (
          <EmptyState className="mt-4" text="Execution roles will appear once the lead agent commits a plan snapshot." />
        )}
      </section>

      <section className="rounded-2xl border border-slate-200/80 bg-white/92 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.04)]">
        <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-sky-700">
          Calculation Plan
        </div>
        {designBriefSummary?.calculationPlan?.length ? (
          <div className="mt-4 space-y-3">
            {designBriefSummary.calculationPlan.slice(0, 6).map((item) => (
              <article
                key={item.itemId}
                className="rounded-xl border border-slate-200/80 bg-slate-50/85 px-4 py-3"
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <div className="text-sm font-semibold text-slate-950">
                      {item.label}
                    </div>
                    <div className="mt-1 text-xs uppercase tracking-[0.16em] text-slate-500">
                      {item.category} | {item.approvalStateLabel}
                    </div>
                  </div>
                  <div className="text-sm font-semibold text-slate-900">
                    {item.proposedValue}
                  </div>
                </div>
                <div className="mt-2 grid gap-2 text-xs text-slate-600 md:grid-cols-2">
                  <div>Source: {item.sourceLabel || "Not linked"}</div>
                  <div>Confidence: {item.confidenceLabel || "Not set"}</div>
                  <div>
                    Immediate confirmation:{" "}
                    {item.requiresImmediateConfirmation ? "required" : "not required"}
                  </div>
                  <div>Origin: {item.originLabel || "Not set"}</div>
                </div>
                {item.evidenceGapNote ? (
                  <p className="mt-2 text-xs text-amber-700">{item.evidenceGapNote}</p>
                ) : null}
                {item.researcherNote ? (
                  <p className="mt-1 text-xs text-slate-600">{item.researcherNote}</p>
                ) : null}
              </article>
            ))}
          </div>
        ) : (
          <EmptyState
            className="mt-4"
            text="Calculation plan items will show up here once the lead agent proposes concrete execution parameters."
          />
        )}
      </section>
    </section>
  );
}

function PlanMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-slate-200/80 bg-slate-50/80 px-3 py-2">
      <div className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">
        {label}
      </div>
      <div className="mt-1 text-sm font-semibold text-slate-900">{value}</div>
    </div>
  );
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-slate-200/80 bg-slate-50/85 px-3 py-3">
      <div className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">
        {label}
      </div>
      <div className="mt-1 text-sm font-semibold text-slate-900">{value}</div>
    </div>
  );
}

function ListCard({
  title,
  items,
  className,
}: {
  title: string;
  items: string[];
  className?: string;
}) {
  return (
    <section
      className={`rounded-xl border border-slate-200/80 bg-slate-50/85 px-3 py-3 ${className ?? ""}`}
    >
      <div className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">
        {title}
      </div>
      <ul className="mt-2 space-y-2 text-sm text-slate-700">
        {items.slice(0, 6).map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </section>
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
    <div className={`rounded-xl border border-dashed border-slate-200 bg-slate-50/70 px-4 py-6 text-sm text-slate-600 ${className ?? ""}`}>
      {text}
    </div>
  );
}
