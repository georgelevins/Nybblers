import Link from "next/link";
import GoogleAuthLink from "../components/GoogleAuthLink";
import styles from "../redditdemand.module.css";

export default function SignInPage() {
  return (
    <main className={styles.authPage}>
      <section className={styles.authShell}>
        <div className={styles.welcomeCard}>
          <h1 className={styles.authHeading}>Welcome to Remand</h1>
          <p className={styles.authSub}>
            Sign in to view previous searches, track opportunities manage alerts and work with our AI agents
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
              placeholder="Password"
              aria-label="Password"
            />
            <button type="submit" className={styles.primaryButton}>
              Sign in
            </button>
          </form>

          <p className={styles.authDivider}>or</p>
          <GoogleAuthLink href="/home" label="Sign in with Google" />

          <p className={`${styles.authSub} ${styles.authCenterText}`} style={{ marginTop: "0.9rem" }}>
            New here?{" "}
            <Link href="/register" className={styles.textLink}>
              Register for the first time
            </Link>
          </p>
        </div>
      </section>
    </main>
  );
}
