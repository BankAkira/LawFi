// Auth types
export interface User {
  id: number;
  email: string;
  name: string;
  auth_provider: "email" | "google" | "line";
  subscription_tier: "free" | "pro" | "enterprise";
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

// Ruling types
export type CaseType =
  | "แพ่ง"
  | "อาญา"
  | "แรงงาน"
  | "ภาษี"
  | "ทรัพย์สินทางปัญญา"
  | "ล้มละลาย"
  | "ปกครอง"
  | "ครอบครัว"
  | "เยาวชน"
  | "สิ่งแวดล้อม"
  | "อื่นๆ";

export type RulingResult =
  | "ยืน"
  | "กลับ"
  | "แก้"
  | "ยกฟ้อง"
  | "ยกอุทธรณ์"
  | "กลับอุทธรณ์"
  | "อื่นๆ";

export interface RulingListItem {
  id: number;
  ruling_number: string;
  year: number;
  case_type: CaseType | null;
  result: RulingResult | null;
  summary: string | null;
  keywords: string[] | null;
  relevance_score: number | null;
}

export interface RulingDetail {
  id: number;
  ruling_number: string;
  year: number;
  date: string | null;
  case_type: CaseType | null;
  division: string | null;
  result: RulingResult | null;
  summary: string | null;
  facts: string | null;
  issues: string | null;
  judgment: string | null;
  full_text: string;
  keywords: string[] | null;
  referenced_sections: string[] | null;
  pdf_url: string | null;
  created_at: string;
}

// Search types
export interface SearchRequest {
  query: string;
  case_type?: CaseType;
  year_from?: number;
  year_to?: number;
  result?: RulingResult;
  keywords?: string[];
  page?: number;
  page_size?: number;
}

export interface SearchResponse {
  results: RulingListItem[];
  total: number;
  page: number;
  page_size: number;
  query: string;
}
