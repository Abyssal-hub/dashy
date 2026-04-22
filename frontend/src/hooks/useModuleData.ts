import { useQuery } from "@tanstack/react-query";
import { getModuleData } from "@/lib/api";
import { MODULE_REFRESH_INTERVAL } from "@/lib/constants";

export function useModuleData(moduleId: string, size?: string) {
  return useQuery({
    queryKey: ["moduleData", moduleId, size],
    queryFn: () => getModuleData(moduleId, size),
    refetchInterval: MODULE_REFRESH_INTERVAL,
    enabled: !!moduleId,
  });
}
