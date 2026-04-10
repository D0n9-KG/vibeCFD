"use client";

import { type ReactNode, useEffect, useMemo, useRef, useState } from "react";

import { SecondaryLayerHost } from "@/components/workspace/agentic-workbench";
import type {
  SubmarineDesignBriefPayload,
  SubmarineFinalReportPayload,
  SubmarineRuntimeSnapshotPayload,
} from "@/components/workspace/submarine-runtime-panel.contract";

import type { SubmarineDetailModel } from "./submarine-detail-model";
import { SubmarineExperimentBoard } from "./submarine-experiment-board";
import { SubmarineOperatorBoard } from "./submarine-operator-board";
import {
  buildSliceContextNotesModel,
  buildSliceEvidenceBadgesModel,
  buildSliceFactsModel,
} from "./submarine-research-canvas.model";
import { SubmarineResearchSliceCard } from "./submarine-research-slice-card";
import { SubmarineResearchSliceHistoryBanner } from "./submarine-research-slice-history-banner";
import { SubmarineResearchSliceRibbon } from "./submarine-research-slice-ribbon";
import {
  resolveSubmarineSecondaryLayerIds,
  type SubmarineSecondaryLayerId,
} from "./submarine-secondary-layers.model";
import type {
  SubmarineResearchSliceId,
  SubmarineSessionModel,
} from "./submarine-session-model";
import { SubmarineTrustPanels } from "./submarine-trust-panels";

type SubmarineResearchCanvasProps = {
  session: SubmarineSessionModel;
  detail: SubmarineDetailModel;
  runtime: SubmarineRuntimeSnapshotPayload | null;
  designBrief: SubmarineDesignBriefPayload | null;
  finalReport: SubmarineFinalReportPayload | null;
  artifactPaths: readonly string[];
};

type DrawerId = SubmarineSecondaryLayerId;



function OverviewMetric({ label, value }: { label: string; value: string }) {
  return (
    <article className="rounded-2xl border border-white/90 bg-white/88 px-3 py-3">
      <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">
        {label}
      </div>
      <div className="mt-1 text-sm font-semibold leading-6 text-slate-900">{value}</div>
    </article>
  );
}
export function SubmarineResearchCanvas({
  session,
  detail,
  runtime,
  designBrief,
  finalReport,
  artifactPaths,
}: SubmarineResearchCanvasProps) {
  const [ribbonExpanded, setRibbonExpanded] = useState(false);
  const [inspectedSliceId, setInspectedSliceId] = useState<SubmarineResearchSliceId | null>(
    session.historyInspection.isViewingHistory ? session.viewedSlice.id : null,
  );

  const displayedSlice =
    session.slices.find((slice) => slice.id === inspectedSliceId) ?? session.currentSlice;
  const isViewingHistory = displayedSlice.id !== session.currentSlice.id;
  const [surfaceMotionPhase, setSurfaceMotionPhase] = useState<"staged" | "settled">(
    "settled",
  );
  const hasMountedSurfaceRef = useRef(false);

  const [activeDrawerId, setActiveDrawerId] = useState<DrawerId>(() =>
    resolveSubmarineSecondaryLayerIds({
      sliceId: displayedSlice.id,
      detail,
    })[0] ?? "operator",
  );

  useEffect(() => {
    if (!inspectedSliceId) {
      return;
    }

    const stillExists = session.slices.some((slice) => slice.id === inspectedSliceId);
    if (!stillExists || inspectedSliceId === session.currentSlice.id) {
      setInspectedSliceId(null);
    }
  }, [inspectedSliceId, session.currentSlice.id, session.slices]);

  useEffect(() => {
    if (!hasMountedSurfaceRef.current) {
      hasMountedSurfaceRef.current = true;
      return;
    }

    setSurfaceMotionPhase("staged");
    const frameId = window.requestAnimationFrame(() => {
      setSurfaceMotionPhase("settled");
    });

    return () => {
      window.cancelAnimationFrame(frameId);
    };
  }, [displayedSlice.id, isViewingHistory]);

  const drawerLayers = useMemo(() => {
    const layersById: Record<DrawerId, { id: DrawerId; label: string; content: ReactNode }> = {
      trust: {
        id: "trust",
        label: "证据与可信度",
        content: <SubmarineTrustPanels panels={detail.trustPanels} />,
      },
      studies: {
        id: "studies",
        label: "对比试验与后处理结果",
        content: <SubmarineExperimentBoard experimentBoard={detail.experimentBoard} />,
      },
      operator: {
        id: "operator",
        label: "研究判断与后续安排",
        content: <SubmarineOperatorBoard operatorBoard={detail.operatorBoard} />,
      },
    };

    return resolveSubmarineSecondaryLayerIds({
      sliceId: displayedSlice.id,
      detail,
    }).map((layerId) => layersById[layerId]);
  }, [detail, displayedSlice.id]);

  useEffect(() => {
    setActiveDrawerId((current) => {
      if (drawerLayers.length === 0) {
        return current;
      }

      const firstLayer = drawerLayers[0];
      return drawerLayers.some((layer) => layer.id === current)
        ? current
        : firstLayer
          ? firstLayer.id
          : current;
    });
  }, [drawerLayers]);

  const executionPlanCount =
    runtime?.execution_plan?.length ?? designBrief?.execution_outline?.length ?? 0;
  const skillNames = useMemo(
    () =>
      [
        ...(runtime?.execution_plan?.flatMap((item) => item.target_skills ?? []) ?? []),
        ...(runtime?.activity_timeline?.flatMap((item) => item.skill_names ?? []) ?? []),
      ].filter(
        (skill, index, all): skill is string =>
          Boolean(skill) && all.indexOf(skill) === index,
      ),
    [runtime?.activity_timeline, runtime?.execution_plan],
  );
  const requestedOutputs = useMemo(
    () =>
      runtime?.requested_outputs
        ?.map((item) => item?.label ?? item?.requested_label ?? "")
        .filter(Boolean) ??
      designBrief?.requested_outputs
        ?.map((item) => item?.label ?? item?.requested_label ?? "")
        .filter(Boolean) ??
      [],
    [designBrief?.requested_outputs, runtime?.requested_outputs],
  );
  const verificationRequirements = useMemo(
    () =>
      designBrief?.scientific_verification_requirements
        ?.map((item) => item?.summary_zh ?? item?.label ?? "")
        .filter(Boolean) ?? [],
    [designBrief?.scientific_verification_requirements],
  );

  const facts = useMemo(
    () =>
      buildSliceFactsModel({
        sliceId: displayedSlice.id,
        pendingApprovalCount: session.negotiation.pendingApprovalCount,
        runtimeStatus: runtime?.runtime_status ?? null,
        artifactCount: artifactPaths.length,
        executionPlanCount,
        skillNames,
        requestedOutputs,
      }),
    [
      artifactPaths.length,
      displayedSlice.id,
      executionPlanCount,
      requestedOutputs,
      runtime?.runtime_status,
      session.negotiation.pendingApprovalCount,
      skillNames,
    ],
  );

  const evidenceBadges = useMemo(
    () =>
      buildSliceEvidenceBadgesModel({
        runtime,
        designBrief,
        finalReport,
        artifactPaths,
        requestedOutputs,
      }),
    [artifactPaths, designBrief, finalReport, requestedOutputs, runtime],
  );

  const contextNotes = useMemo(
    () =>
      buildSliceContextNotesModel({
        sliceId: displayedSlice.id,
        runtime,
        designBrief,
        finalReport,
        requestedOutputs,
        verificationRequirements,
        skillNames,
        executionPlanCount,
        artifactPaths,
      }),
    [
      artifactPaths,
      designBrief,
      displayedSlice.id,
      executionPlanCount,
      finalReport,
      requestedOutputs,
      runtime,
      skillNames,
      verificationRequirements,
    ],
  );

  return (
    <div className="flex h-full min-h-0 flex-col gap-4">
      <SubmarineResearchSliceRibbon
        slices={session.slices}
        activeSliceId={session.currentSlice.id}
        viewedSliceId={displayedSlice.id}
        expanded={ribbonExpanded}
        onSelectSlice={(sliceId) => {
          setInspectedSliceId(sliceId === session.currentSlice.id ? null : sliceId);
        }}
        onToggleExpanded={() => {
          setRibbonExpanded((current) => !current);
        }}
      />

      <section className="rounded-[24px] border border-sky-200/60 bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(244,249,253,0.96))] px-4 py-4 shadow-[0_18px_40px_rgba(14,165,233,0.08)]">
        <div className="grid gap-3 md:grid-cols-3">
          <OverviewMetric label="当前切片" value={session.currentSlice.title} />
          <OverviewMetric
            label="查看模式"
            value={isViewingHistory ? `正在查看 ${displayedSlice.title}` : "跟随当前研究"}
          />
          <OverviewMetric
            label="研究链状态"
            value={session.summary.evidenceReady ? "报告可审阅" : "研究推进中"}
          />
        </div>
      </section>

      <div
        className={[
          "flex flex-col gap-4 motion-safe:transition-[opacity,transform] motion-safe:duration-300 motion-safe:ease-out motion-reduce:transition-none",
          surfaceMotionPhase === "staged"
            ? "motion-safe:translate-y-1 motion-safe:opacity-0"
            : "motion-safe:translate-y-0 motion-safe:opacity-100",
        ].join(" ")}
      >
        {isViewingHistory ? (
          <SubmarineResearchSliceHistoryBanner
            slice={displayedSlice}
            onReturnToCurrent={() => {
              setInspectedSliceId(null);
            }}
          />
        ) : null}

        <SubmarineResearchSliceCard
          slice={displayedSlice}
          isHistoricalView={isViewingHistory}
          facts={facts}
          evidenceBadges={evidenceBadges}
          contextNotes={contextNotes}
        />
      </div>

      {session.liveProgress.visible ? (
        <section
          data-live-progress="submarine"
          className="rounded-[24px] border border-sky-200/70 bg-white/92 px-4 py-4 shadow-[0_18px_40px_rgba(14,165,233,0.06)]"
        >
          <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-sky-700">
            实时进展
          </div>
          <h3 className="mt-2 text-lg font-semibold text-slate-950">
            结构化 CFD 产物生成中
          </h3>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            {session.liveProgress.statusSummary}
          </p>

          <div className="mt-4 grid gap-3 md:grid-cols-3">
            <OverviewMetric label="状态" value={session.liveProgress.statusLabel} />
            <OverviewMetric
              label="主智能体反馈"
              value={session.liveProgress.latestAssistantPreview ?? "暂未给出新的主智能体反馈。"}
            />
            <OverviewMetric
              label="研究者输入"
              value={session.liveProgress.latestUserPreview ?? "暂未收到新的研究者输入。"}
            />
          </div>
        </section>
      ) : null}

      {drawerLayers.length > 0 ? (
        <SecondaryLayerHost
          layers={drawerLayers}
          activeLayerId={activeDrawerId}
          className="border-slate-200/70 bg-transparent"
        />
      ) : null}
    </div>
  );
}
