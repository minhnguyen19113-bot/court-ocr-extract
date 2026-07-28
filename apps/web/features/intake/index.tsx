import { ModulePage } from "@/components/module-page";
import { SectionCard } from "@/components/section-card";

export function IntakeFeature() {
  return (
    <ModulePage
      title="Tiếp nhận hồ sơ"
      description="Ghi nhận hồ sơ mới và kiểm tra thông tin đầu vào trước khi xử lý."
      emptyTitle="Chưa có hồ sơ mới"
      emptyDescription="Hồ sơ được tiếp nhận sẽ xuất hiện tại đây."
      nextStep="Chọn tệp và xác nhận thông tin khi chức năng được mở."
      actionLabel="Tiếp nhận hồ sơ"
      actionDisabled
    >
      <SectionCard
        title="Thông tin tiếp nhận"
        description="Chức năng này đang được chuẩn bị và chưa nhận tệp thật."
      >
        <div className="form-grid">
          <label htmlFor="case-domain">Lĩnh vực vụ việc</label>
          <select id="case-domain" defaultValue="criminal" disabled>
            <option value="criminal">Hình sự</option>
          </select>

          <label htmlFor="document-source">Nguồn hồ sơ</label>
          <select id="document-source" defaultValue="user-file" disabled>
            <option value="user-file">Tệp do người dùng lựa chọn</option>
          </select>

          <label htmlFor="intake-file">Tệp PDF hoặc ảnh</label>
          <input
            id="intake-file"
            type="file"
            accept=".pdf,.jpg,.jpeg,.png"
            disabled
          />
        </div>
        <p className="notice">
          Chưa thể tiếp nhận tệp ở bản thử nghiệm này. Nút thao tác sẽ được mở khi
          quy trình lưu trữ và bảo vệ hồ sơ sẵn sàng.
        </p>
      </SectionCard>
    </ModulePage>
  );
}
