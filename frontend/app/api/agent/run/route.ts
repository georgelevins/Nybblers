import { NextRequest, NextResponse } from "next/server";

const BACKEND_BASE =
  (process.env.API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "").trim() ||
  "http://localhost:8000";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const res = await fetch(`${BACKEND_BASE}/agent/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const raw = await res.text();
    let data: unknown;
    try {
      data = raw ? JSON.parse(raw) : {};
    } catch {
      return NextResponse.json(
        { detail: res.ok ? "Invalid response from API" : raw?.slice(0, 200) || res.statusText },
        { status: res.ok ? 502 : res.status }
      );
    }
    if (!res.ok) {
      return NextResponse.json(
        { detail: (data as { detail?: string }).detail ?? res.statusText },
        { status: res.status }
      );
    }
    return NextResponse.json(data);
  } catch (err) {
    const message =
      err instanceof Error ? err.message : "Backend request failed";
    return NextResponse.json(
      { detail: message },
      { status: 502 }
    );
  }
}
