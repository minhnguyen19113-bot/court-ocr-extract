import { ModulePage } from "@/components/module-page";
import { PageHeader } from "@/components/page-header";
import { PrimaryAction } from "@/components/primary-action";
import { SchemaContractPanel } from "@/components/schema-contract-panel";
import { SectionCard } from "@/components/section-card";
import { StatusBadge } from "@/components/status-badge";

export function ReviewFeature() {
  return (
    <ModulePage
      title="Kiểm tra dữ liệu"
      description="Đối chiếu từng trường thông tin trước khi chuyển hồ sơ sang phê duyệt."
      emptyTitle="Không có hồ sơ chờ kiểm tra"
      emptyDescription="Hồ sơ đã chuẩn bị xong dữ liệu sẽ xuất hiện tại đây."
      nextStep="Theo dõi khu vực Xử lý hồ sơ."
      actionLabel="Bắt đầu kiểm tra"
      actionDisabled
    >
      <SchemaContractPanel />
    </ModulePage>
  );
}

export function ReviewDetailFeature({ reviewId }: { reviewId: string }) {
  return (
    <div className="page-stack">
      <PageHeader
        title="Chi tiết kiểm tra dữ liệu"
        description="Đối chiếu thông tin và ghi lại nội dung cần hiệu chỉnh."
        action={<PrimaryAction label="Lưu kết quả kiểm tra" disabled />}
      />
      <div className="context-row">
        <span>Mã tham chiếu: {reviewId}</span>
        <StatusBadge status="IN_REVIEW" />
      </div>
      <SectionCard
        title="Ghi chú kiểm tra"
        description="Ghi rõ nội dung cần xác nhận hoặc hiệu chỉnh."
      >
        <label htmlFor="review-note">Nội dung ghi chú</label>
        <textarea
          id="review-note"
          rows={4}
          placeholder="Chưa có ghi chú."
          disabled
        />
        <p className="notice">
          Chức năng lưu và phê duyệt đang được chuẩn bị.
        </p>
      </SectionCard>
      <SchemaContractPanel />
    </div>
  );
}
