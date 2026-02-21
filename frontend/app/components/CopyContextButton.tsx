"use client";

import { useState } from "react";

type CopyContextButtonProps = {
  title: string;
  summary: string;
  className?: string;
};

export default function CopyContextButton({
  title,
  summary,
  className,
}: CopyContextButtonProps) {
  const [label, setLabel] = useState("Copy thread context");

  async function handleCopy() {
    const content = `Thread: "${title}"\nContext: ${summary}`;

    try {
      await navigator.clipboard.writeText(content);
      setLabel("Copied");
      setTimeout(() => setLabel("Copy thread context"), 1400);
    } catch {
      setLabel("Copy failed");
      setTimeout(() => setLabel("Copy thread context"), 1400);
    }
  }

  return (
    <button type="button" className={className} onClick={handleCopy}>
      {label}
    </button>
  );
}
