import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { StatusBadge } from "../components/status-badge";
import "./setup";

describe("StatusBadge", () => {
  it("uses text and an accessible label, not color alone", () => {
    const { rerender } = render(<StatusBadge status="APPROVED" />);

    const approved = screen.getByLabelText("Trạng thái: Đã phê duyệt");
    expect(approved).toHaveTextContent(/Đã phê duyệt/i);
    expect(approved.querySelector("[aria-hidden='true']")).toBeInTheDocument();

    rerender(<StatusBadge status="PUBLISHED" />);

    const published = screen.getByLabelText("Trạng thái: Đã công bố");
    expect(published).toHaveTextContent(/Đã công bố/i);
    expect(published.querySelector("[aria-hidden='true']")).toBeInTheDocument();
  });
});
