import { NextResponse } from 'next/server'

const WORKER_ENDPOINT = '/ingest'

function getHeader(request: Request, name: string): string | null {
  const value = request.headers.get(name)
  return value ?? null
}

export async function POST(request: Request) {
  const secret = process.env.TELEGRAM_WEBHOOK_SECRET
  if (secret) {
    const provided = getHeader(request, 'X-TG-SECRET')
    if (!provided || provided !== secret) {
      return NextResponse.json({ status: 'unauthorized' }, { status: 401 })
    }
  }

  const workerUrl = process.env.RENDER_WORKER_URL
  const workerToken = process.env.WORKER_AUTH_TOKEN
  if (!workerUrl || !workerToken) {
    console.error('Missing worker configuration')
    return NextResponse.json({ status: 'misconfigured' }, { status: 500 })
  }

  let payload: unknown
  try {
    payload = await request.json()
  } catch (error) {
    console.error('Invalid JSON payload', error)
    return NextResponse.json({ status: 'invalid_json' }, { status: 400 })
  }

  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), 1500)

  try {
    await fetch(`${workerUrl}${WORKER_ENDPOINT}`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${workerToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
      signal: controller.signal,
    })
  } catch (error) {
    console.error('Worker ingest failed', error)
  } finally {
    clearTimeout(timeout)
  }

  return NextResponse.json({ status: 'ok' }, { status: 200 })
}
