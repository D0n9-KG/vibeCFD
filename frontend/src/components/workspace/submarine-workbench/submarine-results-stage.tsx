"use client";

import { useMemo } from "react";

import type {
  SubmarineDesignBriefPayload,
  SubmarineFinalReportPayload,
  SubmarineRuntimeSnapshotPayload,
} from "../submarine-runtime-panel.contract";
import {
  buildSubmarineAcceptanceSummary,
  buildSubmarineConclusionSectionsSummary,
  buildSubmarineDesignBriefSummary,
  buildSubmarineEvidenceIndexSummary,
  buildSubmarineFigureDeliverySummary,
  buildSubmarineOutputDeliverySummary,
  buildSubmarineReportOverviewSummary,
  buildSubmarineResultCards,
  buildSubmarineScientificStudySummary,
  groupSubmarineArtifacts,
} from "../submarine-runtime-panel.utils";

import type { SubmarineDetailModel } from "./submarine-detail-model";
import { SubmarineExperimentBoard } from "./submarine-experiment-board";
import { SubmarineOperatorBoard } from "./submarine-operator-board";
import type { SubmarineSessionModel } from "./submarine-session-model";
import { SubmarineTrustPanels } from "./submarine-trust-panels";

export function SubmarineResultsStage({
  session,
  detail,
  runtime,
  designBrief,
  finalReport,
  artifactPaths,
}: {
  session: SubmarineSessionModel;
  detail: SubmarineDetailModel;
  runtime: SubmarineRuntimeSnapshotPayload | null;
  designBrief: SubmarineDesignBriefPayload | null;
  finalReport: SubmarineFinalReportPayload | null;
  artifactPaths: string[];
}) {
  const designBriefSummary = useMemo(
    () => buildSubmarineDesignBriefSummary(designBrief),
    [designBrief],
  );
  const acceptanceSummary = useMemo(
    () => buildSubmarineAcceptanceSummary(finalReport),
    [finalReport],
  );
  const outputDeliverySummary = useMemo(
    () =>
      buildSubmarineOutputDeliverySummary({
        requestedOutputs:
          runtime?.requested_outputs ??
          designBrief?.requested_outputs ??
          finalReport?.requested_outputs,
        outputDeliveryPlan:
          runtime?.output_delivery_plan ?? finalReport?.output_delivery_plan,
      }),
    [
      designBrief?.requested_outputs,
      finalReport?.output_delivery_plan,
      finalReport?.requested_outputs,
      runtime?.output_delivery_plan,
      runtime?.requested_outputs,
    ],
  );
  const figureDeliverySummary = useMemo(
    () => buildSubmarineFigureDeliverySummary(finalReport),
    [finalReport],
  );
  const reportOverviewSummary = useMemo(
    () => buildSubmarineReportOverviewSummary(finalReport),
    [finalReport],
  );
  const conclusionSections = useMemo(
    () => buildSubmarineConclusionSectionsSummary(finalReport),
    [finalReport],
  );
  const evidenceIndex = useMemo(
    () => buildSubmarineEvidenceIndexSummary(finalReport),
    [finalReport],
  );
  const scientificStudySummary = useMemo(
    () => buildSubmarineScientificStudySummary(finalReport),
    [finalReport],
  );
  const resultCards = useMemo(
    () =>
      buildSubmarineResultCards({
        requestedOutputs: designBriefSummary?.requestedOutputs,
        outputDelivery:
          acceptanceSummary?.outputDelivery?.length
            ? acceptanceSummary.outputDelivery
            : outputDeliverySummary,
        figureDelivery: figureDeliverySummary,
        artifactPaths,
      }),
    [
      acceptanceSummary?.outputDelivery,
      artifactPaths,
      designBriefSummary?.requestedOutputs,
      figureDeliverySummary,
      outputDeliverySummary,
    ],
  );
  const groupedArtifacts = useMemo(
    () => groupSubmarineArtifacts(artifactPaths),
    [artifactPaths],
  );

  return (
    <section className="space-y-4 pb-4">
      <article className="rounded-2xl border border-slate-200/80 bg-white/92 p-5 shadow-[0_14px_30px_rgba(15,23,42,0.04)]">
        <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-sky-700">
          Results Stage
        </div>
        <h2 className="mt-2 text-xl font-semibold tracking-tight text-slate-950">
          Evidence delivery, post-processing, and report package
        </h2>
        <p className="mt-3 text-sm leading-7 text-slate-700">
          Preserve provenance, reproducibility, remediation, and follow-up context before shipping the conclusion.
        </p>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <Metric label="Evidence Ready" value={session.summary.evidenceReady ? "yes" : "no"} />
          <Metric label="Conclusion Sections" value={String(conclusionSections.length)} />
          <Metric label="Evidence Groups" value={String(evidenceIndex?.groupCount ?? 0)} />
          <Metric label="Artifacts" value={String(artifactPaths.length)} />
        </div>
        {!session.summary.evidenceReady ? (
          <div className="mt-4 rounded-xl border border-amber-200/80 bg-amber-50/80 px-4 py-3 text-sm text-amber-900">
            The session is already in a supervisor-facing state, but the final report artifact has not landed yet.
            Keep the right rail open and inspect the draft package below before confirming delivery.
          </div>
        ) : null}
      </article>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.1fr)_minmax(320px,0.9fr)]">
        <section className="rounded-2xl border border-slate-200/80 bg-white/92 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.04)]">
          <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-sky-700">
            Report Overview
          </div>
          {reportOverviewSummary ? (
            <>
              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                <DetailRow
                  label="Allowed Claim Level"
                  value={reportOverviewSummary.allowedClaimLevelLabel}
                />
                <DetailRow
                  label="Review Status"
                  value={reportOverviewSummary.reviewStatusLabel}
                />
                <DetailRow
                  label="Reproducibility"
                  value={reportOverviewSummary.reproducibilityStatusLabel}
                />
                <DetailRow
                  label="Current Conclusion"
                  value={reportOverviewSummary.currentConclusion}
                />
              </div>
              <div className="mt-4 rounded-xl border border-slate-200/80 bg-slate-50/85 px-4 py-3">
                <div className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">
                  Recommended Next Step
                </div>
                <div className="mt-1 text-sm text-slate-700">
                  {reportOverviewSummary.recommendedNextStep}
                </div>
              </div>
            </>
          ) : (
            <EmptyState
              className="mt-4"
              text={
                runtime?.report_virtual_path
                  ? `Draft report package detected at ${runtime.report_virtual_path}`
                  : "The report overview will appear once the result-reporting artifact is available."
              }
            />
          )}
        </section>

        <section className="rounded-2xl border border-slate-200/80 bg-white/92 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.04)]">
          <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-sky-700">
            Evidence Map
          </div>
          {evidenceIndex?.groups?.length ? (
            <div className="mt-4 space-y-3">
              {evidenceIndex.groups.slice(0, 6).map((group) => (
                <article
                  key={group.groupId}
                  className="rounded-xl border border-slate-200/80 bg-slate-50/85 px-4 py-3"
                >
                  <div className="text-sm font-semibold text-slate-950">
                    {group.groupTitle}
                  </div>
                  <div className="mt-1 text-xs uppercase tracking-[0.16em] text-slate-500">
                    {group.groupId}
                  </div>
                  <ul className="mt-2 space-y-2 text-xs text-slate-600">
                    {group.artifactPaths.slice(0, 3).map((path) => (
                      <li key={path} className="break-all">
                        {path}
                      </li>
                    ))}
                    {group.provenanceManifestPath && group.provenanceManifestPath !== "--" ? (
                      <li className="break-all">{group.provenanceManifestPath}</li>
                    ) : null}
                  </ul>
                </article>
              ))}
            </div>
          ) : (
            <EmptyState
              className="mt-4"
              text="Evidence groups will populate here once the final report builds its provenance index."
            />
          )}
        </section>
      </div>

      <section className="rounded-2xl border border-slate-200/80 bg-white/92 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.04)]">
        <div className="flex items-center justify-between gap-3">
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-sky-700">
              Output Delivery
            </div>
            <p className="mt-1 text-sm text-slate-700">
              Requested outputs, post-processing products, and report-bound artifacts stay visible together.
            </p>
          </div>
          <div className="text-sm font-semibold text-slate-950">{resultCards.length} outputs</div>
        </div>
        {resultCards.length ? (
          <div className="mt-4 grid gap-3 xl:grid-cols-2">
            {resultCards.map((card) => (
              <article
                key={card.outputId}
                className="rounded-xl border border-slate-200/80 bg-slate-50/85 px-4 py-3"
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <div className="text-sm font-semibold text-slate-950">{card.label}</div>
                    <div className="mt-1 text-xs uppercase tracking-[0.16em] text-slate-500">
                      {card.supportLevel} | {card.deliveryStatus}
                    </div>
                  </div>
                  <div className="text-xs text-slate-500">{card.requestedLabel}</div>
                </div>
                <p className="mt-2 text-sm text-slate-700">{card.specSummary}</p>
                {card.detail ? <p className="mt-2 text-xs text-slate-600">{card.detail}</p> : null}
                {card.figureCaption ? (
                  <p className="mt-2 text-xs text-slate-600">{card.figureCaption}</p>
                ) : null}
                {card.artifactPaths.length ? (
                  <ul className="mt-3 space-y-2 text-xs text-slate-600">
                    {card.artifactPaths.slice(0, 4).map((path) => (
                      <li key={path} className="break-all">
                        {path}
                      </li>
                    ))}
                  </ul>
                ) : null}
              </article>
            ))}
          </div>
        ) : (
          <EmptyState
            className="mt-4"
            text="Delivered outputs will appear here as soon as the agent links post-processing artifacts."
          />
        )}
      </section>

      {(conclusionSections.length > 0 || scientificStudySummary) ? (
        <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(320px,0.95fr)]">
          <section className="rounded-2xl border border-slate-200/80 bg-white/92 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.04)]">
            <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-sky-700">
              Conclusion Draft
            </div>
            {conclusionSections.length ? (
              <div className="mt-4 space-y-3">
                {conclusionSections.slice(0, 4).map((section) => (
                  <article
                    key={section.conclusionId}
                    className="rounded-xl border border-slate-200/80 bg-slate-50/85 px-4 py-3"
                  >
                    <div className="text-sm font-semibold text-slate-950">{section.title}</div>
                    <div className="mt-1 text-xs uppercase tracking-[0.16em] text-slate-500">
                      {section.claimLevelLabel} | {section.confidenceLabel}
                    </div>
                    <p className="mt-2 text-sm text-slate-700">{section.summary}</p>
                    {section.inlineSourceRefs.length ? (
                      <p className="mt-2 text-xs text-slate-600">
                        Sources: {section.inlineSourceRefs.join(", ")}
                      </p>
                    ) : null}
                    {section.evidenceGapNotes.length ? (
                      <p className="mt-2 text-xs text-amber-700">
                        Gaps: {section.evidenceGapNotes.join(" | ")}
                      </p>
                    ) : null}
                  </article>
                ))}
              </div>
            ) : (
              <EmptyState
                className="mt-4"
                text="Conclusion sections will appear here once the report writer assembles the final claims."
              />
            )}
          </section>

          <section className="rounded-2xl border border-slate-200/80 bg-white/92 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.04)]">
            <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-sky-700">
              Post-processing Studies
            </div>
            {scientificStudySummary ? (
              <div className="mt-4 space-y-3">
                <DetailRow
                  label="Execution Status"
                  value={scientificStudySummary.executionStatusLabel}
                />
                <DetailRow
                  label="Workflow Status"
                  value={scientificStudySummary.workflowStatusLabel}
                />
                <DetailRow
                  label="Manifest"
                  value={scientificStudySummary.manifestPath}
                />
                {scientificStudySummary.studies.slice(0, 3).map((study) => (
                  <article
                    key={study.studyType}
                    className="rounded-xl border border-slate-200/80 bg-slate-50/85 px-4 py-3"
                  >
                    <div className="text-sm font-semibold text-slate-950">
                      {study.summaryLabel}
                    </div>
                    <div className="mt-1 text-xs uppercase tracking-[0.16em] text-slate-500">
                      {study.workflowStatusLabel} | {study.studyExecutionStatusLabel}
                    </div>
                    <p className="mt-2 text-sm text-slate-700">{study.workflowDetail}</p>
                  </article>
                ))}
              </div>
            ) : (
              <EmptyState
                className="mt-4"
                text="Post-processing studies will appear here once the report captures compare and study artifacts."
              />
            )}
          </section>
        </div>
      ) : null}

      <SubmarineTrustPanels panels={detail.trustPanels} />
      <SubmarineExperimentBoard experimentBoard={detail.experimentBoard} />
      <SubmarineOperatorBoard operatorBoard={detail.operatorBoard} />

      <section className="rounded-2xl border border-slate-200/80 bg-white/92 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.04)]">
        <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-sky-700">
          Report Package Artifacts
        </div>
        {groupedArtifacts.length ? (
          <div className="mt-4 grid gap-3 xl:grid-cols-2">
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
                  {group.paths.slice(0, 4).map((path) => (
                    <li key={path} className="break-all">
                      {path}
                    </li>
                  ))}
                </ul>
              </article>
            ))}
          </div>
        ) : (
          <EmptyState
            className="mt-4"
            text="Submarine report artifacts will appear here once the workspace persists report-bound files."
          />
        )}
      </section>
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

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-slate-200/80 bg-slate-50/85 px-3 py-3">
      <div className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">
        {label}
      </div>
      <div className="mt-1 break-all text-sm text-slate-900">{value}</div>
    </div>
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
