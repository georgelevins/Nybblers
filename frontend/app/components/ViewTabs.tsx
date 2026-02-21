import Link from "next/link";

type TabKey = "demand" | "opportunity" | "alerts";

type ViewTabsProps = {
  active: TabKey;
  query: string;
  className?: string;
  tabClassName?: string;
  activeClassName?: string;
};

function withQuery(pathname: string, query: string, extra?: Record<string, string>) {
  const params = new URLSearchParams();
  if (query) params.set("q", query);
  if (extra) {
    for (const [key, value] of Object.entries(extra)) {
      params.set(key, value);
    }
  }
  const qs = params.toString();
  return qs ? `${pathname}?${qs}` : pathname;
}

export default function ViewTabs({
  active,
  query,
  className,
  tabClassName,
  activeClassName,
}: ViewTabsProps) {
  const links: Array<{ key: TabKey; label: string; href: string }> = [
    {
      key: "demand",
      label: "Demand View",
      href: withQuery("/results", query, { view: "demand" }),
    },
    {
      key: "opportunity",
      label: "Opportunity View",
      href: withQuery("/results", query, { view: "opportunity" }),
    },
    {
      key: "alerts",
      label: "Alerts",
      href: withQuery("/alerts", query),
    },
  ];

  return (
    <div className={className}>
      {links.map((tab) => (
        <Link
          key={tab.key}
          className={`${tabClassName ?? ""} ${active === tab.key ? activeClassName ?? "" : ""}`.trim()}
          href={tab.href}
        >
          {tab.label}
        </Link>
      ))}
    </div>
  );
}
