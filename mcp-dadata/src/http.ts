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

    return JSON.parse(text) as T;
  } finally {
    clearTimeout(t);
  }
}
