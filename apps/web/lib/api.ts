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

// Uploads each file one at a time (the backend endpoint only takes one file per
// request) and collects the resulting storage paths, in order.
async function uploadFiles(endpoint: string, files: File[]): Promise<string[]> {
  const paths: string[] = [];
  for (const file of files) {
    const { path } = await uploadFile(endpoint, file);
    paths.push(path);
  }
  return paths;
}

export const api = {
  uploadBrandAssets: (files: File[]) => uploadFiles("/assets/brand-guideline", files),

  createBrand: (body: { name: string; guideline_raw_text: string; guideline_asset_paths: string[] }) =>
    request<any>("/brands", { method: "POST", body: JSON.stringify(body) }),

  listBrands: () => request<any[]>("/brands"),

  uploadProductAssets: (files: File[]) => uploadFiles("/assets/product", files),

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
    media_type: "image" | "video";
    include_voiceover?: boolean;
    include_music?: boolean;
  }) => request<any>("/campaigns", { method: "POST", body: JSON.stringify(body) }),

  listCampaigns: () => request<any[]>("/campaigns"),

  getCampaign: (id: string) => request<any>(`/campaigns/${id}`),

  ideate: (id: string) => request<any[]>(`/campaigns/${id}/ideate`, { method: "POST" }),

  updateVariantPrompt: (
    campaignId: string,
    variantId: string,
    body: { image_prompt: string; motion_prompt?: string; voiceover_script?: string; voice_instructions?: string; music_prompt?: string }
  ) =>
    request<any>(`/campaigns/${campaignId}/variants/${variantId}/prompt`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),

  generateMedia: (id: string, variant_ids: string[]) =>
    request<any[]>(`/campaigns/${id}/generate-media`, { method: "POST", body: JSON.stringify({ variant_ids }) }),

  listVariants: (id: string) => request<any[]>(`/campaigns/${id}/variants`),

  generateCopy: (id: string) => request<any[]>(`/campaigns/${id}/generate-copy`, { method: "POST" }),

  listCaptions: (id: string) => request<any[]>(`/campaigns/${id}/captions`),

  updateCaption: (campaignId: string, captionId: string, body: { caption_text: string; hashtags: string[] }) =>
    request<any>(`/campaigns/${campaignId}/captions/${captionId}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),

  approve: (id: string, approved_variant_ids: string[]) =>
    request(`/campaigns/${id}/approve`, { method: "POST", body: JSON.stringify({ approved_variant_ids }) }),

  post: (id: string) => request<any[]>(`/campaigns/${id}/post`, { method: "POST" }),

  getReport: (id: string) => request<any>(`/campaigns/${id}/report`),

  runReportNow: (id: string) => request<any>(`/campaigns/${id}/report/run-now`, { method: "POST" }),

  refreshMetrics: (id: string) => request<any[]>(`/campaigns/${id}/metrics/refresh`, { method: "POST" }),

  getMetricsHistory: (id: string) => request<any[]>(`/campaigns/${id}/metrics/history`),

  listSocialAccounts: () => request<any[]>("/social/accounts"),

  connectSocial: (platform: "facebook" | "tiktok") =>
    request<{ authorize_url: string }>(`/social/connect/${platform}`, { method: "POST" }),

  disconnectSocial: (id: string) => request(`/social/accounts/${id}`, { method: "DELETE" }),

  getPostingTimeRecommendation: (platform: string) =>
    request<{ platform: string; recommended_hour_utc: number | null; data_points: number; confidence: string }>(
      `/social/posting-time-recommendation/${platform}`
    ),
};
