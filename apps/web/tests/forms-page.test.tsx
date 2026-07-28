import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import FormsPage from "../app/forms/page";
import "./setup";

describe("FormsPage", () => {
  it("states adapter limitations and keeps official generation unavailable", async () => {
    render(await FormsPage());

    expect(screen.getByRole("heading", { name: "Biểu mẫu" })).toBeInTheDocument();
    expect(screen.queryByText(/NOT_IMPLEMENTED/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/DECLARED/i)).not.toBeInTheDocument();
    expect(
      screen.getAllByText(/chưa hỗ trợ|đang chuẩn bị/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByText(/loại bỏ.*phần hướng dẫn/i),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Tạo biểu mẫu/i }),
    ).toBeDisabled();
  });
});
