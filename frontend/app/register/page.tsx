import Link from "next/link";
import GoogleAuthLink from "../components/GoogleAuthLink";
import styles from "../redditdemand.module.css";

export default function RegisterPage() {
  return (
    <main className={styles.authPage}>
      <section className={styles.authShell}>
        <div className={styles.registerLayout}>
          <div className={styles.registerPanel}>
            <h1 className={styles.authHeading}>Create your account</h1>
            <p className={styles.authSub}>
              Register with email to save searches and unlock full feature access.
            </p>

            <form action="/home" className={styles.authForm}>
              <input
                className={styles.authInput}
                name="email"
                type="email"
                placeholder="Email"
                aria-label="Email"
              />
              <input
                className={styles.authInput}
                name="password"
                type="password"
                placeholder="Create password"
                aria-label="Create password"
              />
              <button type="submit" className={styles.primaryButton}>
                Register with Email
              </button>
            </form>

            <p className={styles.authDivider}>or</p>
            <GoogleAuthLink href="/home" label="Register with Google" />

            <Link href="/home?skipped=1" className={styles.skipLink}>
              Skip profile creation
            </Link>

            <p className={`${styles.authSub} ${styles.authCenterText}`} style={{ marginTop: "0.9rem" }}>
              Already have an account?{" "}
              <Link href="/signin" className={styles.textLink}>
                Sign in
              </Link>
            </p>
          </div>

          <aside className={styles.overviewPanel}>
            <h2>What Remand gives you</h2>
            <p>
              Turn one search into a full market report: buyer readiness, momentum, saturation,
              top feedback, and the people already discussing your idea.
            </p>
            <ul className={styles.overviewList}>
              <li>Buyer Readiness Score with weighted demand signals.</li>
              <li>Interactive Growth Momentum chart with live hover details and time filter.</li>
              <li>Market Saturation Curve: need/problem mentions vs existing-tool mentions.</li>
              <li>Best Feedback: top relevant comments with direct Reddit links.</li>
              <li>People by subreddit with one-click username ZIP export.</li>
              <li>Explore with AI to brainstorm and validate next moves.</li>
            </ul>
          </aside>
        </div>
      </section>
    </main>
  );
}
