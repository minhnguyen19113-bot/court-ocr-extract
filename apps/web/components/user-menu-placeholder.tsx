import { UserRound } from "@/components/icons";

export function UserMenuPlaceholder() {
  return (
    <div className="user-menu-placeholder" aria-label="Người dùng thử nghiệm">
      <span className="user-avatar" aria-hidden="true">
        <UserRound size={17} strokeWidth={1.8} />
      </span>
      <strong>Người dùng thử nghiệm</strong>
    </div>
  );
}
