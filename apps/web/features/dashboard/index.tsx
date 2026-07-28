import Link from "next/link";

import { PageHeader } from "@/components/page-header";
import { PrimaryAction } from "@/components/primary-action";
import { SectionCard } from "@/components/section-card";
import { StatusBadge } from "@/components/status-badge";
import { SummaryCard } from "@/components/summary-card";

const SUMMARY_ITEMS = [
  {
    label: "Hồ sơ mới tiếp nhận",
    value: 12,
    status: "DRAFT" as const,
    helper: "Cần xác nhận thông tin đầu vào"
  },
  {
    label: "Đang xử lý",
    value: 4,
    status: "IN_REVIEW" as const,
    helper: "Đang được hệ thống chuẩn bị dữ liệu"
  },
  {
    label: "Chờ kiểm tra",
    value: 7,
    status: "PENDING_REVIEW" as const,
    helper: "Cần người dùng đối chiếu"
  },
  {
    label: "Đã phê duyệt",
    value: 18,
    status: "APPROVED" as const,
    helper: "Đã hoàn thành bước xác nhận"
  }
] as const;

const WORK_ITEMS = [
  {
    title: "Kiểm tra hồ sơ mới tiếp nhận",
    description: "12 hồ sơ đang chờ xác nhận thông tin ban đầu.",
    status: "PENDING_REVIEW" as const
  },
  {
    title: "Đối chiếu dữ liệu",
    description: "7 hồ sơ đã sẵn sàng để người dùng kiểm tra.",
    status: "IN_REVIEW" as const
  },
  {
    title: "Hoàn tất phê duyệt",
    description: "3 hồ sơ cần xác nhận trước khi lưu kết quả.",
    status: "APPROVED" as const
  }
] as const;

export function DashboardFeature() {
  return (
    <div className="page-stack">
      <PageHeader
        title="Tổng quan"
        description="Theo dõi hồ sơ cần xử lý và các công việc đang chờ xác nhận."
        action={<PrimaryAction label="Tiếp nhận hồ sơ" href="/intake" />}
      />

      <section className="summary-section" aria-labelledby="summary-heading">
        <div className="section-heading">
          <div>
            <h2 id="summary-heading">Tình hình hồ sơ</h2>
            <p>Dữ liệu minh họa</p>
          </div>
        </div>
        <div className="summary-grid">
          {SUMMARY_ITEMS.map((item) => (
            <SummaryCard key={item.label} {...item} />
          ))}
        </div>
      </section>

      <div className="dashboard-secondary-grid">
        <SectionCard
          title="Công việc cần xử lý"
          description="Ưu tiên theo bước đang chờ người dùng xác nhận."
        >
          <ul className="work-list">
            {WORK_ITEMS.map((item) => (
              <li key={item.title}>
                <div>
                  <h3>{item.title}</h3>
                  <p>{item.description}</p>
                </div>
                <StatusBadge status={item.status} compact />
              </li>
            ))}
          </ul>
        </SectionCard>

        <SectionCard
          title="Lối tắt"
          description="Mở nhanh các khu vực thường dùng."
        >
          <nav aria-label="Lối tắt">
            <ul className="shortcut-list">
              <li>
                <Link href="/jobs">Xử lý hồ sơ</Link>
              </li>
              <li>
                <Link href="/review">Kiểm tra dữ liệu</Link>
              </li>
              <li>
                <Link href="/exports">Kết quả và xuất file</Link>
              </li>
            </ul>
          </nav>
        </SectionCard>
      </div>
    </div>
  );
}
