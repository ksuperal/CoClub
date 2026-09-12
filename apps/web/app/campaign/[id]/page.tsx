"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { downloadImage, variantFilename } from "@/lib/download";
import { DownloadIcon } from "@/components/icons";
import MetricsChart from "./MetricsChart";

type Variant = {
  id: string;
  message_angle: string;
  image_url: string | null;
  quality_check_status: string;
  status: string;
};

type Caption = {
  id: string;
  variant_id: string;
  platform: string;
  caption_text: string;
  hashtags: string[];
};

export default function CampaignStatusPage() {
  const { id } = useParams<{ id: string }>();
  const [campaign, setCampaign] = useState<any>(null);
  const [variants, setVariants] = useState<Variant[]>([]);
  const [captions, setCaptions] = useState<Caption[]>([]);
  const [report, setReport] = useState<any>(null);
  const [metrics, setMetrics] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [runningReport, setRunningReport] = useState(false);
  const [refreshingMetrics, setRefreshingMetrics] = useState(false);
  const [variantFilter, setVariantFilter] = useState<"approved" | "all">("approved");

  async function refresh() {
    try {
      const c = await api.getCampaign(id);
      setCampaign(c);
      const [v, cap, r, m] = await Promise.all([
        api.listVariants(id),
        api.listCaptions(id),
        api.getReport(id),
        api.getMetricsHistory(id),
      ]);
      setVariants(v);
      setCaptions(cap);
      setReport(r);
      setMetrics(m);
    } catch (err: any) {
      setError(err.message ?? String(err));
    }
  }

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 5000);
    return () => clearInterval(interval);
  }, [id]);

  async function handleRunReportNow() {
    setRunningReport(true);
    try {
      const r = await api.runReportNow(id);
      setReport(r);
    } catch (err: any) {
      setError(err.message ?? String(err));
    } finally {
      setRunningReport(false);
    }
  }

  // No LLM call — just fetches live numbers from each connected platform and adds
  // a point to the graph. Safe to click anytime there's a posted post, on a
  // `completed` campaign included (its posts are often still live).
  async function handleRefreshMetrics() {
    setRefreshingMetrics(true);
    setError(null);
    try {
      await api.refreshMetrics(id);
      const m = await api.getMetricsHistory(id);
      setMetrics(m);
    } catch (err: any) {
      setError(err.message ?? String(err));
    } finally {
      setRefreshingMetrics(false);
    }
  }

  if (!campaign) return <p className="text-sm text-neutral-500">Loading…</p>;

  const hasPostedPosts = metrics.length > 0 || ["posted", "awaiting_feedback", "completed"].includes(campaign.status);

  return (
    <div>
      <Link href="/home" className="text-sm text-neutral-500">
        ← Back to campaigns
      </Link>
      <h1 className="text-xl font-semibold mb-2 mt-2">Campaign status</h1>
      <p className="text-sm mb-1">
        Status: <span className="font-medium">{campaign.status}</span>
      </p>
      {campaign.error_message && <p className="text-red-600 text-sm mb-4">{campaign.error_message}</p>}
      {error && <p className="text-red-600 text-sm mb-4">{error}</p>}

      {hasPostedPosts && (
        <div className="border rounded p-4 mt-4 mb-8">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-medium">Engagement over time</h2>
            <button
              onClick={handleRefreshMetrics}
              disabled={refreshingMetrics}
              className="border rounded px-3 py-1.5 text-sm disabled:opacity-50"
            >
              {refreshingMetrics ? "Refreshing…" : "Refresh metrics"}
            </button>
          </div>
          <MetricsChart snapshots={metrics} />
        </div>
      )}

      {campaign.status === "awaiting_feedback" && (
        <button
          onClick={handleRunReportNow}
          disabled={runningReport}
          className="border rounded px-3 py-2 text-sm mb-6 disabled:opacity-50"
        >
          {runningReport ? "Running…" : "Run feedback report now (skip 24hr wait)"}
        </button>
      )}

      {report && (
        <div className="border rounded p-4 mt-4 mb-8">
          <h2 className="font-medium mb-2">Feedback report</h2>
          <p className="text-sm whitespace-pre-wrap">{report.summary_text}</p>
        </div>
      )}

      {variants.length > 0 && (
        <>
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-medium">Variants & captions</h2>
            <div className="flex items-center gap-1 text-xs border rounded p-0.5">
              <button
                onClick={() => setVariantFilter("approved")}
                className={`px-2 py-1 rounded ${variantFilter === "approved" ? "bg-black text-white" : "text-neutral-500"}`}
              >
                Approved
              </button>
              <button
                onClick={() => setVariantFilter("all")}
                className={`px-2 py-1 rounded ${variantFilter === "all" ? "bg-black text-white" : "text-neutral-500"}`}
              >
                All
              </button>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            {variants
              .filter((v) => variantFilter === "all" || v.status === "approved")
              .map((v) => {
              const variantCaptions = captions.filter((c) => c.variant_id === v.id);
              return (
                <div key={v.id} className="border rounded p-3 flex flex-col gap-2">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium">{v.message_angle}</p>
                    <span
                      className={`text-xs rounded-full px-2 py-0.5 flex-shrink-0 ${
                        v.status === "approved"
                          ? "bg-green-100 text-green-700"
                          : v.status === "rejected"
                            ? "bg-neutral-100 text-neutral-500"
                            : "bg-neutral-100 text-neutral-600"
                      }`}
                    >
                      {v.status}
                    </span>
                  </div>
                  {v.image_url && (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={v.image_url} alt={v.message_angle} className="rounded" />
                  )}
                  {v.image_url && (
                    <button
                      onClick={() => downloadImage(v.image_url!, variantFilename(v.message_angle, v.id))}
                      aria-label="Download image"
                      title="Download image"
                      className="self-start p-1.5 rounded-full border border-neutral-200 bg-neutral-50 text-neutral-500 hover:bg-black hover:text-white hover:border-black transition-colors"
                    >
                      <DownloadIcon className="w-4 h-4" />
                    </button>
                  )}
                  {variantCaptions.map((c) => (
                    <div key={c.id} className="text-xs bg-neutral-100 rounded p-2">
                      <span className="font-medium">{c.platform}:</span> {c.caption_text}
                      <div className="text-neutral-500">{c.hashtags.map((h) => `#${h}`).join(" ")}</div>
                    </div>
                  ))}
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
