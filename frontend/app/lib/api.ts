/**
 * Backend API client for Remand.
 * Base URL is read from NEXT_PUBLIC_API_URL (set in .env.local).
 */

export function getApiBase(): string {
  if (typeof window !== "undefined") {
    return (process.env.NEXT_PUBLIC_API_URL ?? "").trim() || "http://localhost:8000";
  }
  return process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
}

// ---- Shared types ----

export type TimePoint = {
  date: string;
  label: string;
  value: number;
};

export type TopMatch = {
  id: string;
  subreddit: string;
  author: string | null;
  body: string;
  score: number;
  url: string | null;
  similarity: number;
  kind: "post" | "comment";
};

export type GrowthData = {
  weekly: TimePoint[];
  monthly: TimePoint[];
};

// ---- Agent types ----

export type AgentAction = "enhance_idea";

export type IdeaCard = {
  problem?: string | null;
  customer?: string | null;
  when?: string | null;
  current_workaround?: string | null;
  solution?: string | null;
  differentiator?: string | null;
  monetization?: string | null;
  distribution?: string | null;
};

export type EvidenceItem = {
  match_id: string;
  quote: string;
  why_it_matters: string;
};

export type AgentResponse = {
  action: string;
  idea_card: IdeaCard;
  outputs: Record<string, unknown>;
  assumptions: string[];
  risks: string[];
  next_steps: string[];
  evidence: EvidenceItem[];
};

export type RetrievalMatch = {
  id: string;
  title: string;
  text: string;
  source: "reddit" | "internal" | "web" | "other";
  metadata?: Record<string, unknown>;
};

// ---- Search API ----

export type SearchResultItem = {
  id: string;
  title: string;
  subreddit: string;
  created_utc: string;
  num_comments: number;
  activity_ratio: number;
  last_comment_utc: string | null;
  similarity_score: number;
  snippet: string;
};

export async function searchPosts(
  query: string,
  limit = 20,
): Promise<SearchResultItem[]> {
  const base = getApiBase();
  const res = await fetch(`${base}/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query: query.trim(), limit }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error((err as { detail?: string }).detail ?? "Search failed");
  }
  const data = await res.json() as { results: SearchResultItem[] };
  return data.results;
}

// ---- Analytics API ----

export async function getMentionsTrend(query: string): Promise<TimePoint[]> {
  const base = getApiBase();
  const params = new URLSearchParams({ q: query.trim() });
  const res = await fetch(`${base}/search/mentions-over-time?${params}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error((err as { detail?: string }).detail ?? "Mentions request failed");
  }
  const data = await res.json() as { points: TimePoint[] };
  return data.points;
}

export async function getUsersBySubreddit(
  query: string,
): Promise<Record<string, string[]>> {
  const base = getApiBase();
  const params = new URLSearchParams({ q: query.trim() });
  const res = await fetch(`${base}/search/users-by-subreddit?${params}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error((err as { detail?: string }).detail ?? "Users request failed");
  }
  const data = await res.json() as { subreddits: Record<string, string[]> };
  return data.subreddits;
}

export async function getTopMatches(
  query: string,
  limit = 10,
): Promise<TopMatch[]> {
  const base = getApiBase();
  const params = new URLSearchParams({ q: query.trim(), limit: String(limit) });
  const res = await fetch(`${base}/search/top-matches?${params}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error((err as { detail?: string }).detail ?? "Top matches request failed");
  }
  const data = await res.json() as { matches: TopMatch[] };
  return data.matches;
}

export async function getGrowthMomentum(query: string): Promise<GrowthData> {
  const base = getApiBase();
  const params = new URLSearchParams({ q: query.trim() });
  const res = await fetch(`${base}/search/growth-momentum?${params}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error((err as { detail?: string }).detail ?? "Growth request failed");
  }
  return res.json() as Promise<GrowthData>;
}

// ---- Agent API ----

export async function runAgent(
  action: AgentAction,
  ideaText: string,
  retrievalMatches?: RetrievalMatch[],
): Promise<AgentResponse> {
  const base = getApiBase();
  const res = await fetch(`${base}/agent/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      action,
      idea_text: ideaText.trim(),
      constraints: {},
      context: {},
      retrieval: {
        matches: retrievalMatches ?? [],
      },
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error((err as { detail?: string }).detail ?? "Agent request failed");
  }
  return res.json() as Promise<AgentResponse>;
}

/** Convert TopMatch items into RetrievalMatch format for the agent. */
export function matchesToRetrieval(matches: TopMatch[]): RetrievalMatch[] {
  return matches.map((m) => ({
    id: m.id,
    title: m.kind === "post" ? m.body.slice(0, 120) : `Comment by ${m.author ?? "unknown"}`,
    text: m.body,
    source: "reddit" as const,
    metadata: {
      subreddit: m.subreddit,
      score: m.score,
      kind: m.kind,
      url: m.url ?? undefined,
    },
  }));
}
