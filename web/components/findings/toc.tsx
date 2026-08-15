"use client";

import * as React from "react";
import { motion } from "motion/react";
import { cn } from "@/lib/utils";

interface TocProps {
  sections: { letter: string; title: string }[];
}

/** Sticky section nav with scroll-spy highlighting — tracks which section
 * is in view via IntersectionObserver rather than a static list. */
export function Toc({ sections }: TocProps) {
  const [active, setActive] = React.useState(sections[0]?.letter);

  React.useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            setActive(entry.target.id.replace("section-", ""));
          }
        }
      },
      { rootMargin: "-20% 0px -70% 0px", threshold: 0 }
    );
    for (const s of sections) {
      const el = document.getElementById(`section-${s.letter}`);
      if (el) observer.observe(el);
    }
    return () => observer.disconnect();
  }, [sections]);

  return (
    <nav className="top-24 hidden shrink-0 lg:sticky lg:block lg:w-48">
      <div className="text-xs font-semibold text-foreground">Sections</div>
      <ol className="mt-3 flex flex-col gap-1">
        {sections.map((s) => {
          const isActive = active === s.letter;
          return (
            <li key={s.letter} className="relative">
              <a
                href={`#section-${s.letter}`}
                className={cn(
                  "relative flex items-start gap-2 rounded-md py-1 pl-3 text-xs transition-colors",
                  isActive ? "font-medium text-foreground" : "text-muted-foreground hover:text-foreground"
                )}
              >
                {isActive && (
                  <motion.span
                    layoutId="toc-active"
                    transition={{ type: "spring", stiffness: 420, damping: 34 }}
                    className="absolute inset-y-0 left-0 w-0.5 rounded-full bg-primary"
                  />
                )}
                <span className="font-mono">{s.letter}.</span> {s.title}
              </a>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
