"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import type { SearchHistoryItem } from "@/types";
import api from "@/services/api";
import { useAuth } from "@/context/AuthContext";

export default function HistoryPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [history, setHistory] = useState<SearchHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      router.push("/login");
      return;
    }

    const fetchHistory = async () => {
      try {
        const data = await api.getHistory();
        setHistory(data);
      } catch {
        // Ignore
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, [user, authLoading, router]);

  if (authLoading || loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/4" />
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-16 bg-gray-200 rounded" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">
        ประวัติการค้นหา
      </h1>

      {history.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <p className="mb-4">ยังไม่มีประวัติการค้นหา</p>
          <Link
            href="/"
            className="text-indigo-600 hover:underline font-medium"
          >
            เริ่มค้นหาฎีกา
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {history.map((item) => {
            const filters = item.filters_applied
              ? JSON.parse(item.filters_applied)
              : {};
            const params = new URLSearchParams({ q: item.query });
            if (filters.case_type) params.set("case_type", filters.case_type);
            if (filters.year_from)
              params.set("year_from", String(filters.year_from));
            if (filters.year_to)
              params.set("year_to", String(filters.year_to));

            return (
              <Link
                key={item.id}
                href={`/search?${params.toString()}`}
                className="block bg-white p-4 rounded-xl border border-gray-200 hover:border-indigo-300 hover:shadow-sm transition"
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium text-gray-900">
                    {item.query}
                  </span>
                  <span className="text-xs text-gray-400">
                    {new Date(item.created_at).toLocaleString("th-TH")}
                  </span>
                </div>
                <div className="flex gap-2 mt-1">
                  <span className="text-xs text-gray-500">
                    {item.results_count} ผลลัพธ์
                  </span>
                  {Object.keys(filters).length > 0 && (
                    <span className="text-xs text-indigo-500">
                      +{Object.keys(filters).length} ตัวกรอง
                    </span>
                  )}
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
