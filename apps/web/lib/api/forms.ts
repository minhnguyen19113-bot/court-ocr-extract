import { getJson } from "@/lib/api/client";

export type FormCapabilityStatus =
  | "NOT_IMPLEMENTED"
  | "DECLARED"
  | "AVAILABLE"
  | "UNAVAILABLE";

export interface FormFormatCapability {
  capability_status: FormCapabilityStatus;
  adapter_implemented: boolean;
  output_format_declared: boolean;
}

export interface FormCapabilities {
  contract_supported: boolean;
  official_generation_available: boolean;
  draft_preview_available: boolean;
  source_states_allowed_for_official_generation: string[];
  formats: Record<string, FormFormatCapability>;
}

export function getFormCapabilities(): Promise<FormCapabilities> {
  return getJson<FormCapabilities>("/forms/capabilities");
}
