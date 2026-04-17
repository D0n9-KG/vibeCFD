import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createRuntimeModel,
  deleteRuntimeModel,
  loadRuntimeConfig,
  loadRuntimeModels,
  saveRuntimeConfig,
  updateRuntimeModel,
} from "./api";

function invalidateModelQueries(queryClient: ReturnType<typeof useQueryClient>) {
  void queryClient.invalidateQueries({ queryKey: ["runtime-config"] });
  void queryClient.invalidateQueries({ queryKey: ["runtime-models"] });
  void queryClient.invalidateQueries({ queryKey: ["models"] });
}

export function useRuntimeConfig({ enabled = true }: { enabled?: boolean } = {}) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["runtime-config"],
    queryFn: loadRuntimeConfig,
    enabled,
  });

  return { runtimeConfig: data ?? null, isLoading, error };
}

export function useRuntimeModels({ enabled = true }: { enabled?: boolean } = {}) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["runtime-models"],
    queryFn: loadRuntimeModels,
    enabled,
  });

  return { runtimeModels: data ?? [], isLoading, error };
}

export function useUpdateRuntimeConfig() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: saveRuntimeConfig,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["runtime-config"] });
    },
  });
}

export function useCreateRuntimeModel() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createRuntimeModel,
    onSuccess: () => {
      invalidateModelQueries(queryClient);
    },
  });
}

export function useUpdateRuntimeModel() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      modelName,
      request,
    }: {
      modelName: string;
      request: Parameters<typeof updateRuntimeModel>[1];
    }) => updateRuntimeModel(modelName, request),
    onSuccess: () => {
      invalidateModelQueries(queryClient);
    },
  });
}

export function useDeleteRuntimeModel() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteRuntimeModel,
    onSuccess: () => {
      invalidateModelQueries(queryClient);
    },
  });
}
