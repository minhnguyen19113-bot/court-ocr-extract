export interface SchemaColumn {
  key: string;
  label: string;
  export_order: number;
  required: boolean | null;
  review_rule: string;
}

export interface SchemaContract {
  schema_id: string;
  schema_version: string;
  case_domain: string;
  sheet_name: string;
  columns: SchemaColumn[];
}
