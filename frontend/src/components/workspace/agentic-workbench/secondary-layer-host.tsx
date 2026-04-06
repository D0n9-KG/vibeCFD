"use client";

import { type ReactNode } from "react";

import { cn } from "@/lib/utils";

import {
  DEFAULT_SECONDARY_LAYER_EMPTY_STATE,
  DEFAULT_SECONDARY_LAYER_MISSING_STATE,
  selectSecondaryLayer,
  type SecondaryLayerRecord,
} from "./secondary-layer-host.contract";

export type SecondaryLayerDefinition = SecondaryLayerRecord<ReactNode>;

export type SecondaryLayerHostProps = {
  layers: readonly SecondaryLayerDefinition[];
  activeLayerId?: string;
  emptyState?: ReactNode;
  missingState?: ReactNode;
  className?: string;
};

export function SecondaryLayerHost({
  layers,
  activeLayerId,
  emptyState = DEFAULT_SECONDARY_LAYER_EMPTY_STATE,
  missingState = DEFAULT_SECONDARY_LAYER_MISSING_STATE,
  className,
}: SecondaryLayerHostProps) {
  const selection = selectSecondaryLayer({
    layers,
    activeLayerId,
  });

  return (
    <section
      className={cn(
        "rounded-[22px] border border-slate-200/80 bg-white/84 p-3",
        className,
      )}
    >
      {selection.kind === "active" ? (
        <div className="space-y-2">
          <div className="text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-500">
            Secondary Layer
          </div>
          <h3 className="text-sm font-semibold text-slate-900">
            {selection.layer.label}
          </h3>
          <div className="text-sm text-slate-700">{selection.layer.content}</div>
        </div>
      ) : selection.kind === "missing" ? (
        <p className="text-sm text-slate-600">{missingState}</p>
      ) : (
        <p className="text-sm text-slate-600">{emptyState}</p>
      )}
    </section>
  );
}
