export type PlatformStatus =
  | "DRAFT"
  | "PENDING_REVIEW"
  | "IN_REVIEW"
  | "NEEDS_CORRECTION"
  | "REJECTED"
  | "APPROVED"
  | "PUBLISHED"
  | "UNOFFICIAL"
  | "OFFICIAL";

export type StatusTone = "neutral" | "review" | "success" | "danger";

export interface StatusPresentation {
  label: string;
  tone: StatusTone;
}

export const STATUS_PRESENTATION: Readonly<
  Record<PlatformStatus, StatusPresentation>
> = {
  DRAFT: { label: "Bản nháp", tone: "neutral" },
  PENDING_REVIEW: { label: "Chờ kiểm tra", tone: "review" },
  IN_REVIEW: { label: "Đang kiểm tra", tone: "review" },
  NEEDS_CORRECTION: { label: "Cần hiệu chỉnh", tone: "review" },
  REJECTED: { label: "Đã từ chối", tone: "danger" },
  APPROVED: { label: "Đã phê duyệt", tone: "success" },
  PUBLISHED: { label: "Đã công bố", tone: "success" },
  UNOFFICIAL: { label: "Chưa chính thức", tone: "review" },
  OFFICIAL: { label: "Chính thức", tone: "success" }
};
