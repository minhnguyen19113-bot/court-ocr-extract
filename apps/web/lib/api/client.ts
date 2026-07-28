const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "/api/v1";

export class ApiClientError extends Error {
  constructor(
    message: string,
    readonly status: number
  ) {
    super(message);
    this.name = "ApiClientError";
  }
}

export async function getJson<T>(
  endpoint: string,
  init: RequestInit = {}
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...init,
    method: "GET",
    headers: {
      Accept: "application/json",
      ...init.headers
    }
  });

  if (!response.ok) {
    throw new ApiClientError(
      `API request failed with status ${response.status}`,
      response.status
    );
  }

  return (await response.json()) as T;
}
