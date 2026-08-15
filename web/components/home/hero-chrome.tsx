"use client";

import { motion } from "motion/react";
import { ChevronDown } from "lucide-react";

/** The topology.vc-style hero furniture: a bottom info bar with a corner
 * mark and a bouncing scroll cue, laid over the live chrome background. */
export function HeroChrome() {
  return (
    <div className="relative z-10 flex items-center justify-between border-t border-white/10 px-6 py-5 text-white/60">
      <span className="font-mono text-[11px] tracking-[0.18em]">
        TDACN — TEMPORAL DRIFT, Q1–Q3
      </span>
      <motion.a
        href="#metrics"
        className="flex items-center gap-1.5 font-mono text-[11px] tracking-[0.18em] transition-colors hover:text-white"
        animate={{ y: [0, 5, 0] }}
        transition={{ duration: 1.8, repeat: Infinity, ease: "easeInOut" }}
      >
        EXPLORE
        <ChevronDown className="h-3.5 w-3.5" />
      </motion.a>
    </div>
  );
}
