"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { NavigationIcon, Scale } from "@/components/icons";
import { NAVIGATION_ITEMS } from "@/lib/navigation";

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="sidebar" aria-label="Thanh điều hướng">
      <div className="brand-block">
        <span className="brand-mark" aria-hidden="true">
          <Scale size={23} strokeWidth={1.7} />
        </span>
        <strong>Nền tảng dữ liệu Tòa án</strong>
        <span>Hồ sơ · Dữ liệu · Biểu mẫu</span>
      </div>
      <nav aria-label="Điều hướng chính">
        <ul className="nav-list">
          {NAVIGATION_ITEMS.map((item) => {
            const isActive =
              pathname === item.href ||
              (item.href !== "/dashboard" && pathname.startsWith(`${item.href}/`));
            return (
              <li key={item.href}>
                <Link
                  className="nav-link"
                  href={item.href}
                  aria-current={isActive ? "page" : undefined}
                >
                  <span className="nav-icon" aria-hidden="true">
                    <NavigationIcon name={item.icon} />
                  </span>
                  <span>{item.label}</span>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
    </aside>
  );
}
