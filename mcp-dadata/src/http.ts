export class HttpError extends Error {
  constructor(
    message: string,
    public status: number,
    public bodyText?: string,
  ) {
    super(message);
  }
}

export async function postJson<T>(
  url: string,
  body: unknown,
  headers: Record<string, string>,
  timeoutMs: number,
): Promise<T> {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), timeoutMs);

  try {
    const res = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        ...headers,
      },
      body: JSON.stringify(body),
      signal: ctrl.signal,
    });

    const text = await res.text();
    if (!res.ok) throw new HttpError(`HTTP ${res.status} for ${url}`, res.status, text);

    try {
      return JSON.parse(text) as T;
    } catch (e) {
      throw new HttpError(
        `Failed to parse JSON response from ${url}: ${e instanceof Error ? e.message : String(e)}`,
        res.status,
        text,
      );
    }
  } finally {
    clearTimeout(t);
  }
}
