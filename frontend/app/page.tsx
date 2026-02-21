import Image from "next/image";
import Link from "next/link";
import LandingGrowthChart from "./components/landing/LandingGrowthChart";
import FadeInOnView from "./components/landing/FadeInOnView";
import styles from "./landing.module.css";
import landingImage from "./rocket.png";
import landingImage2 from "./ai.png";

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
            <FadeInOnView>
              <Image
                src={landingImage}
                alt="Rocket taking off illustration"
                className={styles.imageAsset}
                priority
                width={960}
                height={540}
              />
            </FadeInOnView>
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
            <LandingGrowthChart />

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

          <div className={styles.aiLayout}>
            <div className={styles.aiVisualFrame}>
              <FadeInOnView>
                <Image
                  src={landingImage2}
                  alt="AI agent illustration"
                  className={styles.aiVisual}
                  width={960}
                  height={540}
                />
              </FadeInOnView>
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
        </div>
      </section>
    </main>
  );
}
