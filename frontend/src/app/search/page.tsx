"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import type { RulingListItem, SearchResponse, CaseType } from "@/types";
import api from "@/services/api";
import { useAuth } from "@/context/AuthContext";

function SearchResults() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { user } = useAuth();

  const query = searchParams.get("q") || "";
  const caseType = searchParams.get("case_type") as CaseType | null;
  const yearFrom = searchParams.get("year_from");
  const yearTo = searchParams.get("year_to");
  const page = parseInt(searchParams.get("page") || "1");

  const [results, setResults] = useState<RulingListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!query) return;

    const doSearch = async () => {
      setLoading(true);
      setError("");
      try {
        const response: SearchResponse = await api.search({
          query,
          case_type: caseType || undefined,
          year_from: yearFrom ? parseInt(yearFrom) : undefined,
          year_to: yearTo ? parseInt(yearTo) : undefined,
          page,
          page_size: 20,
        });
        setResults(response.results);
        setTotal(response.total);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "เกิดข้อผิดพลาดในการค้นหา"
        );
      } finally {
        setLoading(false);
      }
    };

    doSearch();
  }, [query, caseType, yearFrom, yearTo, page]);

  if (!query) {
    router.push("/");
    return null;
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">
          ผลการค้นหา: &ldquo;{query}&rdquo;
        </h1>
        {!loading && (
          <p className="text-sm text-gray-500 mt-1">
            พบ {total} ผลลัพธ์
          </p>
        )}
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      {!user && (
        <div className="mb-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg text-yellow-700">
          กรุณา{" "}
          <Link href="/login" className="underline font-medium">
            เข้าสู่ระบบ
          </Link>{" "}
          เพื่อค้นหา
        </div>
      )}

      {loading ? (
        <div className="space-y-4">
          {[...Array(5)].map((_, i) => (
            <div
              key={i}
              className="bg-white p-6 rounded-xl border border-gray-200 animate-pulse"
            >
              <div className="h-5 bg-gray-200 rounded w-1/3 mb-3" />
              <div className="h-4 bg-gray-200 rounded w-full mb-2" />
              <div className="h-4 bg-gray-200 rounded w-2/3" />
            </div>
          ))}
        </div>
      ) : (
        <div className="space-y-4">
          {results.map((ruling) => (
            <Link
              key={ruling.id}
              href={`/ruling/${ruling.id}`}
              className="block bg-white p-6 rounded-xl border border-gray-200 hover:border-indigo-300 hover:shadow-md transition"
            >
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">
                    ฎีกาที่ {ruling.ruling_number}
                  </h2>
                  <div className="flex gap-2 mt-1">
                    {ruling.case_type && (
                      <span className="text-xs px-2 py-1 rounded-full bg-blue-100 text-blue-700">
                        {ruling.case_type}
                      </span>
                    )}
                    {ruling.result && (
                      <span className="text-xs px-2 py-1 rounded-full bg-gray-100 text-gray-600">
                        {ruling.result}
                      </span>
                    )}
                    <span className="text-xs px-2 py-1 rounded-full bg-gray-100 text-gray-600">
                      พ.ศ. {ruling.year}
                    </span>
                  </div>
                </div>
                {ruling.relevance_score !== null && (
                  <span className="text-xs text-gray-400">
                    {(ruling.relevance_score * 100).toFixed(0)}% ตรง
                  </span>
                )}
              </div>
              {ruling.summary && (
                <p className="mt-3 text-sm text-gray-600 line-clamp-3">
                  {ruling.summary}
                </p>
              )}
              {ruling.keywords && ruling.keywords.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-1">
                  {ruling.keywords.slice(0, 5).map((kw) => (
                    <span
                      key={kw}
                      className="text-xs px-2 py-0.5 bg-indigo-50 text-indigo-600 rounded"
                    >
                      {kw}
                    </span>
                  ))}
                </div>
              )}
            </Link>
          ))}

          {results.length === 0 && !loading && (
            <div className="text-center py-12 text-gray-500">
              ไม่พบผลลัพธ์สำหรับ &ldquo;{query}&rdquo;
            </div>
          )}
        </div>
      )}

      {total > 20 && (
        <div className="mt-8 flex justify-center gap-2">
          {page > 1 && (
            <button
              onClick={() => {
                const params = new URLSearchParams(searchParams.toString());
                params.set("page", String(page - 1));
                router.push(`/search?${params.toString()}`);
              }}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50"
            >
              ก่อนหน้า
            </button>
          )}
          <span className="px-4 py-2 text-sm text-gray-600">
            หน้า {page} จาก {Math.ceil(total / 20)}
          </span>
          {page < Math.ceil(total / 20) && (
            <button
              onClick={() => {
                const params = new URLSearchParams(searchParams.toString());
                params.set("page", String(page + 1));
                router.push(`/search?${params.toString()}`);
              }}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50"
            >
              ถัดไป
            </button>
          )}
        </div>
      )}
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense
      fallback={
        <div className="max-w-4xl mx-auto px-4 py-8">กำลังโหลด...</div>
      }
    >
      <SearchResults />
    </Suspense>
  );
}
