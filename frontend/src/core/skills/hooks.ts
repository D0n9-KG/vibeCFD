import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  enableSkill,
  loadSkillGraph,
  loadSkillLifecycle,
  loadSkillLifecycleSummaries,
  publishSkill,
  updateSkillLifecycle,
} from "./api";

import { loadSkills } from ".";

export function useSkills() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["skills"],
    queryFn: () => loadSkills(),
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
      void queryClient.invalidateQueries({ queryKey: ["threads", "search"] });
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
    }: {
      skillName: string;
      enabled: boolean;
      version_note?: string;
      binding_targets: Parameters<typeof updateSkillLifecycle>[1]["binding_targets"];
    }) =>
      updateSkillLifecycle(skillName, {
        enabled,
        version_note,
        binding_targets,
      }),
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({ queryKey: ["skills", "lifecycle"] });
      void queryClient.invalidateQueries({
        queryKey: ["skills", "lifecycle", variables.skillName],
      });
      void queryClient.invalidateQueries({ queryKey: ["skills"] });
      void queryClient.invalidateQueries({ queryKey: ["threads", "search"] });
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
