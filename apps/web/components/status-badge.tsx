import {
  BadgeCheck,
  Circle,
  CircleCheck,
  Clock3,
  Search,
  TriangleAlert,
  XCircle,
  type LucideIcon
} from "lucide-react";

import {
  STATUS_PRESENTATION,
  type PlatformStatus
} from "@/lib/formatting/status";

export interface StatusBadgeProps {
  status: PlatformStatus;
  compact?: boolean;
}

const STATUS_ICONS: Readonly<Record<PlatformStatus, LucideIcon>> = {
  DRAFT: Circle,
  PENDING_REVIEW: Clock3,
  IN_REVIEW: Search,
  NEEDS_CORRECTION: TriangleAlert,
  REJECTED: XCircle,
  APPROVED: CircleCheck,
  PUBLISHED: BadgeCheck,
  UNOFFICIAL: Clock3,
  OFFICIAL: CircleCheck
};

export function StatusBadge({
  status,
  compact = false
}: Readonly<StatusBadgeProps>) {
  const presentation = STATUS_PRESENTATION[status];
  const Icon = STATUS_ICONS[status];

  return (
    <span
      className={`status-badge status-${presentation.tone}${compact ? " status-compact" : ""}`}
      aria-label={`Trạng thái: ${presentation.label}`}
    >
      <Icon aria-hidden="true" focusable="false" size={14} strokeWidth={2} />
      <span>{presentation.label}</span>
    </span>
  );
}
