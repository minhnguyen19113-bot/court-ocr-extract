import type { ReactNode } from "react";

export interface SectionCardProps {
  title: string;
  description?: string;
  children: ReactNode;
  className?: string;
}

export function SectionCard({
  title,
  description,
  children,
  className = ""
}: Readonly<SectionCardProps>) {
  return (
    <section className={`section-card ${className}`.trim()}>
      <div className="section-card-heading">
        <div>
          <h2>{title}</h2>
          {description ? <p>{description}</p> : null}
        </div>
      </div>
      {children}
    </section>
  );
}
