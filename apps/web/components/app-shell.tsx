import type { ReactNode } from "react";

import { Sidebar } from "@/components/sidebar";
import { TopBar } from "@/components/top-bar";

export interface AppShellProps {
  children: ReactNode;
}

export function AppShell({ children }: Readonly<AppShellProps>) {
  return (
    <div className="app-shell">
      <Sidebar />
      <TopBar />
      <main className="content-area" id="main-content" tabIndex={-1}>
        {children}
      </main>
    </div>
  );
}
