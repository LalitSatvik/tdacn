import Link from "next/link";
import { getGraph, getOverview } from "@/lib/data";
import { subsampleGraph } from "@/lib/graph-utils";
import { HeroGraph } from "@/components/graph/hero-graph";
import { HeroChrome } from "@/components/home/hero-chrome";
import { KpiCard, type FormatKind } from "@/components/ui/kpi-card";
import { Card, SectionHeading } from "@/components/ui/card";
import { LiquidButton, MetalButton } from "@/components/ui/liquid-glass-button";
import { Reveal, StaggerGroup, StaggerItem } from "@/components/motion/reveal";

const FORMAT_KEYS: Record<string, FormatKind> = {
  vocab_churn: "percent",
  degree_ks: "pvalue",
  community_count: "integer",
};

export default async function OverviewPage() {
  const [overview, graphQ1] = await Promise.all([getOverview(), getGraph("Q1")]);
  const hero = subsampleGraph(graphQ1, 550);
  const [heroMetric, ...restMetrics] = overview.metrics;

  return (
    <>
      <section className="relative flex h-screen min-h-[720px] flex-col overflow-hidden">
        <HeroGraph data={hero} />
        <div className="relative z-10 flex flex-1 flex-col justify-center px-6">
          <div className="mx-auto w-full max-w-5xl">
            <h1 className="font-display max-w-3xl text-6xl font-semibold leading-[0.98] tracking-tight text-white sm:text-7xl lg:text-8xl">
              Drift is real.
              <br />
              We measured it.
            </h1>
            <p className="mt-7 max-w-xl text-base text-white/70 sm:text-lg">
              A graph-embedding analysis of whether the relationships between
              XBRL accounting concepts — not the reported numbers — stay
              stable across consecutive SEC filing quarters.
            </p>
            <div className="mt-10 flex flex-wrap items-center gap-4">
              <MetalButton variant="primary" asChild className="h-12 px-7 text-sm">
                <Link href="/explorer">Explore the network</Link>
              </MetalButton>
              <LiquidButton variant="light" size="xl" asChild>
                <Link href="/findings">Read the findings</Link>
              </LiquidButton>
            </div>
          </div>
        </div>
        <HeroChrome />
      </section>

      <section id="metrics" className="mx-auto max-w-6xl px-6 py-24 scroll-mt-24">
        <Reveal>
          <SectionHeading
            accent="Change"
            title="is slowing down — five independent metrics agree."
          />
        </Reveal>
        <StaggerGroup className="mt-10 grid grid-cols-1 gap-4 lg:grid-cols-3">
          <StaggerItem className="lg:col-span-2 lg:row-span-2">
            <KpiCard
              hero
              label={heroMetric.label}
              sublabel={heroMetric.sublabel}
              q1q2={heroMetric.q1q2}
              q2q3={heroMetric.q2q3}
              decelerating={heroMetric.decelerating}
              format={FORMAT_KEYS[heroMetric.id] ?? "decimal"}
            />
          </StaggerItem>
          {restMetrics.map((m) => (
            <StaggerItem key={m.id}>
              <KpiCard
                label={m.label}
                sublabel={m.sublabel}
                q1q2={m.q1q2}
                q2q3={m.q2q3}
                decelerating={m.decelerating}
                format={FORMAT_KEYS[m.id] ?? "decimal"}
              />
            </StaggerItem>
          ))}
        </StaggerGroup>
      </section>

      <section className="mx-auto max-w-6xl px-6 pb-24">
        <StaggerGroup className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <StaggerItem>
            <Card variant="tinted" interactive className="flex h-full flex-col p-8">
              <span className="font-display text-4xl leading-none text-primary/40">&ldquo;</span>
              <div className="-mt-2 text-sm font-medium text-primary">Strongest finding</div>
              <p className="font-display mt-3 text-2xl leading-snug text-foreground">
                {overview.headline}
              </p>
            </Card>
          </StaggerItem>
          <StaggerItem>
            <Card variant="elevated" interactive className="flex h-full flex-col p-8">
              <span className="font-display text-4xl leading-none text-foreground/20">&ldquo;</span>
              <div className="-mt-2 text-sm font-medium text-muted-foreground">Most counter-intuitive</div>
              <p className="font-display mt-3 text-2xl leading-snug text-foreground">
                {overview.counterIntuitive}
              </p>
            </Card>
          </StaggerItem>
        </StaggerGroup>
      </section>

      <section className="mx-auto max-w-6xl px-6 pb-28">
        <Reveal>
          <SectionHeading accent="Three" title="ways of measuring the same drift." />
        </Reveal>
        <Reveal index={1} className="mt-8 grid grid-cols-1 gap-4 lg:grid-cols-5">
          <Card variant="dark" interactive className="p-8 lg:col-span-3">
            <div className="font-mono text-xs text-background/50">01 — per concept</div>
            <h3 className="font-display mt-3 text-2xl font-semibold">Embedding drift</h3>
            <p className="mt-3 max-w-md text-sm text-background/70">
              Cosine distance between a concept&rsquo;s Procrustes-aligned
              node2vec position across quarters — the most granular,
              per-concept signal, and the one every other page of this site
              is built around.
            </p>
          </Card>
          <div className="flex flex-col gap-4 lg:col-span-2">
            <Card interactive className="p-6">
              <div className="font-mono text-xs text-muted-foreground">02 — per graph</div>
              <h3 className="font-display mt-2 text-lg font-semibold text-foreground">Graph drift</h3>
              <p className="mt-2 text-sm text-muted-foreground">
                Centrality and community-membership change computed directly
                from each period&rsquo;s graph — a model-free check against
                the embedding.
              </p>
            </Card>
            <Card interactive className="p-6">
              <div className="font-mono text-xs text-muted-foreground">03 — whole network</div>
              <h3 className="font-display mt-2 text-lg font-semibold text-foreground">Global drift</h3>
              <p className="mt-2 text-sm text-muted-foreground">
                Edge overlap, degree-distribution shape, vocabulary churn —
                statistics that don&rsquo;t depend on any per-concept
                correspondence at all.
              </p>
            </Card>
          </div>
        </Reveal>
      </section>
    </>
  );
}
