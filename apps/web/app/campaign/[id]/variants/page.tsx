"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { downloadImage, variantFilename } from "@/lib/download";
import { DownloadIcon } from "@/components/icons";

type Variant = {
  id: string;
  message_angle: string;
  image_url: string | null;
  quality_check_status: string;
  status: string;
  media_type: string;
  video_url: string | null;
  generation_status: string;
  video_gen_error: string | null;
  audio_gen_error: string | null;
};

type Caption = {
  id: string;
  variant_id: string;
  platform: string;
  caption_text: string;
  hashtags: string[];
};

function hashtagsToText(hashtags: string[]): string {
  return hashtags.map((h) => `#${h}`).join(" ");
}

type PostingTimeRecommendation = {
  platform: string;
  recommended_hour_utc: number | null;
  data_points: number;
  confidence: string;
};
type RealPostingTimeRecommendation = PostingTimeRecommendation & { recommended_hour_utc: number };

// e.g. 18 -> "6:00 PM UTC" — explicitly labeled UTC since the recommendation is
// computed in UTC, not the viewer's local time (no brand/account timezone is
// stored anywhere yet — see services/posting_time.py).
function formatHourUtc(hour: number): string {
  const period = hour < 12 ? "AM" : "PM";
  const displayHour = hour % 12 === 0 ? 12 : hour % 12;
  return `${displayHour}:00 ${period} UTC`;
}

// Accepts either "#foo #bar" or "foo, bar" — strips leading #s and splits on
// whitespace/commas, so editors don't have to think about the exact format.
function textToHashtags(text: string): string[] {
  return text
    .split(/[\s,]+/)
    .map((h) => h.replace(/^#/, "").trim())
    .filter(Boolean);
}

function EditableCaption({
  campaignId,
  caption,
  onSaved,
}: {
  campaignId: string;
  caption: Caption;
  onSaved: (updated: Caption) => void;
}) {
  const [captionText, setCaptionText] = useState(caption.caption_text);
  const [hashtagsText, setHashtagsText] = useState(hashtagsToText(caption.hashtags));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const dirty = captionText !== caption.caption_text || hashtagsText !== hashtagsToText(caption.hashtags);

  async function handleSave() {
    setSaving(true);
    setError(null);
    try {
      const updated = await api.updateCaption(campaignId, caption.id, {
        caption_text: captionText,
        hashtags: textToHashtags(hashtagsText),
      });
      onSaved(updated);
    } catch (err: any) {
      setError(err.message ?? String(err));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="text-xs bg-neutral-100 rounded p-2 flex flex-col gap-1">
      <span className="font-medium">{caption.platform}</span>
      <textarea
        value={captionText}
        onChange={(e) => setCaptionText(e.target.value)}
        rows={3}
        className="w-full border rounded p-1 text-xs"
      />
      <input
        value={hashtagsText}
        onChange={(e) => setHashtagsText(e.target.value)}
        placeholder="#hashtags separated by spaces"
        className="w-full border rounded p-1 text-xs text-neutral-500"
      />
      <div className="flex items-center gap-2">
        <button
          onClick={handleSave}
          disabled={!dirty || saving}
          className="border rounded px-2 py-1 text-xs disabled:opacity-50"
        >
          {saving ? "Saving…" : dirty ? "Save" : "Saved"}
        </button>
        {error && <span className="text-red-600">{error}</span>}
      </div>
    </div>
  );
}

export default function VariantsPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [variants, setVariants] = useState<Variant[]>([]);
  const [captions, setCaptions] = useState<Caption[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [step, setStep] = useState<string | null>("Loading…");
  const [error, setError] = useState<string | null>(null);
  const [warningMessage, setWarningMessage] = useState<string | null>(null);
  const [recommendations, setRecommendations] = useState<RealPostingTimeRecommendation[]>([]);

  useEffect(() => {
    (async () => {
      try {
        const campaign = await api.getCampaign(id);
        setWarningMessage(campaign.warning_message ?? null);

        const v = await api.listVariants(id);
        setVariants(v);
        setSelected(
          new Set(
            v
              .filter((x: Variant) => x.quality_check_status === "passed" && x.generation_status === "generated")
              .map((x: Variant) => x.id)
          )
        );

        let c = await api.listCaptions(id);
        if (c.length === 0) {
          setStep("Writing captions & hashtags…");
          await api.generateCopy(id);
          c = await api.listCaptions(id);
        }
        setCaptions(c);
        setStep(null);

        // Best-posting-time: only ever shown if there's real signal — the endpoint
        // itself is gated (services/posting_time.py) behind 10+ real posts on a
        // platform, returning recommended_hour_utc: null below that. A failure here
        // is non-critical (purely informational), so it's swallowed rather than
        // blocking the rest of the review flow.
        try {
          const platforms = [...new Set(c.map((caption: Caption) => caption.platform))];
          const results = await Promise.all(
            platforms.map((p) => api.getPostingTimeRecommendation(p).catch(() => null))
          );
          setRecommendations(
            results.filter(
              (r): r is RealPostingTimeRecommendation => !!r && r.recommended_hour_utc !== null
            )
          );
        } catch {
          // purely informational — never surfaces as a page-level error
        }
      } catch (err: any) {
        setError(err.message ?? String(err));
        setStep(null);
      }
    })();
  }, [id]);

  function toggle(variantId: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(variantId) ? next.delete(variantId) : next.add(variantId);
      return next;
    });
  }

  function handleCaptionSaved(updated: Caption) {
    setCaptions((prev) => prev.map((c) => (c.id === updated.id ? updated : c)));
  }

  async function handleApproveAndPost() {
    setError(null);
    try {
      setStep("Approving…");
      await api.approve(id, Array.from(selected));
      setStep("Posting…");
      await api.post(id);
      router.push(`/campaign/${id}`);
    } catch (err: any) {
      setError(err.message ?? String(err));
      setStep(null);
    }
  }

  return (
    <div>
      <Link href="/home" className="text-sm text-neutral-500">
        ← Back to campaigns
      </Link>
      <h1 className="text-xl font-semibold mb-2 mt-2">Review variants</h1>
      <p className="text-sm text-neutral-500 mb-6">
        Select which variants to approve for posting. Unchecked variants are rejected. Edit
        any caption below before posting — changes save per caption, independently.
      </p>

      {step && <p className="text-sm text-neutral-500 mb-4">{step}</p>}
      {error && <p className="text-red-600 text-sm mb-4">{error}</p>}
      {warningMessage && (
        <p className="text-amber-700 bg-amber-50 border border-amber-200 rounded px-3 py-2 text-sm mb-4">
          Note: {warningMessage}
        </p>
      )}
      {recommendations.length > 0 && (
        <div className="text-blue-700 bg-blue-50 border border-blue-200 rounded px-3 py-2 text-sm mb-4">
          <p className="font-medium mb-1">Recommended posting time</p>
          {recommendations.map((r) => (
            <p key={r.platform}>
              {r.platform}: {formatHourUtc(r.recommended_hour_utc)} (based on {r.confidence} confidence from your
              past posts)
            </p>
          ))}
        </div>
      )}

      <div className="grid grid-cols-2 gap-4 mb-8">
        {variants.map((v) => {
          const variantCaptions = captions.filter((c) => c.variant_id === v.id);
          return (
            <div key={v.id} className="border rounded p-3 flex flex-col gap-2">
              <label className="flex items-center gap-2 text-sm font-medium">
                <input
                  type="checkbox"
                  checked={selected.has(v.id)}
                  disabled={v.generation_status !== "generated"}
                  onChange={() => toggle(v.id)}
                />
                {v.message_angle}
              </label>
              {v.media_type === "video" && v.video_url && (
                <video src={v.video_url} controls className="rounded w-full" />
              )}
              {v.media_type === "video" && v.video_url && v.audio_gen_error && (
                <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded px-2 py-1">
                  Posted without audio: {v.audio_gen_error}
                </p>
              )}
              {v.media_type === "video" && !v.video_url && v.generation_status === "generating" && (
                <p className="text-xs text-neutral-500 bg-neutral-100 rounded p-3 text-center">
                  Generating video… this can take a few minutes. Refresh to check.
                </p>
              )}
              {v.media_type === "video" && v.generation_status === "failed" && (
                <p className="text-xs text-red-600 bg-red-50 rounded p-3">
                  Video generation failed{v.video_gen_error ? `: ${v.video_gen_error}` : "."}
                </p>
              )}
              {v.media_type !== "video" && v.image_url && (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={v.image_url} alt={v.message_angle} className="rounded" />
              )}
              <div className="flex items-center justify-between">
                <p className="text-xs text-neutral-400">
                  quality check: {v.quality_check_status}
                </p>
                {v.media_type === "video" && v.video_url && (
                  <button
                    onClick={() => downloadImage(v.video_url!, variantFilename(v.message_angle, v.id, "mp4"))}
                    aria-label="Download video"
                    title="Download video"
                    className="p-1.5 rounded-full border border-neutral-200 bg-neutral-50 text-neutral-500 hover:bg-black hover:text-white hover:border-black transition-colors"
                  >
                    <DownloadIcon className="w-4 h-4" />
                  </button>
                )}
                {v.media_type !== "video" && v.image_url && (
                  <button
                    onClick={() => downloadImage(v.image_url!, variantFilename(v.message_angle, v.id))}
                    aria-label="Download image"
                    title="Download image"
                    className="p-1.5 rounded-full border border-neutral-200 bg-neutral-50 text-neutral-500 hover:bg-black hover:text-white hover:border-black transition-colors"
                  >
                    <DownloadIcon className="w-4 h-4" />
                  </button>
                )}
              </div>
              {variantCaptions.map((c) => (
                <EditableCaption key={c.id} campaignId={id} caption={c} onSaved={handleCaptionSaved} />
              ))}
            </div>
          );
        })}
      </div>

      <button
        onClick={handleApproveAndPost}
        disabled={!!step || selected.size === 0}
        className="bg-black text-white rounded px-3 py-2 disabled:opacity-50"
      >
        Approve & post
      </button>
    </div>
  );
}
