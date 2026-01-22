import { NextResponse } from 'next/server'

const TIMEOUT_MS = 1500

export async function POST(request: Request) {
  const secret = process.env.TELEGRAM_WEBHOOK_SECRET
  if (secret) {
    const header = request.headers.get('x-tg-secret')
    if (header !== secret) {
      return NextResponse.json({ status: 'unauthorized' }, { status: 401 })
    }
  }

  let payload: unknown
  try {
    payload = await request.json()
  } catch (error) {
    console.error('invalid telegram payload', error)
    return NextResponse.json({ status: 'ok' })
  }

  const workerUrl = process.env.RENDER_WORKER_URL
  const workerToken = process.env.WORKER_AUTH_TOKEN
  if (!workerUrl || !workerToken) {
    console.error('worker configuration is missing')
    return NextResponse.json({ status: 'ok' })
  }

  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), TIMEOUT_MS)
  const ingestUrl = `${workerUrl.replace(/\/$/, '')}/ingest`

  try {
    await fetch(ingestUrl, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${workerToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload),
      signal: controller.signal
    })
  } catch (error) {
    console.error('failed to forward update to worker', error)
  } finally {
    clearTimeout(timeoutId)
  }

  return NextResponse.json({ status: 'ok' })
}
