import { cn } from "@/lib/cn";

type Props = {
  title: string;
  question?: string;
  rightSlot?: React.ReactNode;
  className?: string;
  children: React.ReactNode;
};

export function Panel({ title, question, rightSlot, className, children }: Props) {
  return (
    <section className={cn("panel", className)}>
      <header className="panel-header">
        <div>
          <h3 className="panel-title">{title}</h3>
          {question ? <p className="panel-question mt-0.5">{question}</p> : null}
        </div>
        {rightSlot ? <div className="text-2xs text-ink-500">{rightSlot}</div> : null}
      </header>
      <div className="divide-y divide-ink-100">{children}</div>
    </section>
  );
}
