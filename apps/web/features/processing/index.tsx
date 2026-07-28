import { SectionCard } from "@/components/section-card";
import { StatusBadge } from "@/components/status-badge";

const PROCESSING_STEPS = [
  {
    title: "Kiểm tra tài liệu",
    description: "Xác nhận tệp có thể đọc và đủ điều kiện xử lý.",
    status: "DRAFT" as const
  },
  {
    title: "Chuẩn bị dữ liệu",
    description: "Hệ thống sắp xếp thông tin để người dùng đối chiếu.",
    status: "DRAFT" as const
  },
  {
    title: "Chuyển sang kiểm tra",
    description: "Kết quả ban đầu phải được người dùng xác nhận.",
    status: "PENDING_REVIEW" as const
  }
] as const;

export function ProcessingFeature() {
  return (
    <SectionCard
      title="Tiến độ xử lý"
      description="Ba bước cần hoàn tất trước khi hồ sơ được kiểm tra."
    >
      <ol className="timeline">
        {PROCESSING_STEPS.map((step, index) => (
          <li key={step.title}>
            <span className="timeline-index" aria-hidden="true">
              {index + 1}
            </span>
            <div>
              <h3>{step.title}</h3>
              <p>{step.description}</p>
            </div>
            <StatusBadge status={step.status} compact />
          </li>
        ))}
      </ol>
    </SectionCard>
  );
}
