import ResultsWorkspace from "../components/results/ResultsWorkspace";
import styles from "../redditdemand.module.css";
import {
  getAllAnalytics,
  type TimePoint,
  type TopMatch,
  type GrowthData,
} from "../lib/api";

type SearchParamsInput = Record<string, string | string[] | undefined>;

function firstParam(value: string | string[] | undefined): string {
  if (Array.isArray(value)) return value[0] ?? "";
  return value ?? "";
}

export default async function ResultsPage({
  searchParams,
}: {
  searchParams: Promise<SearchParamsInput>;
}) {
  const params = await searchParams;
  const query = firstParam(params.q).trim() || "micro saas ideas";

  let points: TimePoint[] = [];
  let subreddits: Record<string, string[]> = {};
  let topMatches: TopMatch[] = [];
  let growthData: GrowthData = { weekly: [], monthly: [] };

  try {
    const analytics = await getAllAnalytics(query, 10);
    points = analytics.mentions.points;
    subreddits = analytics.subreddits.subreddits;
    topMatches = analytics.top_matches.matches;
    growthData = analytics.growth;
  } catch {
    // Partial failures are handled by showing empty states in the workspace
  }

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
