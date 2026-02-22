import ResultsWorkspace from "../components/results/ResultsWorkspace";
import styles from "../redditdemand.module.css";
import {
  getMentionsTrend,
  getUsersBySubreddit,
  getTopMatches,
  getGrowthMomentum,
  type TimePoint,
  type TopMatch,
  type GrowthData,
} from "../lib/api";

type SearchParamsInput = Record<string, string | string[] | undefined>;

function firstParam(value: string | string[] | undefined): string {
  if (Array.isArray(value)) return value[0] ?? "";
  return value ?? "";
}

async function fetchAnalytics(query: string): Promise<{
  points: TimePoint[];
  subreddits: Record<string, string[]>;
  topMatches: TopMatch[];
  growthData: GrowthData;
}> {
  const [points, subreddits, topMatches, growthData] = await Promise.allSettled([
    getMentionsTrend(query),
    getUsersBySubreddit(query),
    getTopMatches(query, 10),
    getGrowthMomentum(query),
  ]);

  return {
    points: points.status === "fulfilled" ? points.value : [],
    subreddits: subreddits.status === "fulfilled" ? subreddits.value : {},
    topMatches: topMatches.status === "fulfilled" ? topMatches.value : [],
    growthData:
      growthData.status === "fulfilled"
        ? growthData.value
        : { weekly: [], monthly: [] },
  };
}

export default async function ResultsPage({
  searchParams,
}: {
  searchParams: Promise<SearchParamsInput>;
}) {
  const params = await searchParams;
  const query = firstParam(params.q).trim() || "micro saas ideas";

  const { points, subreddits, topMatches, growthData } = await fetchAnalytics(query);

  return (
    <main className={styles.page}>
      <ResultsWorkspace
        query={query}
        points={points}
        subreddits={subreddits}
        topMatches={topMatches}
        growthData={growthData}
      />
    </main>
  );
}
