import { EnvironmentBadge } from "@/components/environment-badge";
import { Bell } from "@/components/icons";
import { UserMenuPlaceholder } from "@/components/user-menu-placeholder";

export function TopBar() {
  return (
    <header className="top-bar">
      <EnvironmentBadge />
      <div className="top-bar-actions">
        <button className="icon-button" type="button" aria-label="Xem thông báo">
          <Bell aria-hidden="true" size={20} strokeWidth={1.8} />
        </button>
        <UserMenuPlaceholder />
      </div>
    </header>
  );
}
