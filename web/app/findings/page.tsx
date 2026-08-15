import { getFindings, getOverview } from "@/lib/data";
import { SectionHeading, StatusPill } from "@/components/ui/card";
import { Toc } from "@/components/findings/toc";
import { Reveal, StaggerGroup, StaggerItem } from "@/components/motion/reveal";

export default async function FindingsPage() {
  const [findings, overview] = await Promise.all([getFindings(), getOverview()]);

  return (
    <div className="mx-auto max-w-6xl px-6 pb-28 pt-32">
      <Reveal>
        <SectionHeading
          accent="Findings:"
          title="the full report, question by question."
          description={`${findings.answeredQuestions} of ${findings.totalQuestions} planned empirical questions have real evidence as of this run — the rest are flagged honestly as open, each with a note on what it would take.`}
        />
      </Reveal>

      <Reveal index={1}>
        <blockquote className="font-display mt-12 max-w-3xl text-3xl leading-snug text-foreground">
          {overview.headline}
        </blockquote>
        <blockquote className="font-display mt-8 max-w-3xl text-2xl leading-snug text-foreground/60">
          {overview.counterIntuitive}
        </blockquote>
      </Reveal>

      <div className="mt-16 flex flex-col gap-16 lg:flex-row lg:items-start lg:gap-12">
        <Toc sections={findings.sections.map((s) => ({ letter: s.letter, title: s.title }))} />

        <div className="min-w-0 flex-1">
          {findings.sections.map((s) => (
            <section
              key={s.letter}
              id={`section-${s.letter}`}
              className="scroll-mt-24 border-t border-border/60 py-10 first:border-0 first:pt-0"
            >
              <h2 className="font-display text-2xl font-semibold text-foreground">
                <span className="text-primary">{s.letter}.</span> {s.title}
              </h2>
              <StaggerGroup className="mt-6 flex flex-col gap-3">
                {s.questions.map((q) => (
                  <StaggerItem key={q.number}>
                    <div className="flex items-start gap-4 rounded-2xl border border-border/60 bg-card p-4 transition-colors hover:border-primary/25">
                      <span className="mt-0.5 shrink-0 font-mono text-xs text-muted-foreground">
                        {q.number}
                      </span>
                      <p className="flex-1 text-sm text-foreground/90">{q.text}</p>
                      <StatusPill status={q.status} className="mt-0.5 shrink-0" />
                    </div>
                  </StaggerItem>
                ))}
              </StaggerGroup>
            </section>
          ))}
        </div>
      </div>
    </div>
  );
}
