"use client";

import Link from "next/link";
import { useAuth } from "@/context/AuthContext";

export default function Navbar() {
  const { user, logout, loading } = useAuth();

  return (
    <nav className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          <div className="flex items-center gap-8">
            <Link href="/" className="text-xl font-bold text-indigo-600">
              LawFi
            </Link>
            <div className="hidden sm:flex gap-6">
              <Link
                href="/"
                className="text-gray-600 hover:text-gray-900 text-sm font-medium"
              >
                ค้นหา
              </Link>
              {user && (
                <Link
                  href="/bookmarks"
                  className="text-gray-600 hover:text-gray-900 text-sm font-medium"
                >
                  บุ๊คมาร์ค
                </Link>
              )}
            </div>
          </div>

          <div className="flex items-center gap-4">
            {loading ? (
              <div className="h-8 w-20 bg-gray-200 animate-pulse rounded" />
            ) : user ? (
              <div className="flex items-center gap-4">
                <span className="text-sm text-gray-600">{user.name}</span>
                <span className="text-xs px-2 py-1 rounded-full bg-indigo-100 text-indigo-700 font-medium">
                  {user.subscription_tier.toUpperCase()}
                </span>
                <button
                  onClick={logout}
                  className="text-sm text-gray-500 hover:text-gray-700"
                >
                  ออกจากระบบ
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-3">
                <Link
                  href="/login"
                  className="text-sm text-gray-600 hover:text-gray-900"
                >
                  เข้าสู่ระบบ
                </Link>
                <Link
                  href="/register"
                  className="text-sm bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700"
                >
                  สมัครสมาชิก
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
