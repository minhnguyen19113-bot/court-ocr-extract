import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { Sidebar } from "../components/sidebar";
import "./setup";

vi.mock("next/navigation", () => ({
  usePathname: () => "/dashboard",
}));

const expectedItems = [
  ["Tổng quan", "/dashboard"],
  ["Tiếp nhận hồ sơ", "/intake"],
  ["Xử lý hồ sơ", "/jobs"],
  ["Kiểm tra dữ liệu", "/review"],
  ["Phê duyệt", "/publishing"],
  ["Kết quả và xuất file", "/exports"],
  ["Biểu mẫu", "/forms"],
  ["Nhật ký", "/audit"],
  ["Quản trị hệ thống", "/admin"],
  ["Hướng dẫn sử dụng", "/help"],
] as const;

describe("Sidebar", () => {
  it("exposes the ten Vietnamese workflow destinations as links", () => {
    render(<Sidebar />);

    expect(screen.getByRole("navigation")).toBeInTheDocument();
    for (const [label, href] of expectedItems) {
      expect(screen.getByRole("link", { name: label })).toHaveAttribute(
        "href",
        href,
      );
    }
    expect(screen.getAllByRole("link")).toHaveLength(10);
    expect(screen.queryByText(/OCR/i)).not.toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Tổng quan" }),
    ).toHaveAttribute("aria-current", "page");
  });
});
