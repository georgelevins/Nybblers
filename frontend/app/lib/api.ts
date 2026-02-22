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

// ---- Active threads (engagement campaign) ----

export type ActiveThread = {
  id: string;
  title: string;
  subreddit: string;
  url: string | null;
  last_comment_utc: string | null;
  score: number;
  num_comments: number;
  recent_comments: number;
  velocity: number;
  estimated_impressions: number;
};

export type ActiveThreadsResponse = {
  active_count: number;
  total_estimated_impressions: number;
  window_hours: number;
  threads: ActiveThread[];
};

export async function getThreadsActivity(
  postIds: string[],
  windowHours = 24,
): Promise<ActiveThreadsResponse | null> {
  if (!postIds.length) return null;
  const base = getApiBase();
  const params = new URLSearchParams({
    ids: postIds.join(","),
    window_hours: String(windowHours),
  });
  const res = await fetch(`${base}/threads/activity?${params}`);
  if (res.status === 503) return null;
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error((err as { detail?: string }).detail ?? "Thread activity request failed");
  }
  return res.json() as Promise<ActiveThreadsResponse>;
}

export async function getActiveThreads(
  query: string,
  windowHours = 24,
  minComments = 3,
  limit = 20,
): Promise<ActiveThreadsResponse | null> {
  const base = getApiBase();
  const params = new URLSearchParams({
    q: query.trim(),
    window_hours: String(windowHours),
    min_comments: String(minComments),
    limit: String(limit),
  });
  const res = await fetch(`${base}/search/active-threads?${params}`);
  if (res.status === 503) return null; // DB not available — caller shows empty state
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error((err as { detail?: string }).detail ?? "Active threads request failed");
  }
  return res.json() as Promise<ActiveThreadsResponse>;
}

export async function draftReply(
  threadTitle: string,
  threadSubreddit: string,
  query: string,
): Promise<string> {
  // From the browser, use same-origin proxy to avoid CORS/network errors to backend
  const url =
    typeof window !== "undefined"
      ? "/api/engage/draft-reply"
      : `${getApiBase()}/engage/draft-reply`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ thread_title: threadTitle, thread_subreddit: threadSubreddit, query }),
  });
  const raw = await res.text();
  let data: { draft?: string; detail?: string };
  try {
    data = raw ? (JSON.parse(raw) as { draft?: string; detail?: string }) : {};
  } catch {
    throw new Error(res.ok ? "Invalid response from server" : (raw?.slice(0, 200) || res.statusText));
  }
  if (!res.ok) {
    throw new Error(data.detail ?? res.statusText ?? "Draft failed");
  }
  if (typeof data.draft !== "string") {
    throw new Error("Invalid response: missing draft");
  }
  return data.draft;
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
