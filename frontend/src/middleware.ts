import { NextRequest, NextResponse } from "next/server";

const PROTECTED_PATHS = ["/bookmarks", "/history", "/profile"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Check if the path is protected
  const isProtected = PROTECTED_PATHS.some((p) => pathname.startsWith(p));
  if (!isProtected) return NextResponse.next();

  // Check for access token in cookies or authorization header
  // Note: localStorage is not available in middleware (server-side),
  // so we check for a cookie that the frontend sets
  const token = request.cookies.get("access_token")?.value;

  if (!token) {
    // Redirect to login with return URL
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("returnTo", pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/bookmarks/:path*", "/history/:path*", "/profile/:path*"],
};
