type ArtifactCarrier = {
  artifact_virtual_paths?: unknown;
} | null;

type ThreadValuesLike = {
  artifacts?: unknown;
  submarine_runtime?: ArtifactCarrier;
  submarine_skill_studio?: ArtifactCarrier;
};

function asArtifactList(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value.filter((item): item is string => typeof item === "string");
}

export function collectThreadArtifacts(values: ThreadValuesLike): string[] {
  const merged = [
    ...asArtifactList(values.artifacts),
    ...asArtifactList(values.submarine_runtime?.artifact_virtual_paths),
    ...asArtifactList(values.submarine_skill_studio?.artifact_virtual_paths),
  ];

  return merged.filter((artifact, index) => merged.indexOf(artifact) === index);
}
