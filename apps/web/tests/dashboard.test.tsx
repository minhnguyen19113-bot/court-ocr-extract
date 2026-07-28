import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import DashboardPage from "../app/dashboard/page";
import "./setup";

describe("DashboardPage", () => {
  it("renders exactly four primary operational summaries", async () => {
    render(await DashboardPage());

    for (const [label, value] of [
      ["Hồ sơ mới tiếp nhận", 12],
      ["Đang xử lý", 4],
      ["Chờ kiểm tra", 7],
      ["Đã phê duyệt", 18],
    ]) {
      expect(screen.getByLabelText(`${label}: ${value}`)).toBeInTheDocument();
    }

    expect(screen.getAllByRole("article")).toHaveLength(4);
    expect(screen.queryByText("Chờ công bố")).not.toBeInTheDocument();
    expect(screen.queryByText("Biểu mẫu đã sinh")).not.toBeInTheDocument();
    expect(screen.getByText("Dữ liệu minh họa")).toBeInTheDocument();
    expect(screen.queryByText(/synthetic/i)).not.toBeInTheDocument();
    expect(
      screen.getByRole("heading", { level: 2, name: "Công việc cần xử lý" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { level: 2, name: "Lối tắt" }),
    ).toBeInTheDocument();
  });
});
