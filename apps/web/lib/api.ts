import { supabase } from "./supabaseClient";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function authHeaders(): Promise<Record<string, string>> {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = {
    "Content-Type": "application/json",
    ...(await authHeaders()),
    ...(options.headers || {}),
  };
  const res = await fetch(`${API_URL}${path}`, { ...options, headers });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${body}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

async function uploadFile(endpoint: string, file: File): Promise<{ path: string }> {
  const form = new FormData();
  form.append("file", file);
  const headers = await authHeaders();
  const res = await fetch(`${API_URL}${endpoint}`, { method: "POST", headers, body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export const api = {
  uploadBrandAsset: (file: File) => uploadFile("/assets/brand-guideline", file),

  createBrand: (body: { name: string; guideline_raw_text: string; guideline_asset_paths: string[] }) =>
    request<any>("/brands", { method: "POST", body: JSON.stringify(body) }),

  listBrands: () => request<any[]>("/brands"),

  uploadProductAsset: (file: File) => uploadFile("/assets/product", file),

  createProduct: (body: {
    brand_id: string;
    name: string;
    description_text?: string;
    asset_paths: string[];
  }) => request<any>("/products", { method: "POST", body: JSON.stringify(body) }),

  listProducts: (brand_id: string) => request<any[]>(`/products?brand_id=${brand_id}`),

  createCampaign: (body: {
    brand_id: string;
    product_id?: string | null;
    campaign_type: string;
    brief: string;
    variant_count: number;
  }) => request<any>("/campaigns", { method: "POST", body: JSON.stringify(body) }),

  getCampaign: (id: string) => request<any>(`/campaigns/${id}`),

  generateVariants: (id: string) => request<any[]>(`/campaigns/${id}/generate-variants`, { method: "POST" }),

  listVariants: (id: string) => request<any[]>(`/campaigns/${id}/variants`),

  generateCopy: (id: string) => request<any[]>(`/campaigns/${id}/generate-copy`, { method: "POST" }),

  listCaptions: (id: string) => request<any[]>(`/campaigns/${id}/captions`),

  approve: (id: string, approved_variant_ids: string[]) =>
    request(`/campaigns/${id}/approve`, { method: "POST", body: JSON.stringify({ approved_variant_ids }) }),

  post: (id: string) => request<any[]>(`/campaigns/${id}/post`, { method: "POST" }),

  getReport: (id: string) => request<any>(`/campaigns/${id}/report`),

  runReportNow: (id: string) => request<any>(`/campaigns/${id}/report/run-now`, { method: "POST" }),
};
