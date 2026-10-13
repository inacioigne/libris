import { NextRequest, NextResponse } from "next/server";
import { loginHandler, privateResponse } from "@/server/auth/handlers";
import { authService } from "@/server/auth/runtime";

export const runtime = "nodejs";
export async function POST(request: NextRequest): Promise<NextResponse> {
  try { return await loginHandler(request, authService()); }
  catch { return privateResponse(new NextResponse(null, { status: 503 })); }
}
