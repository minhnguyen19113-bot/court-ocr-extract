import { FolderOpen } from "@/components/icons";

export interface EmptyStateProps {
  title: string;
  description: string;
  nextStep?: string;
}

export function EmptyState({
  title,
  description,
  nextStep
}: Readonly<EmptyStateProps>) {
  return (
    <div className="empty-state">
      <span className="empty-state-icon" aria-hidden="true">
        <FolderOpen size={26} strokeWidth={1.6} />
      </span>
      <h2>{title}</h2>
      <p>{description}</p>
      {nextStep ? <p className="empty-state-next">Bước tiếp theo: {nextStep}</p> : null}
    </div>
  );
}
