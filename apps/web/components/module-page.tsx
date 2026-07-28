import type { ReactNode } from "react";

import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";
import { PrimaryAction } from "@/components/primary-action";

export interface ModulePageProps {
  title: string;
  description: string;
  emptyTitle: string;
  emptyDescription: string;
  actionLabel: string;
  actionHref?: string;
  actionDisabled?: boolean;
  nextStep?: string;
  children?: ReactNode;
}

export function ModulePage({
  title,
  description,
  emptyTitle,
  emptyDescription,
  actionLabel,
  actionHref,
  actionDisabled = false,
  nextStep,
  children
}: Readonly<ModulePageProps>) {
  const action =
    actionDisabled || !actionHref ? (
      <PrimaryAction label={actionLabel} disabled />
    ) : (
      <PrimaryAction label={actionLabel} href={actionHref} />
    );

  return (
    <div className="module-page">
      <PageHeader title={title} description={description} action={action} />
      {children ? (
        children
      ) : (
        <EmptyState
          title={emptyTitle}
          description={emptyDescription}
          nextStep={nextStep}
        />
      )}
    </div>
  );
}
