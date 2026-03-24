"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import type { CaseType } from "@/types";

const CASE_TYPES: CaseType[] = [
  "แพ่ง",
  "อาญา",
  "แรงงาน",
  "ภาษี",
  "ทรัพย์สินทางปัญญา",
  "ล้มละลาย",
  "ปกครอง",
  "ครอบครัว",
  "เยาวชน",
  "สิ่งแวดล้อม",
];

export default function HomePage() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [showFilters, setShowFilters] = useState(false);
  const [caseType, setCaseType] = useState<CaseType | "">("");
  const [yearFrom, setYearFrom] = useState("");
  const [yearTo, setYearTo] = useState("");

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    const params = new URLSearchParams({ q: query });
    if (caseType) params.set("case_type", caseType);
    if (yearFrom) params.set("year_from", yearFrom);
    if (yearTo) params.set("year_to", yearTo);

    router.push(`/search?${params.toString()}`);
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[calc(100vh-4rem)] px-4">
      <div className="w-full max-w-2xl text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-2">LawFi</h1>
        <p className="text-lg text-gray-500 mb-8">
          ค้นหาคำพิพากษาศาลฎีกาด้วย AI
        </p>

        <form onSubmit={handleSearch} className="w-full">
          <div className="relative">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder='ค้นหาฎีกา เช่น "ละเมิด สัญญาซื้อขาย" หรือเลขฎีกา "1234/2565"'
              className="w-full px-6 py-4 text-lg border border-gray-300 rounded-2xl shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
            <button
              type="submit"
              className="absolute right-3 top-1/2 -translate-y-1/2 bg-indigo-600 text-white px-6 py-2 rounded-xl hover:bg-indigo-700 transition"
            >
              ค้นหา
            </button>
          </div>

          <button
            type="button"
            onClick={() => setShowFilters(!showFilters)}
            className="mt-3 text-sm text-gray-500 hover:text-gray-700"
          >
            {showFilters ? "ซ่อนตัวกรอง" : "ตัวกรองขั้นสูง"}
          </button>

          {showFilters && (
            <div className="mt-4 p-4 bg-white border border-gray-200 rounded-xl grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  ประเภทคดี
                </label>
                <select
                  value={caseType}
                  onChange={(e) => setCaseType(e.target.value as CaseType | "")}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                >
                  <option value="">ทั้งหมด</option>
                  {CASE_TYPES.map((ct) => (
                    <option key={ct} value={ct}>
                      {ct}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  ปี พ.ศ. ตั้งแต่
                </label>
                <input
                  type="number"
                  value={yearFrom}
                  onChange={(e) => setYearFrom(e.target.value)}
                  placeholder="2500"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  ถึงปี พ.ศ.
                </label>
                <input
                  type="number"
                  value={yearTo}
                  onChange={(e) => setYearTo(e.target.value)}
                  placeholder="2568"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                />
              </div>
            </div>
          )}
        </form>

        <div className="mt-12 grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
          {[
            { label: "คำพิพากษาฎีกา", value: "100,000+" },
            { label: "ประเภทคดี", value: "10+" },
            { label: "Hybrid Search", value: "AI + Keyword" },
            { label: "อัปเดต", value: "ต่อเนื่อง" },
          ].map((stat) => (
            <div key={stat.label} className="p-4">
              <div className="text-2xl font-bold text-indigo-600">
                {stat.value}
              </div>
              <div className="text-sm text-gray-500 mt-1">{stat.label}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
