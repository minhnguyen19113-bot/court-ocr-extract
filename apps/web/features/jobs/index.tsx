import { EmptyState } from "@/components/empty-state";
import { ModulePage } from "@/components/module-page";
import { PageHeader } from "@/components/page-header";
import { PrimaryAction } from "@/components/primary-action";
import { SectionCard } from "@/components/section-card";
import { StatusBadge } from "@/components/status-badge";
import { ProcessingFeature } from "@/features/processing";

export function JobsFeature() {
  return (
    <ModulePage
      title="Xử lý hồ sơ"
      description="Theo dõi tiến độ chuẩn bị dữ liệu của từng hồ sơ mà không hiển thị nội dung nhạy cảm."
      emptyTitle="Chưa có hồ sơ đang xử lý"
      emptyDescription="Hồ sơ sẽ xuất hiện sau khi được tiếp nhận thành công."
      nextStep="Tiếp nhận hồ sơ mới khi chức năng được mở."
      actionLabel="Tạo đợt xử lý"
      actionDisabled
    >
      <SectionCard title="Danh sách hồ sơ" description="Lọc theo trạng thái công việc.">
        <div className="filter-row">
          <div>
            <label htmlFor="job-status-filter">Trạng thái</label>
            <select id="job-status-filter" defaultValue="all">
              <option value="all">Tất cả trạng thái</option>
              <option value="draft">Mới tiếp nhận</option>
              <option value="processing">Đang xử lý</option>
              <option value="pending_review">Chờ kiểm tra</option>
            </select>
          </div>
        </div>
        <EmptyState
          title="Chưa có hồ sơ phù hợp"
          description="Không có hồ sơ nào phù hợp với bộ lọc hiện tại."
          nextStep="Thay đổi bộ lọc hoặc quay lại sau."
        />
      </SectionCard>
    </ModulePage>
  );
}

export function JobDetailFeature({ jobId }: { jobId: string }) {
  return (
    <div className="page-stack">
      <PageHeader
        title="Chi tiết xử lý hồ sơ"
        description="Xem tiến độ và bước đang chờ xác nhận của hồ sơ."
        action={<PrimaryAction label="Tiếp tục xử lý" disabled />}
      />
      <div className="context-row">
        <span>Mã tham chiếu: {jobId}</span>
        <StatusBadge status="DRAFT" />
      </div>
      <ProcessingFeature />
    </div>
  );
}
