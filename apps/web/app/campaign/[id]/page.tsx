"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";

export default function CampaignStatusPage() {
  const { id } = useParams<{ id: string }>();
  const [campaign, setCampaign] = useState<any>(null);
  const [report, setReport] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [runningReport, setRunningReport] = useState(false);

  async function refresh() {
    try {
      const c = await api.getCampaign(id);
      setCampaign(c);
      const r = await api.getReport(id);
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
      <h1 className="text-xl font-semibold mb-2">Campaign status</h1>
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
        <div className="border rounded p-4 mt-4">
          <h2 className="font-medium mb-2">Feedback report</h2>
          <p className="text-sm whitespace-pre-wrap">{report.summary_text}</p>
        </div>
      )}
    </div>
  );
}
