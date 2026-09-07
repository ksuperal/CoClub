"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { campaignTypeLabel, STATUS_LABELS } from "@/lib/constants";
import { supabase } from "@/lib/supabaseClient";

type CampaignListItem = {
  id: string;
  brand_name: string | null;
  product_id: string | null;
  campaign_type: string;
  brief: string;
  status: string;
  thumbnail_url: string | null;
  created_at: string;
};

function statusHref(campaign: CampaignListItem): string {
  // Variants are waiting on the user's review/approval — send them straight there.
  // Everything else (still generating, posted, completed, failed) has more to see
  // on the status page.
  return campaign.status === "awaiting_approval"
    ? `/campaign/${campaign.id}/variants`
    : `/campaign/${campaign.id}`;
}

export default function HomePage() {
  const router = useRouter();
  const [campaigns, setCampaigns] = useState<CampaignListItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .listCampaigns()
      .then(setCampaigns)
      .catch((err) => setError(err.message ?? String(err)));
  }, []);

  async function handleSignOut() {
    await supabase.auth.signOut();
    router.replace("/login");
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold">Your campaigns</h1>
        <div className="flex items-center gap-3">
          <Link href="/intake" className="bg-black text-white rounded px-3 py-2 text-sm">
            + New campaign
          </Link>
          <button onClick={handleSignOut} className="text-sm text-neutral-500">
            Sign out
          </button>
        </div>
      </div>

      {error && <p className="text-red-600 text-sm mb-4">{error}</p>}

      {campaigns === null && !error && <p className="text-sm text-neutral-500">Loading…</p>}

      {campaigns?.length === 0 && (
        <div className="border border-dashed rounded p-8 text-center">
          <p className="text-sm text-neutral-500 mb-4">No campaigns yet.</p>
          <Link href="/intake" className="bg-black text-white rounded px-3 py-2 text-sm">
            Create your first campaign
          </Link>
        </div>
      )}

      <div className="flex flex-col gap-3">
        {campaigns?.map((c) => (
          <Link
            key={c.id}
            href={statusHref(c)}
            className="border rounded p-3 flex gap-3 items-center hover:bg-neutral-50"
          >
            {c.thumbnail_url ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={c.thumbnail_url} alt="" className="w-16 h-16 object-cover rounded flex-shrink-0" />
            ) : (
              <div className="w-16 h-16 rounded bg-neutral-100 flex-shrink-0" />
            )}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="font-medium truncate">{c.brand_name ?? "Untitled brand"}</span>
                <span className="text-xs text-neutral-400">· {campaignTypeLabel(c.campaign_type)}</span>
              </div>
              <p className="text-sm text-neutral-500 truncate">{c.brief}</p>
              <p className="text-xs text-neutral-400">{new Date(c.created_at).toLocaleString()}</p>
            </div>
            <span
              className={`text-xs rounded-full px-2 py-1 flex-shrink-0 ${
                c.status === "failed"
                  ? "bg-red-100 text-red-700"
                  : c.status === "completed"
                    ? "bg-green-100 text-green-700"
                    : "bg-neutral-100 text-neutral-600"
              }`}
            >
              {STATUS_LABELS[c.status] ?? c.status}
            </span>
          </Link>
        ))}
      </div>
    </div>
  );
}
