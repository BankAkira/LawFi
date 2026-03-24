"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import type { RulingListItem } from "@/types";
import api from "@/services/api";
import { useAuth } from "@/context/AuthContext";

export default function BookmarksPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [bookmarks, setBookmarks] = useState<RulingListItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      router.push("/login");
      return;
    }

    const fetchBookmarks = async () => {
      try {
        const data = await api.getBookmarks();
        setBookmarks(data);
      } catch {
        // Ignore errors
      } finally {
        setLoading(false);
      }
    };

    fetchBookmarks();
  }, [user, authLoading, router]);

  const handleRemove = async (rulingId: number) => {
    try {
      await api.removeBookmark(rulingId);
      setBookmarks(bookmarks.filter((b) => b.id !== rulingId));
    } catch {
      // Ignore errors
    }
  };

  if (authLoading || loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/4" />
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-24 bg-gray-200 rounded" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">
        บุ๊คมาร์คของฉัน
      </h1>

      {bookmarks.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <p className="mb-4">ยังไม่มีบุ๊คมาร์ค</p>
          <Link
            href="/"
            className="text-indigo-600 hover:underline font-medium"
          >
            ค้นหาฎีกา
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {bookmarks.map((ruling) => (
            <div
              key={ruling.id}
              className="bg-white p-6 rounded-xl border border-gray-200 flex items-start justify-between"
            >
              <Link
                href={`/ruling/${ruling.id}`}
                className="flex-1 hover:text-indigo-600"
              >
                <h2 className="text-lg font-semibold">
                  ฎีกาที่ {ruling.ruling_number}
                </h2>
                <div className="flex gap-2 mt-1">
                  {ruling.case_type && (
                    <span className="text-xs px-2 py-1 rounded-full bg-blue-100 text-blue-700">
                      {ruling.case_type}
                    </span>
                  )}
                  <span className="text-xs px-2 py-1 rounded-full bg-gray-100 text-gray-600">
                    พ.ศ. {ruling.year}
                  </span>
                </div>
                {ruling.summary && (
                  <p className="mt-2 text-sm text-gray-600 line-clamp-2">
                    {ruling.summary}
                  </p>
                )}
              </Link>
              <button
                onClick={() => handleRemove(ruling.id)}
                className="ml-4 text-sm text-red-500 hover:text-red-700"
              >
                ลบ
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
