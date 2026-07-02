import { useState, useEffect } from "react";
import { RANKING_API } from "@/lib/api-config";
import { StockRankItem } from "@/types/stock";

export function useRanking(type: "fluctuation" | "volume" | "foreign" | "institution", sort: string = "0") {
    const [data, setData] = useState<StockRankItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<Error | null>(null);

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            const url = (() => {
                if (type === "volume") return RANKING_API.VOLUME;
                if (type === "foreign") return RANKING_API.FOREIGN;
                if (type === "institution") return RANKING_API.INSTITUTION;
                return RANKING_API.FLUCTUATION;
            })();

            const fullUrl = `${url}?sort=${sort}`;

            try {
                // 캐시를 사용하지 않도록 cache: "no-store" 옵션 추가
                const response = await fetch(fullUrl, { cache: "no-store" });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const result = await response.json();

                // 데이터가 비어있지 않은지 확인
                if (result && Array.isArray(result)) {
                    setData(result);
                } else if (result && result.output) {
                    setData(result.output);
                } else {
                    setData([]);
                }
            } catch (err) {
                console.error(`[API Connection Error] ${type}:`, err);
                setError(err instanceof Error ? err : new Error("Connection failed"));
                setData([]); // 에러 시 빈 배열로 초기화하여 캐시 데이터 잔상을 제거
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [type, sort]);

    return { data, loading, error };
}
