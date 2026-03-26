import type {
  RulingDetail,
  RulingListItem,
  SearchRequest,
  SearchResponse,
  TokenResponse,
  User,
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private getToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("access_token");
  }

  private setTokens(access: string, refresh: string): void {
    localStorage.setItem("access_token", access);
    localStorage.setItem("refresh_token", refresh);
  }

  private clearTokens(): void {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
  }

  private async request<T>(
    path: string,
    options: RequestInit = {}
  ): Promise<T> {
    const token = this.getToken();
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string>),
    };

    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(`${this.baseUrl}${path}`, {
      ...options,
      headers,
    });

    // Handle 401 -- try refresh
    if (response.status === 401 && token) {
      const refreshed = await this.refreshToken();
      if (refreshed) {
        headers["Authorization"] = `Bearer ${this.getToken()}`;
        const retryResponse = await fetch(`${this.baseUrl}${path}`, {
          ...options,
          headers,
        });
        if (!retryResponse.ok) {
          const error = await retryResponse.json().catch(() => ({}));
          throw new Error(error.detail || "คำขอล้มเหลว");
        }
        return retryResponse.json();
      } else {
        this.clearTokens();
        window.location.href = "/login";
        throw new Error("กรุณาเข้าสู่ระบบใหม่");
      }
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || "คำขอล้มเหลว");
    }

    return response.json();
  }

  private async refreshToken(): Promise<boolean> {
    const refreshToken = localStorage.getItem("refresh_token");
    if (!refreshToken) return false;

    try {
      const response = await fetch(`${this.baseUrl}/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (!response.ok) return false;

      const data: TokenResponse = await response.json();
      this.setTokens(data.access_token, data.refresh_token);
      return true;
    } catch {
      return false;
    }
  }

  // --- Auth ---
  async register(
    email: string,
    password: string,
    name: string
  ): Promise<User> {
    return this.request<User>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, name }),
    });
  }

  async login(email: string, password: string): Promise<TokenResponse> {
    const data = await this.request<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    this.setTokens(data.access_token, data.refresh_token);
    return data;
  }

  async googleLogin(idToken: string): Promise<TokenResponse> {
    const data = await this.request<TokenResponse>("/auth/google", {
      method: "POST",
      body: JSON.stringify({ id_token: idToken }),
    });
    this.setTokens(data.access_token, data.refresh_token);
    return data;
  }

  async getMe(): Promise<User> {
    return this.request<User>("/auth/me");
  }

  logout(): void {
    this.clearTokens();
  }

  // --- Search ---
  async search(params: SearchRequest): Promise<SearchResponse> {
    return this.request<SearchResponse>("/search/", {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  async suggest(query: string): Promise<string[]> {
    return this.request<string[]>(`/search/suggest?q=${encodeURIComponent(query)}`);
  }

  // --- Rulings ---
  async getRuling(id: number): Promise<RulingDetail> {
    return this.request<RulingDetail>(`/rulings/${id}`);
  }

  async getRulingByNumber(number: string): Promise<RulingDetail> {
    return this.request<RulingDetail>(
      `/rulings/number/${encodeURIComponent(number)}`
    );
  }

  // --- Bookmarks ---
  async getBookmarks(): Promise<RulingListItem[]> {
    return this.request<RulingListItem[]>("/bookmarks/");
  }

  async addBookmark(rulingId: number): Promise<void> {
    await this.request("/bookmarks/" + rulingId, { method: "POST" });
  }

  async removeBookmark(rulingId: number): Promise<void> {
    await this.request("/bookmarks/" + rulingId, { method: "DELETE" });
  }

  async getBookmarkStatus(rulingId: number): Promise<{ bookmarked: boolean }> {
    return this.request<{ bookmarked: boolean }>(`/bookmarks/${rulingId}/status`);
  }
}

const api = new ApiClient(API_BASE);
export default api;
