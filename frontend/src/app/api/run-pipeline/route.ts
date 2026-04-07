import { NextRequest, NextResponse } from "next/server";

/**
 * Proxy: POST /api/run-pipeline
 *
 * Receives the file upload from the browser and forwards it to the
 * Railway FastAPI backend. The Railway URL is kept server-side in
 * the `API_URL` environment variable (no NEXT_PUBLIC_ prefix needed).
 *
 * Set in Vercel → Settings → Environment Variables:
 *   API_URL = https://your-railway-app.up.railway.app
 */
export async function POST(req: NextRequest) {
  let backendUrl = process.env.API_URL;

  if (!backendUrl) {
    return NextResponse.json(
      { error: "Backend API URL is not configured. Set the API_URL environment variable." },
      { status: 503 }
    );
  }

  // Ensure the URL has a protocol, otherwise fetch() will fail to parse it
  if (!backendUrl.startsWith("http://") && !backendUrl.startsWith("https://")) {
    backendUrl = `https://${backendUrl}`;
  }

  try {
    // Forward the raw multipart FormData directly to the Railway backend
    const formData = await req.formData();

    const backendRes = await fetch(`${backendUrl}/api/run-pipeline`, {
      method: "POST",
      body: formData,
      // Do NOT set Content-Type here; let fetch set it automatically
      // with the correct multipart boundary.
    });

    const data = await backendRes.json();

    return NextResponse.json(data, { status: backendRes.status });
  } catch (err: any) {
    console.error("[proxy /api/run-pipeline]", err);
    return NextResponse.json(
      { error: err.message || "Failed to reach the pipeline backend." },
      { status: 502 }
    );
  }
}
