"use client";

import { useQuery } from "@tanstack/react-query";

import { getSchemaContract } from "@/lib/api/system";

export function SchemaContractPanel() {
  const schemaQuery = useQuery({
    queryKey: ["system", "schema", "criminal.final_excel"],
    queryFn: getSchemaContract
  });

  return (
    <section className="section-card" aria-labelledby="schema-heading">
      <div className="schema-panel-header">
        <div>
          <h2 id="schema-heading">Danh mục trường dữ liệu</h2>
          <p>
            Các trường cần đối chiếu được lấy từ cấu hình dùng chung của hệ thống.
          </p>
        </div>
      </div>

      {schemaQuery.isPending ? (
        <div className="panel-state" role="status">
          Đang tải danh mục trường dữ liệu…
        </div>
      ) : null}

      {schemaQuery.isError ? (
        <div className="panel-state panel-state-error" role="alert">
          Chưa tải được danh mục trường dữ liệu. Vui lòng thử lại sau.
        </div>
      ) : null}

      {schemaQuery.data ? (
        <>
          <div className="schema-table-wrap">
            <table className="schema-table">
              <thead>
                <tr>
                  <th scope="col">Thứ tự</th>
                  <th scope="col">Tên trường</th>
                  <th scope="col">Quy tắc kiểm tra</th>
                  <th scope="col">Bắt buộc</th>
                </tr>
              </thead>
              <tbody>
                {schemaQuery.data.columns.map((column) => (
                  <tr key={column.key}>
                    <td>{column.export_order}</td>
                    <td>{column.label}</td>
                    <td>{column.review_rule}</td>
                    <td>
                      {column.required === true
                        ? "Có"
                        : column.required === false
                          ? "Không"
                          : "Theo nghiệp vụ"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      ) : null}
    </section>
  );
}
