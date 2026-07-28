import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { AppShell } from "../components/app-shell";
import "./setup";

vi.mock("next/navigation", () => ({
  usePathname: () => "/dashboard",
}));

describe("AppShell", () => {
  it("renders the simplified trial context and main content", () => {
    render(
      <AppShell>
        <p>Nội dung kiểm thử tổng hợp</p>
      </AppShell>,
    );

    expect(screen.getByRole("navigation")).toBeInTheDocument();
    expect(screen.getByRole("main")).toHaveTextContent(
      "Nội dung kiểm thử tổng hợp",
    );
    expect(screen.getByText("Bản thử nghiệm")).toBeInTheDocument();
    expect(screen.queryByText(/Môi trường local/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Phase 0/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Vai trò:/i)).not.toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Xem thông báo" }),
    ).toBeInTheDocument();
  });
});
