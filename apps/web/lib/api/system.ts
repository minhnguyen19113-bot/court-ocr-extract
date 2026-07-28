import { getJson } from "@/lib/api/client";
import type { SchemaContract } from "@/lib/schema/types";

export function getSchemaContract(): Promise<SchemaContract> {
  return getJson<SchemaContract>("/system/schema");
}

export const getSystemSchema = getSchemaContract;
