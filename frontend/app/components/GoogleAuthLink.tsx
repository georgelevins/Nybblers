import Link from "next/link";
import styles from "../redditdemand.module.css";

type GoogleAuthLinkProps = {
  href: string;
  label: string;
};

export default function GoogleAuthLink({ href, label }: GoogleAuthLinkProps) {
  return (
    <Link href={href} className={styles.googleButton}>
      <span className={styles.googleIcon} aria-hidden>
        <svg viewBox="0 0 24 24" width="16" height="16">
          <path
            fill="#EA4335"
            d="M12 10.2v3.9h5.5c-.2 1.3-1.6 3.9-5.5 3.9-3.3 0-6-2.7-6-6s2.7-6 6-6c1.9 0 3.1.8 3.8 1.5l2.6-2.5C16.8 3.3 14.7 2.4 12 2.4 6.8 2.4 2.7 6.5 2.7 11.7s4.1 9.3 9.3 9.3c5.4 0 9-3.8 9-9.1 0-.6-.1-1.1-.2-1.7H12z"
          />
        </svg>
      </span>
      <span className={styles.googleLabel}>{label}</span>
    </Link>
  );
}
