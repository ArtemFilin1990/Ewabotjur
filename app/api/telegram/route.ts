import { NextRequest, NextResponse } from 'next/server'

const JSON_HEADERS = { 'Content-Type': 'application/json' }

export async function POST(request: NextRequest) {
  const secret = process.env.TELEGRAM_WEBHOOK_SECRET
  if (secret) {
    const providedSecret =
      request.headers.get('x-tg-secret') ||
      request.headers.get('x-telegram-bot-api-secret-token')
    if (providedSecret !== secret) {
      return NextResponse.json({ status: 'unauthorized' }, { status: 401 })
    }
  }

  const workerUrl = process.env.RENDER_WORKER_URL
  const workerToken = process.env.WORKER_AUTH_TOKEN
  if (!workerUrl || !workerToken) {
    console.error('Missing RENDER_WORKER_URL or WORKER_AUTH_TOKEN')
    return NextResponse.json({ status: 'ok' }, { status: 200, headers: JSON_HEADERS })
  }

  let payload: unknown
  try {
    payload = await request.json()
  } catch (error) {
    console.error('Failed to parse Telegram update', error)
    return NextResponse.json({ status: 'ok' }, { status: 200, headers: JSON_HEADERS })
  }

  try {
    await fetch(`${workerUrl}/ingest`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${workerToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    })
  } catch (error) {
    console.error('Failed to forward update to worker', error)
  }

  return NextResponse.json({ status: 'ok' }, { status: 200, headers: JSON_HEADERS })
}
