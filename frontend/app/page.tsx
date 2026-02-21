import Link from "next/link";
import styles from "./landing.module.css";

export default function Home() {
  return (
    <main className={styles.page}>
      <section className={styles.hero}>
        <h1 className={styles.title}>
          <span>Remand</span>
          <span className={styles.subtitle}>Where Ideas Meet Discussion</span>
        </h1>

        <p className={styles.supporting}>
          Turn Reddit buzz into clear demand signals. Search, validate momentum, and brainstorm next
          moves with our embedded AI agent.
        </p>

        <div className={styles.actions}>
          <Link href="/register" className={styles.primaryButton}>
            Register
          </Link>
          <Link href="/signin" className={styles.secondaryButton}>
            Sign In
          </Link>
          <Link href="/home" className={styles.exploreButton}>
            Explore Product
          </Link>
        </div>
      </section>

      <section className={styles.previewGrid}>
        <article className={styles.card}>
          <div className={styles.cardHeader}>
            <h2 className={styles.cardTitle}>Growth Momentum Preview</h2>
            <span className={styles.cardBadge}>example</span>
          </div>

          <div className={styles.chartWrap}>
            <svg className={styles.chart} viewBox="0 0 560 220" role="img" aria-label="Growth momentum example chart">
              <defs>
                <linearGradient id="momentumFill" x1="0" x2="0" y1="0" y2="1">
                  <stop offset="0%" stopColor="#ff9f62" stopOpacity="0.44" />
                  <stop offset="100%" stopColor="#ff9f62" stopOpacity="0.06" />
                </linearGradient>
              </defs>

              <line x1="44" y1="30" x2="44" y2="188" stroke="#efcfb8" strokeWidth="1" />
              <line x1="44" y1="188" x2="536" y2="188" stroke="#efcfb8" strokeWidth="1" />

              <path
                d="M44 170 L95 164 L146 156 L197 144 L248 130 L299 118 L350 102 L401 84 L452 66 L503 52 L536 42 L536 188 L44 188 Z"
                fill="url(#momentumFill)"
              />
              <path
                d="M44 170 L95 164 L146 156 L197 144 L248 130 L299 118 L350 102 L401 84 L452 66 L503 52 L536 42"
                fill="none"
                stroke="#e35900"
                strokeWidth="4"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </div>

          <div className={styles.statRow}>
            <div className={styles.statChip}>
              <span>Growth Rate</span>
              <strong>+62%</strong>
            </div>
            <div className={styles.statChip}>
              <span>Weekly Mentions</span>
              <strong>118</strong>
            </div>
            <div className={styles.statChip}>
              <span>Momentum</span>
              <strong>Rising</strong>
            </div>
          </div>
        </article>

        <article className={styles.card}>
          <div className={styles.cardHeader}>
            <h2 className={styles.cardTitle}>Embedded AI Agent</h2>
            <span className={styles.cardBadge}>always on</span>
          </div>

          <p className={styles.aiText}>
            The AI agent powers your search and helps brainstorm positioning, replies, and feature
            ideas from the exact conversations your users are already having.
          </p>

          <ul className={styles.aiList}>
            <li>Finds demand signals behind messy discussion threads</li>
            <li>Summarizes user pain points into actionable themes</li>
            <li>Suggests reply angles and product opportunities</li>
          </ul>

          <p className={styles.aiFootnote}>From buzz to decisions, in one workflow.</p>
        </article>
      </section>
    </main>
  );
}
