import { ModulePage } from "@/components/module-page";
import { SectionCard } from "@/components/section-card";
import { StatusBadge } from "@/components/status-badge";

export function PublishingFeature() {
  return (
    <ModulePage
      title="Phê duyệt"
      description="Xác nhận hồ sơ đã được kiểm tra đầy đủ trước khi lưu kết quả."
      emptyTitle="Không có hồ sơ chờ phê duyệt"
      emptyDescription="Chỉ hồ sơ đã hoàn tất kiểm tra mới xuất hiện tại đây."
      nextStep="Hoàn tất bước Kiểm tra dữ liệu."
      actionLabel="Phê duyệt hồ sơ"
      actionDisabled
    >
      <SectionCard
        title="Điều kiện phê duyệt"
        description="Hồ sơ chỉ được phê duyệt khi đáp ứng đầy đủ các điều kiện."
      >
        <div className="section-status">
          <StatusBadge status="UNOFFICIAL" />
        </div>
        <ul className="check-list">
          <li>Có người chịu trách nhiệm xác nhận hồ sơ.</li>
          <li>Không còn cảnh báo nghiêm trọng chưa xử lý.</li>
          <li>Thông tin bắt buộc có giá trị hoặc lý do để trống rõ ràng.</li>
          <li>Nội dung đã kiểm tra được khóa trước khi phê duyệt.</li>
        </ul>
        <p className="notice">
          Chức năng phê duyệt chưa được mở trong bản thử nghiệm này.
        </p>
      </SectionCard>
    </ModulePage>
  );
}
