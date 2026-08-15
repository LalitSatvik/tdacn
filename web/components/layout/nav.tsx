"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "motion/react";
import { cn } from "@/lib/utils";
import { ThemeToggle } from "@/components/theme/theme-toggle";

const LINKS = [
  { href: "/", label: "Overview" },
  { href: "/explorer", label: "Explorer" },
  { href: "/segmentation", label: "Segmentation" },
  { href: "/findings", label: "Findings" },
  { href: "/architecture", label: "Architecture" },
];

export function Nav() {
  const pathname = usePathname();

  return (
    <motion.header
      initial={{ y: -24, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      className="fixed inset-x-0 top-4 z-50 flex justify-center px-4"
    >
      <nav
        className="flex max-w-full items-center gap-1 overflow-x-auto rounded-full
          border border-border/60 bg-card/80 px-2 py-2 shadow-[0_8px_30px_rgba(22,22,15,0.08)]
          backdrop-blur-md [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
      >
        <Link
          href="/"
          className="font-display shrink-0 px-3 text-sm font-semibold tracking-tight text-foreground"
        >
          TDACN
        </Link>
        <div className="mx-1 h-4 w-px shrink-0 bg-border" />
        {LINKS.map((link) => {
          const active =
            link.href === "/"
              ? pathname === "/"
              : pathname?.startsWith(link.href);
          return (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                "relative shrink-0 rounded-full px-3.5 py-1.5 text-sm font-medium transition-colors",
                active
                  ? "text-primary-foreground"
                  : "text-foreground/70 hover:text-foreground"
              )}
            >
              {active && (
                <motion.span
                  layoutId="nav-active-pill"
                  transition={{ type: "spring", stiffness: 420, damping: 34 }}
                  className="absolute inset-0 rounded-full bg-primary"
                />
              )}
              <span className="relative z-10">{link.label}</span>
            </Link>
          );
        })}
        <div className="mx-1 h-4 w-px shrink-0 bg-border" />
        <ThemeToggle />
      </nav>
    </motion.header>
  );
}
