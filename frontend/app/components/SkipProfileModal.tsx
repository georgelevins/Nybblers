"use client";

import { useState } from "react";
import styles from "../redditdemand.module.css";

export default function SkipProfileModal() {
  const [open, setOpen] = useState(true);

  if (!open) return null;

  return (
    <div className={styles.modalOverlay} role="dialog" aria-modal="true" aria-labelledby="skip-profile-title">
      <div className={styles.modalCard}>
        <h2 id="skip-profile-title" className={styles.modalTitle}>
          Limited Access Notice
        </h2>
        <p className={styles.modalBody}>
          Without creating a profile, your searches will not be stored and you will not have access to all RedditDemand features.
        </p>
        <div className={styles.modalActions}>
          <button type="button" className={styles.primaryButton} onClick={() => setOpen(false)}>
            Continue
          </button>
        </div>
      </div>
    </div>
  );
}
