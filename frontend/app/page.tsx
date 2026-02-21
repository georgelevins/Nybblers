import Image from "next/image";
import Link from "next/link";
import styles from "./landing.module.css";
import landingImage from "./landingimage.avif";
import landingImage2 from "./landingimage2.avif";

export default function Home() {
  return (
    <main className={styles.page}>
      <section className={styles.hero}>
        <div className={styles.heroGlow} />
        <div className={styles.heroInner}>
          <h1 className={styles.brandWord}>Remand</h1>
          <p className={styles.tagline}>Where Ideas Meet Discussion</p>

          <p className={styles.heroSupport}>
            Track market buzz, measure demand momentum, and discover conversations where your
            next customers are already talking.
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
        </div>
      </section>

      <section className={styles.imageSection}>
        <div className={styles.sectionInner}>
          <h2 className={styles.sectionTitle}>From Discussion to Direction</h2>
          <p className={styles.sectionText}>
            Remand helps founders and growth teams turn noisy threads into clear next actions.
          </p>
          <div className={styles.imageFrame}>
            <Image
              src={landingImage}
              alt="Developer discussion and planning illustration"
              className={styles.imageAsset}
              priority
            />
          </div>
        </div>
      </section>

      <section className={styles.graphSection}>
        <div className={styles.sectionInner}>
          <h2 className={styles.sectionTitle}>Growth Momentum Preview</h2>
          <p className={styles.sectionText}>
            See how often a topic is discussed over time and spot when momentum starts to accelerate.
          </p>

          <div className={styles.chartCard}>
            <svg className={styles.chart} viewBox="0 0 680 280" role="img" aria-label="Growth momentum sample chart">
              <defs>
                <linearGradient id="momentumFill" x1="0" x2="0" y1="0" y2="1">
                  <stop offset="0%" stopColor="#ff9f62" stopOpacity="0.4" />
                  <stop offset="100%" stopColor="#ff9f62" stopOpacity="0.07" />
                </linearGradient>
              </defs>

              <line x1="60" y1="40" x2="60" y2="230" stroke="#efcfb8" strokeWidth="1" />
              <line x1="60" y1="230" x2="640" y2="230" stroke="#efcfb8" strokeWidth="1" />
              <line x1="60" y1="180" x2="640" y2="180" stroke="#f4dcc9" strokeWidth="1" />
              <line x1="60" y1="130" x2="640" y2="130" stroke="#f4dcc9" strokeWidth="1" />
              <line x1="60" y1="80" x2="640" y2="80" stroke="#f4dcc9" strokeWidth="1" />

              <path
                d="M60 212 L118 205 L176 196 L234 184 L292 169 L350 154 L408 134 L466 112 L524 88 L582 67 L640 52 L640 230 L60 230 Z"
                fill="url(#momentumFill)"
              />
              <path
                d="M60 212 L118 205 L176 196 L234 184 L292 169 L350 154 L408 134 L466 112 L524 88 L582 67 L640 52"
                fill="none"
                stroke="#e35900"
                strokeWidth="4"
                strokeLinecap="round"
                strokeLinejoin="round"
              />

              <text x="72" y="252" fill="#9a5d3a" fontSize="12">Jan</text>
              <text x="230" y="252" fill="#9a5d3a" fontSize="12">Apr</text>
              <text x="390" y="252" fill="#9a5d3a" fontSize="12">Jul</text>
              <text x="548" y="252" fill="#9a5d3a" fontSize="12">Oct</text>
            </svg>

            <div className={styles.statRow}>
              <div className={styles.statChip}>
                <span>Growth Rate</span>
                <strong>+62%</strong>
              </div>
              <div className={styles.statChip}>
                <span>Current Mentions</span>
                <strong>118/week</strong>
              </div>
              <div className={styles.statChip}>
                <span>Momentum</span>
                <strong>Rising</strong>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className={styles.aiSection}>
        <div className={styles.sectionInner}>
          <h2 className={styles.sectionTitle}>Embedded AI Agent</h2>
          <p className={styles.sectionText}>
            Our agent powers your search and brainstorms with you, turning raw Reddit discussions
            into clear positioning, feature ideas, and outreach angles.
          </p>

          <div className={styles.aiVisualFrame}>
            <Image
              src={landingImage2}
              alt="Team using a strategic planning board"
              className={styles.aiVisual}
            />
          </div>

          <div className={styles.aiCard}>
            <ul className={styles.aiList}>
              <li>Finds the strongest demand signals in noisy threads</li>
              <li>Summarizes recurring pain points in seconds</li>
              <li>Suggests practical go-to-market responses</li>
            </ul>
            <p className={styles.aiFootnote}>Built to move from buzz to decisions faster.</p>
          </div>
        </div>
      </section>
    </main>
  );
}
