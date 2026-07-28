import { ModulePage } from "@/components/module-page";
import { PageHeader } from "@/components/page-header";
import { PrimaryAction } from "@/components/primary-action";
import { SectionCard } from "@/components/section-card";
import { StatusBadge } from "@/components/status-badge";

export function FormsFeature() {
  return (
    <ModulePage
      title="Biểu mẫu"
      description="Chọn biểu mẫu và nguồn thông tin đã được phê duyệt để chuẩn bị văn bản."
      emptyTitle="Chưa có biểu mẫu khả dụng"
      emptyDescription="Danh mục biểu mẫu đang được chuẩn bị."
      nextStep="Quay lại khi danh mục và quy tắc tạo văn bản đã được xác nhận."
      actionLabel="Tạo biểu mẫu"
      actionDisabled
    >
      <SectionCard
        title="Danh mục biểu mẫu"
        description="Các định dạng bên dưới chưa thể tạo văn bản chính thức."
      >
        <div className="form-grid">
          <label htmlFor="form-domain-filter">Lĩnh vực</label>
          <select id="form-domain-filter" defaultValue="criminal" disabled>
            <option value="criminal">Hình sự</option>
          </select>
        </div>
        <div className="schema-table-wrap">
          <table className="schema-table">
            <caption>Tình trạng chuẩn bị định dạng biểu mẫu</caption>
            <thead>
              <tr>
                <th scope="col">Định dạng</th>
                <th scope="col">Tình trạng</th>
                <th scope="col">Có thể dùng chính thức</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>DOC</td>
                <td>Chưa hỗ trợ</td>
                <td>Không</td>
              </tr>
              <tr>
                <td>DOCX</td>
                <td>Đang chuẩn bị</td>
                <td>Không</td>
              </tr>
              <tr>
                <td>PDF</td>
                <td>Đang chuẩn bị</td>
                <td>Không</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p className="notice notice-warning" role="alert">
          Hệ thống chưa bảo đảm loại bỏ đầy đủ phần hướng dẫn trong tệp mẫu. Không
          sử dụng kết quả làm văn bản chính thức.
        </p>
      </SectionCard>
    </ModulePage>
  );
}

export function FormDetailFeature({ formId }: { formId: string }) {
  return (
    <div className="page-stack">
      <PageHeader
        title="Chi tiết biểu mẫu"
        description="Xem nguồn thông tin và các trường cần chuẩn bị cho biểu mẫu."
        action={<PrimaryAction label="Tạo biểu mẫu" disabled />}
      />
      <div className="context-row">
        <span>Mã tham chiếu: {formId}</span>
        <StatusBadge status="APPROVED" />
      </div>

      <SectionCard
        title="Nguồn thông tin"
        description="Chỉ hồ sơ đã phê duyệt mới được dùng để chuẩn bị biểu mẫu."
      >
        <dl className="definition-grid">
          <div>
            <dt>Trạng thái nguồn</dt>
            <dd>Đã phê duyệt</dd>
          </div>
          <div>
            <dt>Phiên bản biểu mẫu</dt>
            <dd>Bản minh họa 1.0</dd>
          </div>
          <div>
            <dt>Tình trạng sử dụng</dt>
            <dd>Chưa thể tạo văn bản chính thức</dd>
          </div>
        </dl>
      </SectionCard>

      <SectionCard
        title="Thiết lập đầu ra"
        description="Chọn định dạng và bổ sung trường cần nhập tay."
      >
        <div className="form-grid">
          <label htmlFor="form-output-format">Định dạng đầu ra</label>
          <select id="form-output-format" defaultValue="docx" disabled>
            <option value="docx">DOCX — đang chuẩn bị</option>
            <option value="pdf">PDF — đang chuẩn bị</option>
            <option value="doc">DOC — chưa hỗ trợ</option>
          </select>

          <label htmlFor="manual-signing-location">
            Địa điểm ký — trường cần nhập tay
          </label>
          <input
            id="manual-signing-location"
            type="text"
            placeholder="Nhập khi chức năng được mở"
            disabled
          />
        </div>
        <p className="notice notice-warning" role="alert">
          Không sử dụng kết quả làm văn bản chính thức khi chức năng vẫn đang
          được chuẩn bị.
        </p>
      </SectionCard>
    </div>
  );
}
