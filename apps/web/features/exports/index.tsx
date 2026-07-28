import { ModulePage } from "@/components/module-page";
import { SectionCard } from "@/components/section-card";

export function ExportsFeature() {
  return (
    <ModulePage
      title="Kết quả và xuất file"
      description="Tải kết quả nghiệp vụ từ hồ sơ đã hoàn tất bước kiểm tra phù hợp."
      emptyTitle="Chưa có kết quả sẵn sàng"
      emptyDescription="Kết quả sẽ xuất hiện sau khi hồ sơ được xác nhận."
      nextStep="Kiểm tra trạng thái hồ sơ trong khu vực Phê duyệt."
      actionLabel="Xuất tệp"
      actionDisabled
    >
      <SectionCard
        title="Tùy chọn xuất file"
        description="Bản thử nghiệm hiện chỉ giới thiệu định dạng Excel."
      >
        <div className="form-grid">
          <label htmlFor="export-format">Định dạng đầu ra</label>
          <select id="export-format" defaultValue="xlsx" disabled>
            <option value="xlsx">Excel (.xlsx)</option>
          </select>
        </div>
        <p className="notice">
          Chức năng tạo và tải tệp đang được chuẩn bị.
        </p>
      </SectionCard>
    </ModulePage>
  );
}
