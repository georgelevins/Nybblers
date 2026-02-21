export type ResultsView = "demand" | "opportunity";

export type Thread = {
  title: string;
  subreddit: string;
  age: string;
  comments: number;
  heat: number;
  ranksOnGoogle: boolean;
  active: boolean;
  snippet: string;
  summary: string;
  url: string;
};

export const EXAMPLE_SEARCHES = [
  "invoicing software for freelancers",
  "anxiety about money",
  "managing remote teams is hard",
];

export const THREADS: Thread[] = [
  {
    title: "Best invoicing software for freelancers? FreshBooks seems overpriced",
    subreddit: "r/freelance",
    age: "3 years ago",
    comments: 247,
    heat: 88,
    ranksOnGoogle: true,
    active: false,
    snippet:
      "\"I've been using Wave for 2 years and it's free, but I wish it had automatic reminders for late invoices.\"",
    summary:
      "Freelancers comparing options and asking for better reminders without high monthly pricing.",
    url: "https://www.reddit.com/r/freelance/",
  },
  {
    title: "How do you handle invoicing as a freelance developer?",
    subreddit: "r/webdev",
    age: "2 years ago",
    comments: 183,
    heat: 76,
    ranksOnGoogle: true,
    active: false,
    snippet:
      "\"I tried 6 tools and they all feel built for agencies, not solo developers trying to get paid quickly.\"",
    summary:
      "Solo developers want a lightweight tool that sends clean invoices and tracks payments.",
    url: "https://www.reddit.com/r/webdev/",
  },
  {
    title: "What do you actually use for invoicing? [Poll results inside]",
    subreddit: "r/freelance",
    age: "8 months ago",
    comments: 94,
    heat: 94,
    ranksOnGoogle: false,
    active: true,
    snippet:
      "\"The spreadsheet answers tell me the market still has gaps for simple workflows and follow-ups.\"",
    summary:
      "Poll thread with active comments, clear dissatisfaction, and many DIY workarounds.",
    url: "https://www.reddit.com/r/freelance/",
  },
  {
    title: "Honest review of every invoicing tool I've tried",
    subreddit: "r/entrepreneur",
    age: "1 year ago",
    comments: 312,
    heat: 71,
    ranksOnGoogle: true,
    active: false,
    snippet:
      "\"Most tools assume you have a bookkeeper. I just need to look professional and avoid chasing payments.\"",
    summary:
      "One-person founders discussing why current products are too heavy for solo operators.",
    url: "https://www.reddit.com/r/entrepreneur/",
  },
  {
    title: "Is there an app that tracks time and sends invoice follow-ups automatically?",
    subreddit: "r/digitalnomad",
    age: "5 months ago",
    comments: 56,
    heat: 99,
    ranksOnGoogle: false,
    active: true,
    snippet:
      "\"Time trackers are weak at invoicing, and invoicing apps are weak at time tracking. Why is this split still here?\"",
    summary:
      "High-heat, still-active thread highlighting a persistent workflow gap for remote workers.",
    url: "https://www.reddit.com/r/digitalnomad/",
  },
];

export const DEFAULT_ALERTS = [
  {
    query: "invoicing software for freelancers",
    detail: "Daily digest · r/freelance, r/entrepreneur",
  },
  {
    query: "need help tracking expenses",
    detail: "Instant · r/personalfinance",
  },
];

export function getThreads(view: ResultsView): Thread[] {
  if (view === "opportunity") {
    return [...THREADS].sort((a, b) => b.heat - a.heat);
  }

  return THREADS;
}
