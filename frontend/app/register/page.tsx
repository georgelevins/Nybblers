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
              Find high-intent Reddit threads, validate your startup demand, and focus on
              opportunities that still attract ongoing comments.
            </p>
            <ul className={styles.overviewList}>
              <li>Demand View sorted by semantic relevance.</li>
              <li>Opportunity View sorted by heat score and activity.</li>
              <li>Google-ranking signals to find evergreen threads.</li>
              <li>Alerts for new matching posts.</li>
            </ul>
          </aside>
        </div>
      </section>
    </main>
  );
}
