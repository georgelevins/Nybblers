export type TimePoint = {
  date: string;
  label: string;
  value: number;
};

export type LaunchEvent = {
  date: string;
  label: string;
};

export type RelevantComment = {
  username: string;
  subreddit: string;
  quote: string;
  relevance: number;
  kind: "comment" | "post";
  url: string;
};

export const MONTHLY_TOPIC_MENTIONS: TimePoint[] = [
  { date: "2023-02-01", label: "Feb 23", value: 14 },
  { date: "2023-03-01", label: "Mar 23", value: 16 },
  { date: "2023-04-01", label: "Apr 23", value: 18 },
  { date: "2023-05-01", label: "May 23", value: 20 },
  { date: "2023-06-01", label: "Jun 23", value: 24 },
  { date: "2023-07-01", label: "Jul 23", value: 22 },
  { date: "2023-08-01", label: "Aug 23", value: 28 },
  { date: "2023-09-01", label: "Sep 23", value: 31 },
  { date: "2023-10-01", label: "Oct 23", value: 30 },
  { date: "2023-11-01", label: "Nov 23", value: 35 },
  { date: "2023-12-01", label: "Dec 23", value: 40 },
  { date: "2024-01-01", label: "Jan 24", value: 38 },
  { date: "2024-02-01", label: "Feb 24", value: 44 },
  { date: "2024-03-01", label: "Mar 24", value: 48 },
  { date: "2024-04-01", label: "Apr 24", value: 53 },
  { date: "2024-05-01", label: "May 24", value: 57 },
  { date: "2024-06-01", label: "Jun 24", value: 60 },
  { date: "2024-07-01", label: "Jul 24", value: 65 },
  { date: "2024-08-01", label: "Aug 24", value: 69 },
  { date: "2024-09-01", label: "Sep 24", value: 74 },
  { date: "2024-10-01", label: "Oct 24", value: 78 },
  { date: "2024-11-01", label: "Nov 24", value: 81 },
  { date: "2024-12-01", label: "Dec 24", value: 86 },
  { date: "2025-01-01", label: "Jan 25", value: 92 },
  { date: "2025-02-01", label: "Feb 25", value: 98 },
  { date: "2025-03-01", label: "Mar 25", value: 104 },
  { date: "2025-04-01", label: "Apr 25", value: 112 },
  { date: "2025-05-01", label: "May 25", value: 121 },
  { date: "2025-06-01", label: "Jun 25", value: 130 },
  { date: "2025-07-01", label: "Jul 25", value: 137 },
  { date: "2025-08-01", label: "Aug 25", value: 149 },
  { date: "2025-09-01", label: "Sep 25", value: 158 },
  { date: "2025-10-01", label: "Oct 25", value: 166 },
  { date: "2025-11-01", label: "Nov 25", value: 175 },
  { date: "2025-12-01", label: "Dec 25", value: 189 },
  { date: "2026-01-01", label: "Jan 26", value: 205 },
];

export const WEEKLY_TOPIC_MENTIONS: TimePoint[] = [
  { date: "2025-08-04", label: "Aug 04", value: 42 },
  { date: "2025-08-11", label: "Aug 11", value: 44 },
  { date: "2025-08-18", label: "Aug 18", value: 46 },
  { date: "2025-08-25", label: "Aug 25", value: 45 },
  { date: "2025-09-01", label: "Sep 01", value: 48 },
  { date: "2025-09-08", label: "Sep 08", value: 50 },
  { date: "2025-09-15", label: "Sep 15", value: 52 },
  { date: "2025-09-22", label: "Sep 22", value: 55 },
  { date: "2025-09-29", label: "Sep 29", value: 58 },
  { date: "2025-10-06", label: "Oct 06", value: 60 },
  { date: "2025-10-13", label: "Oct 13", value: 63 },
  { date: "2025-10-20", label: "Oct 20", value: 67 },
  { date: "2025-10-27", label: "Oct 27", value: 70 },
  { date: "2025-11-03", label: "Nov 03", value: 73 },
  { date: "2025-11-10", label: "Nov 10", value: 75 },
  { date: "2025-11-17", label: "Nov 17", value: 80 },
  { date: "2025-11-24", label: "Nov 24", value: 84 },
  { date: "2025-12-01", label: "Dec 01", value: 87 },
  { date: "2025-12-08", label: "Dec 08", value: 91 },
  { date: "2025-12-15", label: "Dec 15", value: 95 },
  { date: "2025-12-22", label: "Dec 22", value: 99 },
  { date: "2025-12-29", label: "Dec 29", value: 106 },
  { date: "2026-01-05", label: "Jan 05", value: 112 },
  { date: "2026-01-12", label: "Jan 12", value: 118 },
];

export const MONTHLY_LAUNCH_EVENTS: LaunchEvent[] = [
  { date: "2024-11-01", label: "Beta Release" },
  { date: "2025-06-01", label: "Public Launch" },
  { date: "2025-10-01", label: "Search Upgrade" },
];

export const WEEKLY_LAUNCH_EVENTS: LaunchEvent[] = [
  { date: "2025-09-22", label: "Beta Release" },
  { date: "2025-11-03", label: "Public Launch" },
  { date: "2025-12-15", label: "Search Upgrade" },
];

export const USERS_BY_SUBREDDIT: Record<string, string[]> = {
  "r/freelance": [
    "invoice_nina",
    "soloops_mark",
    "design_bella",
    "latefee_rob",
    "sprintpay_jules",
    "contract_lane",
    "pixelpay_chris",
    "opsforone_sam",
  ],
  "r/entrepreneur": [
    "bootstrap_amy",
    "d2c_owen",
    "mrr_tracker",
    "founder_lex",
    "startup_kai",
    "revloop_tia",
    "nightbuild_jon",
  ],
  "r/webdev": [
    "node_nomad",
    "frontend_ash",
    "async_mira",
    "deploy_daily",
    "ts_nick",
    "buildship_eli",
  ],
  "r/digitalnomad": [
    "coast_coder",
    "wifi_writer",
    "timezone_sue",
    "travelstack_ian",
    "remote_bryn",
    "nomad_rio",
  ],
  "r/smallbusiness": [
    "bookkeep_kim",
    "cashflow_cam",
    "quickquote_rae",
    "ownerops_alex",
    "ledger_lina",
  ],
};

export const SUBREDDIT_COLORS = [
  "#e35900",
  "#ff8f45",
  "#ffa965",
  "#ffc085",
  "#ffd4ad",
];

export const TOP_RELEVANT_COMMENTS: RelevantComment[] = [
  {
    username: "invoice_nina",
    subreddit: "r/freelance",
    quote:
      "I need one place where client tracking, reminders, and invoicing happen together. Right now I’m stitching three tools.",
    relevance: 98,
    kind: "comment",
    url: "https://www.reddit.com/r/freelance/comments/1abc123/example_comment_1/",
  },
  {
    username: "startup_kai",
    subreddit: "r/entrepreneur",
    quote:
      "If a tool handled follow-ups automatically, I’d pay immediately. Chasing overdue invoices kills my focus every week.",
    relevance: 97,
    kind: "comment",
    url: "https://www.reddit.com/r/entrepreneur/comments/1abc124/example_comment_2/",
  },
  {
    username: "frontend_ash",
    subreddit: "r/webdev",
    quote:
      "I want fast invoice creation directly after time tracking. Most products break that flow and I lose billable hours.",
    relevance: 95,
    kind: "comment",
    url: "https://www.reddit.com/r/webdev/comments/1abc125/example_comment_3/",
  },
  {
    username: "coast_coder",
    subreddit: "r/digitalnomad",
    quote:
      "Timezone clients are brutal for payment reminders. I need scheduling intelligence built into invoicing, not another plugin.",
    relevance: 94,
    kind: "comment",
    url: "https://www.reddit.com/r/digitalnomad/comments/1abc126/example_comment_4/",
  },
  {
    username: "bookkeep_kim",
    subreddit: "r/smallbusiness",
    quote:
      "Simple month-end reporting plus clean invoices would solve 80% of my pain. Most products feel overbuilt for a solo owner.",
    relevance: 92,
    kind: "post",
    url: "https://www.reddit.com/r/smallbusiness/comments/1abc127/example_post_5/",
  },
  {
    username: "opsforone_sam",
    subreddit: "r/freelance",
    quote:
      "The gap is context: I need invoice tools that understand service businesses, not ecommerce checkouts repackaged as billing apps.",
    relevance: 91,
    kind: "comment",
    url: "https://www.reddit.com/r/freelance/comments/1abc128/example_comment_6/",
  },
  {
    username: "d2c_owen",
    subreddit: "r/entrepreneur",
    quote:
      "I tried every mainstream invoicing app and still use spreadsheets for edge cases. That says the product category isn’t done.",
    relevance: 90,
    kind: "comment",
    url: "https://www.reddit.com/r/entrepreneur/comments/1abc129/example_comment_7/",
  },
  {
    username: "deploy_daily",
    subreddit: "r/webdev",
    quote:
      "The first app that gives me ‘create invoice from completed task’ will own this market for dev freelancers.",
    relevance: 89,
    kind: "comment",
    url: "https://www.reddit.com/r/webdev/comments/1abc130/example_comment_8/",
  },
  {
    username: "timezone_sue",
    subreddit: "r/digitalnomad",
    quote:
      "I want predictable cashflow, not accounting complexity. Give me lightweight automation and reminders that actually work.",
    relevance: 88,
    kind: "comment",
    url: "https://www.reddit.com/r/digitalnomad/comments/1abc131/example_comment_9/",
  },
  {
    username: "cashflow_cam",
    subreddit: "r/smallbusiness",
    quote:
      "The best tool would turn messy client notes into a ready invoice draft automatically. That would save me hours each week.",
    relevance: 87,
    kind: "post",
    url: "https://www.reddit.com/r/smallbusiness/comments/1abc132/example_post_10/",
  },
];

export function getGrowthRate(points: TimePoint[]): number {
  if (points.length < 2) return 0;
  const first = points[0].value;
  const last = points[points.length - 1].value;
  if (first === 0) return 0;
  return ((last - first) / first) * 100;
}
