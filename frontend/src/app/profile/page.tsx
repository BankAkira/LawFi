"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";

export default function ProfilePage() {
  const { user, loading, logout } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) router.push("/login");
  }, [user, loading, router]);

  if (loading || !user) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/3" />
          <div className="h-4 bg-gray-200 rounded w-full" />
        </div>
      </div>
    );
  }

  const tierColors: Record<string, string> = {
    free: "bg-gray-100 text-gray-700",
    pro: "bg-indigo-100 text-indigo-700",
    enterprise: "bg-amber-100 text-amber-700",
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">โปรไฟล์</h1>

      <div className="bg-white rounded-2xl border border-gray-200 p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold">{user.name}</h2>
            <p className="text-gray-500">{user.email}</p>
          </div>
          <span
            className={`text-sm px-3 py-1 rounded-full font-medium ${tierColors[user.subscription_tier] || tierColors.free}`}
          >
            {user.subscription_tier.toUpperCase()}
          </span>
        </div>

        <div className="border-t pt-4 grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-gray-500">ผู้ให้บริการเข้าสู่ระบบ</p>
            <p className="font-medium">
              {user.auth_provider === "google" ? "Google" : "อีเมล/รหัสผ่าน"}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500">สมาชิกตั้งแต่</p>
            <p className="font-medium">
              {new Date(user.created_at).toLocaleDateString("th-TH", {
                year: "numeric",
                month: "long",
                day: "numeric",
              })}
            </p>
          </div>
        </div>

        <div className="border-t pt-4 flex gap-4">
          <Link
            href="/bookmarks"
            className="text-sm text-indigo-600 hover:underline"
          >
            บุ๊คมาร์คของฉัน
          </Link>
          <Link
            href="/history"
            className="text-sm text-indigo-600 hover:underline"
          >
            ประวัติการค้นหา
          </Link>
        </div>

        <div className="border-t pt-4">
          <button
            onClick={() => {
              logout();
              router.push("/");
            }}
            className="text-sm text-red-500 hover:text-red-700"
          >
            ออกจากระบบ
          </button>
        </div>
      </div>
    </div>
  );
}
