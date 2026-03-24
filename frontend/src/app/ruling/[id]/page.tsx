"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import type { RulingDetail } from "@/types";
import api from "@/services/api";
import { useAuth } from "@/context/AuthContext";

export default function RulingDetailPage() {
  const params = useParams();
  const { user } = useAuth();
  const [ruling, setRuling] = useState<RulingDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [bookmarked, setBookmarked] = useState(false);

  useEffect(() => {
    const fetchRuling = async () => {
      try {
        const data = await api.getRuling(Number(params.id));
        setRuling(data);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "ไม่สามารถโหลดข้อมูลฎีกาได้"
        );
      } finally {
        setLoading(false);
      }
    };

    if (params.id) fetchRuling();
  }, [params.id]);

  const toggleBookmark = async () => {
    if (!ruling) return;
    try {
      if (bookmarked) {
        await api.removeBookmark(ruling.id);
        setBookmarked(false);
      } else {
        await api.addBookmark(ruling.id);
        setBookmarked(true);
      }
    } catch (err) {
      // Ignore bookmark errors
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/3" />
          <div className="h-4 bg-gray-200 rounded w-full" />
          <div className="h-4 bg-gray-200 rounded w-2/3" />
          <div className="h-32 bg-gray-200 rounded" />
        </div>
      </div>
    );
  }

  if (error || !ruling) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error || "ไม่พบข้อมูลฎีกา"}
        </div>
        <Link href="/" className="mt-4 inline-block text-indigo-600 hover:underline">
          กลับหน้าแรก
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            ฎีกาที่ {ruling.ruling_number}
          </h1>
          <div className="flex gap-2 mt-2">
            {ruling.case_type && (
              <span className="text-sm px-3 py-1 rounded-full bg-blue-100 text-blue-700">
                {ruling.case_type}
              </span>
            )}
            {ruling.result && (
              <span className="text-sm px-3 py-1 rounded-full bg-gray-100 text-gray-600">
                ผล: {ruling.result}
              </span>
            )}
            <span className="text-sm px-3 py-1 rounded-full bg-gray-100 text-gray-600">
              พ.ศ. {ruling.year}
            </span>
            {ruling.division && (
              <span className="text-sm px-3 py-1 rounded-full bg-gray-100 text-gray-600">
                {ruling.division}
              </span>
            )}
          </div>
        </div>
        <div className="flex gap-2">
          {user && (
            <button
              onClick={toggleBookmark}
              className={`px-4 py-2 rounded-lg text-sm border transition ${
                bookmarked
                  ? "bg-indigo-50 border-indigo-300 text-indigo-700"
                  : "border-gray-300 text-gray-600 hover:bg-gray-50"
              }`}
            >
              {bookmarked ? "บันทึกแล้ว" : "บันทึก"}
            </button>
          )}
          {ruling.pdf_url && (
            <a
              href={ruling.pdf_url}
              target="_blank"
              rel="noopener noreferrer"
              className="px-4 py-2 rounded-lg text-sm border border-gray-300 text-gray-600 hover:bg-gray-50"
            >
              ดู PDF
            </a>
          )}
        </div>
      </div>

      {/* Keywords */}
      {ruling.keywords && ruling.keywords.length > 0 && (
        <div className="mb-6 flex flex-wrap gap-2">
          {ruling.keywords.map((kw) => (
            <span
              key={kw}
              className="text-sm px-3 py-1 bg-indigo-50 text-indigo-600 rounded-lg"
            >
              {kw}
            </span>
          ))}
        </div>
      )}

      {/* Summary */}
      {ruling.summary && (
        <Section title="สรุปย่อ" content={ruling.summary} highlight />
      )}

      {/* Facts */}
      {ruling.facts && <Section title="ข้อเท็จจริง" content={ruling.facts} />}

      {/* Issues */}
      {ruling.issues && (
        <Section title="ประเด็นวินิจฉัย" content={ruling.issues} />
      )}

      {/* Judgment */}
      {ruling.judgment && (
        <Section title="คำวินิจฉัย" content={ruling.judgment} />
      )}

      {/* Referenced Sections */}
      {ruling.referenced_sections && ruling.referenced_sections.length > 0 && (
        <div className="mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-2">
            มาตราที่อ้างอิง
          </h2>
          <div className="flex flex-wrap gap-2">
            {ruling.referenced_sections.map((section) => (
              <span
                key={section}
                className="text-sm px-3 py-1 bg-amber-50 text-amber-700 rounded-lg border border-amber-200"
              >
                {section}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Full Text (collapsible) */}
      <details className="mb-6">
        <summary className="cursor-pointer text-lg font-semibold text-gray-900 mb-2 hover:text-indigo-600">
          เนื้อหาเต็ม
        </summary>
        <div className="mt-2 p-4 bg-gray-50 rounded-xl border border-gray-200 whitespace-pre-wrap text-sm text-gray-700 leading-relaxed max-h-[600px] overflow-y-auto">
          {ruling.full_text}
        </div>
      </details>
    </div>
  );
}

function Section({
  title,
  content,
  highlight = false,
}: {
  title: string;
  content: string;
  highlight?: boolean;
}) {
  return (
    <div className="mb-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-2">{title}</h2>
      <div
        className={`p-4 rounded-xl border whitespace-pre-wrap text-sm leading-relaxed ${
          highlight
            ? "bg-indigo-50 border-indigo-200 text-indigo-900"
            : "bg-white border-gray-200 text-gray-700"
        }`}
      >
        {content}
      </div>
    </div>
  );
}
