import { NextRequest, NextResponse } from "next/server";
import { callbackHandler, privateResponse } from "@/server/auth/handlers";
import { authService } from "@/server/auth/runtime";

export const runtime = "nodejs";
export async function GET(request: NextRequest): Promise<NextResponse> {
  try { return await callbackHandler(request, authService()); }
  catch { return privateResponse(new NextResponse(null, { status: 503 })); }
}
