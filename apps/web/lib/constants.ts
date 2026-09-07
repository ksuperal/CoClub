export const CAMPAIGN_TYPES: [string, string][] = [
  ["product_launch", "Product launch"],
  ["event_announcement", "Event announcement"],
  ["promo_offer", "Promo / offer"],
  ["brand_awareness", "Brand awareness"],
  ["other", "Other"],
];

export function campaignTypeLabel(value: string): string {
  return CAMPAIGN_TYPES.find(([v]) => v === value)?.[1] ?? value;
}

export const STATUS_LABELS: Record<string, string> = {
  draft: "Draft",
  generating_variants: "Generating variants…",
  awaiting_approval: "Awaiting your review",
  approved: "Approved",
  posting: "Posting…",
  posted: "Posted",
  awaiting_feedback: "Awaiting feedback",
  completed: "Completed",
  failed: "Failed",
};
