import { useQuery } from "@tanstack/react-query";
import { getModules } from "@/lib/api";

export function useModules() {
  return useQuery({
    queryKey: ["modules"],
    queryFn: getModules,
  });
}
