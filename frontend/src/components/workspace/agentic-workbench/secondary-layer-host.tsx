"use client";

import { type ReactNode } from "react";

import { cn } from "@/lib/utils";

export type SecondaryLayerDefinition = {
  id: string;
  label: string;
  content: ReactNode;
};

export type SecondaryLayerHostProps = {
  layers: readonly SecondaryLayerDefinition[];
  activeLayerId?: string;
  emptyState?: ReactNode;
  className?: string;
};

export function SecondaryLayerHost({
  layers,
  activeLayerId,
  emptyState = "Secondary layers will appear when a trust-critical surface is active.",
  className,
}: SecondaryLayerHostProps) {
  const activeLayer =
    layers.find((layer) => layer.id === activeLayerId) ?? layers[0];

  return (
    <section
      className={cn(
        "rounded-[22px] border border-slate-200/80 bg-white/84 p-3",
        className,
      )}
    >
      {activeLayer ? (
        <div className="space-y-2">
          <div className="text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-500">
            Secondary Layer
          </div>
          <h3 className="text-sm font-semibold text-slate-900">
            {activeLayer.label}
          </h3>
          <div className="text-sm text-slate-700">{activeLayer.content}</div>
        </div>
      ) : (
        <p className="text-sm text-slate-600">{emptyState}</p>
      )}
    </section>
  );
}
