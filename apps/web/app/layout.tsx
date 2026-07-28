import type { Metadata } from "next";
import type { ReactNode } from "react";

import { AppShell } from "@/components/app-shell";

import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: {
    default: "Nền tảng dữ liệu hồ sơ Tòa án",
    template: "%s | Nền tảng dữ liệu hồ sơ Tòa án"
  },
  description:
    "Nền tảng kiểm tra, phê duyệt, công bố dữ liệu và soạn biểu mẫu từ hồ sơ Tòa án."
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="vi">
      <body>
        <a className="skip-link" href="#main-content">
          Chuyển đến nội dung chính
        </a>
        <Providers>
          <AppShell>{children}</AppShell>
        </Providers>
      </body>
    </html>
  );
}
