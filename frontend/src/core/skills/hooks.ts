import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  enableSkill,
  loadSkillGraph,
  loadSkillLifecycle,
  loadSkillLifecycleSummaries,
  publishSkill,
  recordDryRunEvidence,
  rollbackSkillRevision,
  updateSkillLifecycle,
} from "./api";

import { loadSkills } from ".";

export function useSkills({ enabled = true }: { enabled?: boolean } = {}) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["skills"],
    queryFn: () => loadSkills(),
    enabled,
  });
  return { skills: data ?? [], isLoading, error };
}

export function useEnableSkill() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      skillName,
      enabled,
    }: {
      skillName: string;
      enabled: boolean;
    }) => {
      await enableSkill(skillName, enabled);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["skills"] });
      void queryClient.invalidateQueries({ queryKey: ["skills", "lifecycle"] });
    },
  });
}

export function usePublishSkill() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: publishSkill,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["skills", "lifecycle"] });
      void queryClient.invalidateQueries({ queryKey: ["skills"] });
      void queryClient.invalidateQueries({
        queryKey: ["skills", "graph"],
        exact: false,
      });
      void queryClient.invalidateQueries({ queryKey: ["threads", "search"] });
    },
  });
}

export function useRecordDryRunEvidence() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (
      variables: Parameters<typeof recordDryRunEvidence>[0] & {
        isMock?: boolean;
        publishReadinessPath?: string | null;
        dryRunEvidencePath?: string | null;
      },
    ) => recordDryRunEvidence(variables),
    onSuccess: (_data, variables) => {
      const isMock = Boolean(variables.isMock);
      void queryClient.invalidateQueries({
        queryKey: ["artifact", variables.path, variables.thread_id, isMock],
      });
      if (variables.publishReadinessPath) {
        void queryClient.invalidateQueries({
          queryKey: [
            "artifact",
            variables.publishReadinessPath,
            variables.thread_id,
            isMock,
          ],
        });
      }
      if (variables.dryRunEvidencePath) {
        void queryClient.invalidateQueries({
          queryKey: [
            "artifact",
            variables.dryRunEvidencePath,
            variables.thread_id,
            isMock,
          ],
        });
      }
      void queryClient.invalidateQueries({ queryKey: ["skills", "lifecycle"] });
    },
  });
}

export function useSkillLifecycleSummaries({
  enabled = true,
}: {
  enabled?: boolean;
} = {}) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["skills", "lifecycle"],
    queryFn: loadSkillLifecycleSummaries,
    enabled,
  });
  return { lifecycleSummaries: data ?? [], isLoading, error };
}

export function useSkillLifecycle({
  skillName,
  enabled = true,
}: {
  skillName?: string;
  enabled?: boolean;
}) {
  return useQuery({
    queryKey: ["skills", "lifecycle", skillName ?? "__missing__"],
    queryFn: () => loadSkillLifecycle(skillName!),
    enabled: enabled && Boolean(skillName),
  });
}

export function useUpdateSkillLifecycle() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      skillName,
      enabled,
      version_note,
      binding_targets,
      thread_id,
      path,
    }: {
      skillName: string;
      enabled: boolean;
      version_note?: string;
      binding_targets: Parameters<typeof updateSkillLifecycle>[1]["binding_targets"];
      thread_id?: string;
      path?: string;
    }) =>
      updateSkillLifecycle(skillName, {
        enabled,
        version_note,
        binding_targets,
        thread_id,
        path,
      }),
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({ queryKey: ["skills", "lifecycle"] });
      void queryClient.invalidateQueries({
        queryKey: ["skills", "lifecycle", variables.skillName],
      });
      void queryClient.invalidateQueries({ queryKey: ["skills"] });
      void queryClient.invalidateQueries({
        queryKey: ["skills", "graph"],
        exact: false,
      });
      void queryClient.invalidateQueries({ queryKey: ["threads", "search"] });
    },
  });
}

export function useRollbackSkillRevision() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      skillName,
      revision_id,
    }: {
      skillName: string;
      revision_id: string;
    }) => rollbackSkillRevision(skillName, { revision_id }),
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({ queryKey: ["skills", "lifecycle"] });
      void queryClient.invalidateQueries({
        queryKey: ["skills", "lifecycle", variables.skillName],
      });
      void queryClient.invalidateQueries({ queryKey: ["skills"] });
      void queryClient.invalidateQueries({ queryKey: ["threads", "search"] });
      void queryClient.invalidateQueries({
        queryKey: ["skills", "graph", variables.skillName],
        exact: false,
      });
    },
  });
}

export function useSkillGraph({
  skillName,
  isMock = false,
  enabled = true,
}: {
  skillName?: string;
  isMock?: boolean;
  enabled?: boolean;
}) {
  return useQuery({
    queryKey: ["skills", "graph", skillName ?? "__all__", isMock],
    queryFn: () => loadSkillGraph({ skillName, isMock }),
    enabled,
  });
}
