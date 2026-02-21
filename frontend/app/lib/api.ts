/**
 * Backend API base URL. Set NEXT_PUBLIC_API_URL in .env.local (e.g. http://localhost:8000).
 */
export function getApiBase(): string {
  if (typeof window !== "undefined") {
    return (process.env.NEXT_PUBLIC_API_URL ?? "").trim() || "http://localhost:8000";
  }
  return process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
}

export type AgentAction = "flesh_out_idea" | "refine_idea" | "rank_idea";

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

export async function runAgent(
  action: AgentAction,
  ideaText: string
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
      retrieval: { matches: [] },
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error((err as { detail?: string }).detail ?? "Agent request failed");
  }
  return res.json() as Promise<AgentResponse>;
}
