"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";

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
  const [error, setError] = useState<string | null>(null);
  const [runningReport, setRunningReport] = useState(false);

  async function refresh() {
    try {
      const c = await api.getCampaign(id);
      setCampaign(c);
      const [v, cap, r] = await Promise.all([api.listVariants(id), api.listCaptions(id), api.getReport(id)]);
      setVariants(v);
      setCaptions(cap);
      setReport(r);
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

  if (!campaign) return <p className="text-sm text-neutral-500">Loading…</p>;

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
          <h2 className="font-medium mb-3">Variants & captions</h2>
          <div className="grid grid-cols-2 gap-4">
            {variants.map((v) => {
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
