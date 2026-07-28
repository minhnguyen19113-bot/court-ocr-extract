import {
  ArrowRight,
  BadgeCheck,
  Bell,
  CircleHelp,
  ClipboardCheck,
  Download,
  FileText,
  Files,
  FolderOpen,
  History,
  Inbox,
  LayoutDashboard,
  Scale,
  Settings,
  UserRound,
  type LucideIcon
} from "lucide-react";

export type AppIconName =
  | "dashboard"
  | "intake"
  | "jobs"
  | "review"
  | "approval"
  | "exports"
  | "forms"
  | "audit"
  | "admin"
  | "help";

const APP_ICONS: Readonly<Record<AppIconName, LucideIcon>> = {
  dashboard: LayoutDashboard,
  intake: Inbox,
  jobs: Files,
  review: ClipboardCheck,
  approval: BadgeCheck,
  exports: Download,
  forms: FileText,
  audit: History,
  admin: Settings,
  help: CircleHelp
};

export function NavigationIcon({ name }: Readonly<{ name: AppIconName }>) {
  const Icon = APP_ICONS[name];
  return <Icon aria-hidden="true" focusable="false" size={19} strokeWidth={1.8} />;
}

export {
  ArrowRight,
  Bell,
  CircleHelp,
  FileText,
  FolderOpen,
  Scale,
  UserRound
};
