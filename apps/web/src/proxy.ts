import type { NextRequest } from "next/server";
import { secureProxy } from "./server/http-security";

export function proxy(request: NextRequest) { return secureProxy(request); }
export const config = { matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"] };
