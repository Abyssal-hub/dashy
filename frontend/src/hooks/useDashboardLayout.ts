import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getDashboardLayout, updateDashboardLayout } from "@/lib/api";

export function useDashboardLayout() {
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["dashboardLayout"],
    queryFn: getDashboardLayout,
  });

  const mutation = useMutation({
    mutationFn: updateDashboardLayout,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dashboardLayout"] });
    },
  });

  return {
    layout: data,
    isLoading,
    updateLayout: mutation.mutate,
    isUpdating: mutation.isPending,
  };
}
