import { useQuery } from "@tanstack/react-query";
import { fetchSmartMoneyFlow } from "@/lib/api";

export function useSmartMoneyData(symbol: string) {
  return useQuery({
    queryKey: ["smart-money", symbol],
    queryFn: () => fetchSmartMoneyFlow(symbol),
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
    retry: 1,
  });
}
