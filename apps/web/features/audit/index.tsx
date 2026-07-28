import { EmptyState } from "@/components/empty-state";
import { ModulePage } from "@/components/module-page";
import { SectionCard } from "@/components/section-card";

export function AuditFeature() {
  return (
    <ModulePage
      title="Nhật ký"
      description="Theo dõi các thao tác quan trọng đã thực hiện trên hồ sơ."
      emptyTitle="Chưa có hoạt động được ghi nhận"
      emptyDescription="Các thao tác phù hợp sẽ được ghi lại theo thời gian."
      nextStep="Quay lại sau khi có hoạt động trên hồ sơ."
      actionLabel="Xem chi tiết"
      actionDisabled
    >
      <SectionCard
        title="Hoạt động gần đây"
        description="Lọc hoạt động theo nhóm nghiệp vụ."
      >
        <div className="filter-row">
          <div>
            <label htmlFor="audit-event-filter">Loại hoạt động</label>
            <select id="audit-event-filter" defaultValue="all">
              <option value="all">Tất cả hoạt động</option>
              <option value="review">Kiểm tra dữ liệu</option>
              <option value="approval">Phê duyệt</option>
              <option value="publication">Lưu kết quả</option>
              <option value="export">Xuất file</option>
            </select>
          </div>
        </div>
        <EmptyState
          title="Chưa có hoạt động"
          description="Không có hoạt động nào phù hợp với bộ lọc hiện tại."
          nextStep="Thay đổi bộ lọc hoặc quay lại sau."
        />
      </SectionCard>
    </ModulePage>
  );
}
