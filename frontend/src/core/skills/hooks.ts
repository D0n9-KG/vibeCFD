import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { enableSkill, loadSkillGraph, publishSkill } from "./api";

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
    },
  });
}

export function usePublishSkill() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: publishSkill,
    onSuccess: () => {
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
