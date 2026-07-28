import type { PlatformStatus } from "@/lib/formatting/status";
import { StatusBadge } from "@/components/status-badge";

export interface SummaryCardProps {
  label: string;
  value: number;
  status: PlatformStatus;
  helper: string;
}

export function SummaryCard({
  label,
  value,
  status,
  helper
}: Readonly<SummaryCardProps>) {
  return (
    <article className="summary-card">
      <div className="summary-card-heading">
        <h2>{label}</h2>
        <StatusBadge status={status} compact />
      </div>
      <strong className="summary-value" aria-label={`${label}: ${value}`}>
        {value}
      </strong>
      <p>{helper}</p>
    </article>
  );
}
