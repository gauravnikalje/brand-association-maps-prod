import { NextRequest, NextResponse } from "next/server";

/**
 * Proxy: GET /api/download/[run_id]
 *
 * Forwards the download request to the Railway FastAPI backend and
 * streams the Excel file back to the browser.
 */
export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ run_id: string }> }
) {
  const { run_id } = await params;
  const backendUrl = process.env.API_URL;

  if (!backendUrl) {
    return NextResponse.json(
      { error: "Backend API URL is not configured." },
      { status: 503 }
    );
  }

  try {
    const backendRes = await fetch(`${backendUrl}/api/download/${run_id}`);

    if (!backendRes.ok) {
      return NextResponse.json(
        { error: "File not found on backend." },
        { status: backendRes.status }
      );
    }

    const blob = await backendRes.blob();
    const headers = new Headers();
    headers.set(
      "Content-Disposition",
      backendRes.headers.get("Content-Disposition") ||
        `attachment; filename=BAM_output.xlsx`
    );
    headers.set(
      "Content-Type",
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    );

    return new NextResponse(blob, { status: 200, headers });
  } catch (err: any) {
    console.error("[proxy /api/download]", err);
    return NextResponse.json(
      { error: err.message || "Failed to download from backend." },
      { status: 502 }
    );
  }
}
