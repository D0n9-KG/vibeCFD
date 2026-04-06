"use client";

import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";

import {
  SKILL_STUDIO_BINDING_ROLE_IDS,
  type SkillStudioLifecycleBindingTarget,
} from "../skill-studio-workbench.utils";

import type { SkillStudioDetailModel } from "./skill-studio-detail-model";

type SkillStudioPublishStageProps = {
  detail: SkillStudioDetailModel;
  enabled: boolean;
  versionNote: string;
  explicitBindingRoleIds: string[];
  busy: boolean;
  canPublish: boolean;
  canRollback: boolean;
  onEnabledChange: (nextValue: boolean) => void;
  onVersionNoteChange: (nextValue: string) => void;
  onToggleBindingRole: (roleId: string) => void;
  onSaveLifecycle: () => void;
  onPublish: () => void;
  onRollback: () => void;
};

export function SkillStudioPublishStage({
  detail,
  enabled,
  versionNote,
  explicitBindingRoleIds,
  busy,
  canPublish,
  canRollback,
  onEnabledChange,
  onVersionNoteChange,
  onToggleBindingRole,
  onSaveLifecycle,
  onPublish,
  onRollback,
}: SkillStudioPublishStageProps) {
  return (
    <section className="space-y-4">
      <section className="rounded-[28px] border border-slate-200/80 bg-white/95 p-5 shadow-[0_20px_48px_rgba(15,23,42,0.07)]">
        <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-orange-700">
          Publish
        </div>
        <div className="mt-4 grid gap-3 md:grid-cols-4">
          <Metric label="Revisions" value={String(detail.publish.revisionCount)} />
          <Metric label="Bindings" value={String(detail.publish.bindingCount)} />
          <Metric
            label="Blocked Gates"
            value={String(detail.publish.blockedGateCount)}
          />
          <Metric
            label="Rollback"
            value={detail.publish.rollbackTargetId ?? "Unavailable"}
          />
        </div>
      </section>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.1fr)_minmax(320px,0.9fr)]">
        <section className="rounded-[24px] border border-slate-200/80 bg-white/92 p-4 shadow-[0_18px_40px_rgba(15,23,42,0.06)]">
          <div className="flex items-center justify-between gap-3">
            <div>
              <div className="text-sm font-semibold text-slate-950">Lifecycle Controls</div>
              <p className="mt-1 text-sm text-slate-600">
                Keep the publish state, revision note, and explicit bindings aligned
                before shipping the package.
              </p>
            </div>
            <div className="flex items-center gap-2 text-sm text-slate-700">
              <span>Enabled</span>
              <Switch checked={enabled} onCheckedChange={onEnabledChange} />
            </div>
          </div>

          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <Metric label="Active Revision" value={detail.publish.activeRevisionId ?? "Draft"} />
            <Metric
              label="Published Revision"
              value={detail.publish.publishedRevisionId ?? "Not published"}
            />
          </div>

          <div className="mt-4">
            <div className="text-sm font-semibold text-slate-950">Version Note</div>
            <Textarea
              className="mt-2 min-h-28"
              value={versionNote}
              onChange={(event) => onVersionNoteChange(event.target.value)}
              placeholder="Describe what changed and why this revision is safe to publish."
            />
          </div>

          <div className="mt-4">
            <div className="text-sm font-semibold text-slate-950">Explicit Bindings</div>
            <div className="mt-3 grid gap-2 md:grid-cols-2">
              {SKILL_STUDIO_BINDING_ROLE_IDS.map((roleId) => {
                const selected = explicitBindingRoleIds.includes(roleId);
                return (
                  <button
                    key={roleId}
                    type="button"
                    className={`rounded-2xl border px-3 py-3 text-left text-sm transition-colors ${
                      selected
                        ? "border-orange-200 bg-orange-50 text-orange-900"
                        : "border-slate-200 bg-slate-50 text-slate-700"
                    }`}
                    onClick={() => onToggleBindingRole(roleId)}
                  >
                    {roleId}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
            <Button variant="outline" disabled={busy} onClick={onSaveLifecycle}>
              Save Lifecycle
            </Button>
            <Button disabled={busy || !canPublish} onClick={onPublish}>
              Publish Draft
            </Button>
            <Button
              variant="outline"
              disabled={busy || !canRollback}
              onClick={onRollback}
            >
              Roll Back
            </Button>
          </div>
        </section>

        <section className="rounded-[24px] border border-slate-200/80 bg-white/92 p-4 shadow-[0_18px_40px_rgba(15,23,42,0.06)]">
          <div className="text-sm font-semibold text-slate-950">Publish Gates</div>
          <div className="mt-3 space-y-2">
            {detail.publish.gates.length > 0 ? (
              detail.publish.gates.map((gate) => (
                <article
                  key={gate.id}
                  className="rounded-2xl border border-slate-200/80 bg-slate-50/80 px-3 py-3"
                >
                  <div className="flex items-center justify-between gap-3">
                    <div className="text-sm font-medium text-slate-950">{gate.label}</div>
                    <div className="text-xs uppercase tracking-[0.16em] text-slate-500">
                      {gate.status}
                    </div>
                  </div>
                </article>
              ))
            ) : (
              <p className="text-sm text-slate-600">
                Publish blockers and readiness gates will appear here.
              </p>
            )}
          </div>
          {detail.publish.nextActions.length > 0 ? (
            <p className="mt-3 text-sm text-slate-700">
              Next: {detail.publish.nextActions[0]}
            </p>
          ) : null}
          {detail.publish.bindingTargets.length > 0 ? (
            <p className="mt-3 text-xs text-slate-600">
              Active bindings: {formatBindingTargets(detail.publish.bindingTargets)}
            </p>
          ) : null}
        </section>
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-slate-200/80 bg-slate-50/80 px-3 py-3">
      <div className="text-[11px] uppercase tracking-[0.18em] text-slate-500">{label}</div>
      <div className="mt-1 text-lg font-semibold text-slate-950">{value}</div>
    </div>
  );
}

function formatBindingTargets(targets: SkillStudioLifecycleBindingTarget[]) {
  return targets
    .map((target) => `${target.role_id} (${target.mode})`)
    .join(" | ");
}
