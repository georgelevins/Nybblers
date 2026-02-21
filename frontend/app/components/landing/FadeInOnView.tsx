"use client";

import { useEffect, useRef, useState } from "react";

export type FadeInOnViewProps = {
  children: React.ReactNode;
  className?: string;
  delayMs?: number;
};

export default function FadeInOnView({
  children,
  className = "",
  delayMs = 0,
}: FadeInOnViewProps) {
  const ref = useRef<HTMLDivElement | null>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setVisible(true);
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.15 },
    );

    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  return (
    <div
      ref={ref}
      className={className}
      style={{
        transitionDelay: `${delayMs}ms`,
        opacity: visible ? 1 : 0,
        transition: "opacity 0.8s ease",
      }}
    >
      {children}
    </div>
  );
}
