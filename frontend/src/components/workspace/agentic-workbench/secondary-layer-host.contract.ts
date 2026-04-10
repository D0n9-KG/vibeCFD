export type SecondaryLayerRecord<TContent = unknown> = {
  id: string;
  label: string;
  content: TContent;
};

export type SecondaryLayerSelection<TContent = unknown> =
  | { kind: "empty" }
  | { kind: "missing"; activeLayerId: string }
  | { kind: "active"; layer: SecondaryLayerRecord<TContent> };

export type SelectSecondaryLayerOptions<TContent = unknown> = {
  layers: readonly SecondaryLayerRecord<TContent>[];
  activeLayerId?: string;
};

export const DEFAULT_SECONDARY_LAYER_EMPTY_STATE = "当前没有可展开的详情抽屉。";

export const DEFAULT_SECONDARY_LAYER_MISSING_STATE = "请求的详情抽屉暂时不可用。";

export function selectSecondaryLayer<TContent>({
  layers,
  activeLayerId,
}: SelectSecondaryLayerOptions<TContent>): SecondaryLayerSelection<TContent> {
  if (activeLayerId) {
    const requestedLayer = layers.find((layer) => layer.id === activeLayerId);

    return requestedLayer
      ? { kind: "active", layer: requestedLayer }
      : { kind: "missing", activeLayerId };
  }

  const defaultLayer = layers[0];

  return defaultLayer ? { kind: "active", layer: defaultLayer } : { kind: "empty" };
}
