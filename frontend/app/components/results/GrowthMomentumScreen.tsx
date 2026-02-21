"use client";

import { useMemo, useState } from "react";
import LineChart from "./LineChart";
import styles from "@/app/redditdemand.module.css";
import {
  MONTHLY_LAUNCH_EVENTS,
  MONTHLY_TOPIC_MENTIONS,
  WEEKLY_LAUNCH_EVENTS,
  WEEKLY_TOPIC_MENTIONS,
  getGrowthRate,
  type LaunchEvent,
  type TimePoint,
} from "@/app/lib/resultsVisualData";

type Mode = "weekly" | "monthly";

type GrowthMomentumScreenProps = {
  query: string;
};

function toMarkers(points: TimePoint[], events: LaunchEvent[]) {
  return events
    .map((event) => {
      const index = points.findIndex((point) => point.date >= event.date);
      if (index < 0) return null;
      return {
        index,
        label: event.label,
        color: "#d04f00",
      };
    })
    .filter((marker): marker is { index: number; label: string; color: string } => marker !== null);
}

export default function GrowthMomentumScreen({ query }: GrowthMomentumScreenProps) {
  const [mode, setMode] = useState<Mode>("monthly");

  const points = mode === "monthly" ? MONTHLY_TOPIC_MENTIONS : WEEKLY_TOPIC_MENTIONS;
  const launchEvents = mode === "monthly" ? MONTHLY_LAUNCH_EVENTS : WEEKLY_LAUNCH_EVENTS;

  const growth = useMemo(() => getGrowthRate(points), [points]);
  const markers = useMemo(() => toMarkers(points, launchEvents), [points, launchEvents]);

  const first = points[0]?.value ?? 0;
  const latest = points[points.length - 1]?.value ?? 0;
  const delta = latest - first;

  return (
    <section className={styles.visualCard}>
      <div className={styles.visualHeader}>
        <h2 className={styles.visualTitle}>Growth Over Time (Momentum &gt; Raw Numbers)</h2>
        <p className={styles.visualSub}>
          Trend velocity for <strong>{query}</strong> with launch milestones overlaid.
        </p>
      </div>

      <div className={styles.segmentedControl}>
        <button
          type="button"
          className={`${styles.segmentButton} ${mode === "weekly" ? styles.segmentActive : ""}`.trim()}
          onClick={() => setMode("weekly")}
        >
          Weekly Mentions
        </button>
        <button
          type="button"
          className={`${styles.segmentButton} ${mode === "monthly" ? styles.segmentActive : ""}`.trim()}
          onClick={() => setMode("monthly")}
        >
          Monthly Mentions
        </button>
      </div>

      <div className={styles.metricsRow}>
        <div className={styles.metricPill}>
          <span>Growth Rate</span>
          <strong>{growth >= 0 ? "+" : ""}{growth.toFixed(1)}%</strong>
        </div>
        <div className={styles.metricPill}>
          <span>First vs Latest</span>
          <strong>
            {first} → {latest}
          </strong>
        </div>
        <div className={styles.metricPill}>
          <span>Net Momentum</span>
          <strong>{delta >= 0 ? "+" : ""}{delta}</strong>
        </div>
      </div>

      <div className={styles.chartShell}>
        <LineChart
          points={points}
          markers={markers}
          xLabel={mode === "weekly" ? "Time (weeks)" : "Time (months)"}
          yLabel="Mentions"
        />
      </div>

      <div className={styles.launchList}>
        {launchEvents.map((event) => (
          <span key={`${event.date}-${event.label}`} className={styles.launchTag}>
            {event.label} · {event.date}
          </span>
        ))}
      </div>
    </section>
  );
}
