export type AppRole =
  | "operator"
  | "reviewer"
  | "approver"
  | "project_admin"
  | "system_admin";

export type AppCapability =
  | "view_intake"
  | "view_jobs"
  | "review_fields"
  | "approve_review"
  | "request_publish"
  | "manage_project"
  | "manage_system";

export const ROLE_CAPABILITIES: Readonly<Record<AppRole, readonly AppCapability[]>> = {
  operator: ["view_intake", "view_jobs"],
  reviewer: ["view_intake", "view_jobs", "review_fields"],
  approver: [
    "view_intake",
    "view_jobs",
    "review_fields",
    "approve_review",
    "request_publish"
  ],
  project_admin: [
    "view_intake",
    "view_jobs",
    "review_fields",
    "approve_review",
    "request_publish",
    "manage_project"
  ],
  system_admin: [
    "view_intake",
    "view_jobs",
    "review_fields",
    "approve_review",
    "request_publish",
    "manage_project",
    "manage_system"
  ]
};

export function hasCapability(
  role: AppRole,
  capability: AppCapability
): boolean {
  return ROLE_CAPABILITIES[role].includes(capability);
}
