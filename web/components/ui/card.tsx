import * as React from "react";
import { cn } from "@/lib/utils";

const CARD_VARIANTS = {
  default: "border border-border/60 bg-card shadow-[0_2px_20px_-4px_rgb(var(--glass-border)/0.12)]",
  elevated:
    "border border-border/50 bg-gradient-to-b from-card to-card/70 shadow-[0_20px_50px_-20px_rgb(var(--glass-border)/0.35),0_2px_8px_-2px_rgb(var(--glass-border)/0.12)]",
  tinted:
    "border border-primary/20 bg-gradient-to-br from-primary/[0.09] via-card to-card shadow-[0_20px_50px_-24px_rgba(15,122,130,0.5)]",
  dark: "border border-white/10 bg-gradient-to-b from-foreground to-foreground/90 text-background shadow-[0_20px_50px_-20px_rgb(var(--glass-border)/0.5)]",
} as const;

interface CardProps extends React.ComponentProps<"div"> {
  variant?: keyof typeof CARD_VARIANTS;
  interactive?: boolean;
}

export function Card({ className, variant = "default", interactive = false, ...props }: CardProps) {
  return (
    <div
      className={cn(
        "relative rounded-2xl transition-[transform,box-shadow,border-color] duration-300 ease-out",
        CARD_VARIANTS[variant],
        interactive &&
          "hover:-translate-y-1 hover:border-primary/30 hover:shadow-[0_28px_60px_-20px_rgb(var(--glass-border)/0.4)]",
        className
      )}
      {...props}
    />
  );
}

/**
 * Page/section heading. No eyebrow/kicker line above it -- the heading
 * carries its own weight; `accent` colors the lead word instead so
 * wayfinding doesn't cost a separate label row.
 */
export function SectionHeading({
  accent,
  title,
  description,
  className,
  align = "left",
}: {
  accent?: string;
  title: string;
  description?: React.ReactNode;
  className?: string;
  align?: "left" | "center";
}) {
  return (
    <div className={cn("max-w-2xl", align === "center" && "mx-auto text-center", className)}>
      <h2 className="font-display text-3xl font-semibold leading-[1.08] tracking-tight text-foreground sm:text-4xl">
        {accent && <span className="text-primary">{accent} </span>}
        {title}
      </h2>
      {description && (
        <p className="mt-4 text-sm leading-relaxed text-muted-foreground sm:text-base">{description}</p>
      )}
    </div>
  );
}

const STATUS_STYLES: Record<string, string> = {
  answered: "bg-primary/12 text-primary",
  partial: "bg-amber-500/12 text-amber-600 dark:text-amber-400",
  open: "bg-muted text-muted-foreground",
};

const STATUS_LABEL: Record<string, string> = {
  answered: "Answered",
  partial: "Partial",
  open: "Open",
};

export function StatusPill({ status, className }: { status: string; className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-[11px] font-medium",
        STATUS_STYLES[status] ?? STATUS_STYLES.open,
        className
      )}
    >
      {STATUS_LABEL[status] ?? status}
    </span>
  );
}
