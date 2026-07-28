import { afterEach, describe, expect, it, vi } from "vitest";

import { getSystemSchema } from "../lib/api/system";
import "./setup";

describe("getSystemSchema", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("loads the canonical schema through the versioned API client", async () => {
    const response = {
      schema_id: "synthetic.schema",
      schema_version: "1.0.0",
      case_domain: "criminal",
      columns: [
        {
          key: "SYNTHETIC_FIELD",
          label: "Trường tổng hợp",
          export_order: 1,
          required: null,
          review_rule: "DOMAIN_POLICY",
        },
      ],
    };
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => response,
    });
    vi.stubGlobal("fetch", fetchMock);

    await expect(getSystemSchema()).resolves.toEqual(response);
    expect(String(fetchMock.mock.calls[0][0])).toMatch(
      /\/api\/v1\/system\/schema$/,
    );
  });
});
