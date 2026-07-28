import { ModulePage } from "@/components/module-page";
import { SectionCard } from "@/components/section-card";

export function AdminFeature() {
  return (
    <ModulePage
      title="Quản trị hệ thống"
      description="Theo dõi cấu hình và khả năng đang được chuẩn bị cho hệ thống."
      emptyTitle="Chưa có cấu hình cần cập nhật"
      emptyDescription="Các thiết lập quản trị sẽ xuất hiện khi quyền truy cập được hoàn thiện."
      nextStep="Chờ quản trị viên mở quyền phù hợp."
      actionLabel="Lưu cấu hình"
      actionDisabled
    >
      <SectionCard
        title="Cấu hình chung"
        description="Các thiết lập hiện chỉ để xem và chưa thể thay đổi."
      >
        <div className="form-grid">
          <label htmlFor="admin-release">Trạng thái phát hành</label>
          <select id="admin-release" defaultValue="trial" disabled>
            <option value="trial">Bản thử nghiệm</option>
          </select>

          <label htmlFor="admin-default-domain">Lĩnh vực mặc định</label>
          <select id="admin-default-domain" defaultValue="criminal" disabled>
            <option value="criminal">Hình sự</option>
          </select>
        </div>
        <details className="advanced-details">
          <summary>Thông tin kỹ thuật nâng cao</summary>
          <p>
            Khu vực này sẽ hiển thị phiên bản cấu hình và tình trạng kết nối khi
            chức năng quản trị được mở.
          </p>
        </details>
      </SectionCard>
    </ModulePage>
  );
}

export function HelpFeature() {
  return (
    <ModulePage
      title="Hướng dẫn sử dụng"
      description="Nắm các bước chính từ tiếp nhận hồ sơ đến phê duyệt và xuất kết quả."
      emptyTitle="Chưa có hướng dẫn mở rộng"
      emptyDescription="Hướng dẫn chi tiết sẽ được bổ sung theo từng chức năng."
      nextStep="Bắt đầu tại khu vực Tiếp nhận hồ sơ."
      actionLabel="Bắt đầu tiếp nhận"
      actionHref="/intake"
    >
      <SectionCard
        title="Quy trình cơ bản"
        description="Thực hiện lần lượt năm bước để bảo đảm dữ liệu được xác nhận."
      >
        <ol className="guidance-steps">
          <li>Tiếp nhận hồ sơ và kiểm tra thông tin đầu vào.</li>
          <li>Theo dõi quá trình chuẩn bị dữ liệu.</li>
          <li>Đối chiếu từng trường thông tin cần thiết.</li>
          <li>Phê duyệt hồ sơ sau khi đã kiểm tra đầy đủ.</li>
          <li>Xuất kết quả hoặc chuẩn bị biểu mẫu phù hợp.</li>
        </ol>
        <p className="notice">
          Thông tin chưa được phê duyệt không phải dữ liệu chính thức.
        </p>
      </SectionCard>
    </ModulePage>
  );
}
