import type { AppIconName } from "@/components/icons";

export interface NavigationItem {
  label: string;
  href: string;
  icon: AppIconName;
}

export const NAVIGATION_ITEMS: readonly NavigationItem[] = [
  { label: "Tổng quan", href: "/dashboard", icon: "dashboard" },
  { label: "Tiếp nhận hồ sơ", href: "/intake", icon: "intake" },
  { label: "Xử lý hồ sơ", href: "/jobs", icon: "jobs" },
  { label: "Kiểm tra dữ liệu", href: "/review", icon: "review" },
  { label: "Phê duyệt", href: "/publishing", icon: "approval" },
  { label: "Kết quả và xuất file", href: "/exports", icon: "exports" },
  { label: "Biểu mẫu", href: "/forms", icon: "forms" },
  { label: "Nhật ký", href: "/audit", icon: "audit" },
  { label: "Quản trị hệ thống", href: "/admin", icon: "admin" },
  { label: "Hướng dẫn sử dụng", href: "/help", icon: "help" }
] as const;
