"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";

type Variant = {
  id: string;
  message_angle: string;
  image_prompt: string;
  media_type: string;
  motion_prompt: string | null;
  generation_status: string;
  voiceover_script: string | null;
  voice_instructions: string | null;
  music_prompt: string | null;
  target_platforms: string[];
};

function EditablePrompt({
  campaignId,
  variant,
  onSaved,
}: {
  campaignId: string;
  variant: Variant;
  onSaved: (updated: Variant) => void;
}) {
  const [imagePrompt, setImagePrompt] = useState(variant.image_prompt);
  const [motionPrompt, setMotionPrompt] = useState(variant.motion_prompt ?? "");
  const [voiceoverScript, setVoiceoverScript] = useState(variant.voiceover_script ?? "");
  const [voiceInstructions, setVoiceInstructions] = useState(variant.voice_instructions ?? "");
  const [musicPrompt, setMusicPrompt] = useState(variant.music_prompt ?? "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isVideo = variant.media_type === "video";
  // A campaign can now mix pieces with different settings (from the scoping plan),
  // so whether this variant has audio fields at all is per-variant — the same
  // signal (non-null) used before the campaign-wide audio toggles existed.
  const showVoiceover = variant.voiceover_script !== null;
  const showMusic = variant.music_prompt !== null;
  const dirty =
    imagePrompt !== variant.image_prompt ||
    (isVideo && motionPrompt !== (variant.motion_prompt ?? "")) ||
    (showVoiceover &&
      (voiceoverScript !== (variant.voiceover_script ?? "") || voiceInstructions !== (variant.voice_instructions ?? ""))) ||
    (showMusic && musicPrompt !== (variant.music_prompt ?? ""));

  async function handleSave() {
    setSaving(true);
    setError(null);
    try {
      const updated = await api.updateVariantPrompt(campaignId, variant.id, {
        image_prompt: imagePrompt,
        ...(isVideo ? { motion_prompt: motionPrompt } : {}),
        ...(showVoiceover ? { voiceover_script: voiceoverScript, voice_instructions: voiceInstructions } : {}),
        ...(showMusic ? { music_prompt: musicPrompt } : {}),
      });
      onSaved(updated);
    } catch (err: any) {
      setError(err.message ?? String(err));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="flex flex-col gap-2">
      <label className="text-xs text-neutral-500">
        Image prompt (the starting image{isVideo ? ", animated below" : ""})
        <textarea
          value={imagePrompt}
          onChange={(e) => setImagePrompt(e.target.value)}
          rows={4}
          className="w-full border rounded p-2 text-sm mt-1"
        />
      </label>
      {isVideo && (
        <label className="text-xs text-neutral-500">
          Motion prompt (how the starting image animates)
          <textarea
            value={motionPrompt}
            onChange={(e) => setMotionPrompt(e.target.value)}
            rows={3}
            className="w-full border rounded p-2 text-sm mt-1"
          />
        </label>
      )}
      {showVoiceover && (
        <>
          <label className="text-xs text-neutral-500">
            Voiceover script (spoken narration)
            <textarea
              value={voiceoverScript}
              onChange={(e) => setVoiceoverScript(e.target.value)}
              rows={2}
              className="w-full border rounded p-2 text-sm mt-1"
            />
          </label>
          <label className="text-xs text-neutral-500">
            Voice delivery (tone/pace direction for the voiceover)
            <input
              value={voiceInstructions}
              onChange={(e) => setVoiceInstructions(e.target.value)}
              className="w-full border rounded p-2 text-sm mt-1"
            />
          </label>
        </>
      )}
      {showMusic && (
        <label className="text-xs text-neutral-500">
          Background music style
          <input
            value={musicPrompt}
            onChange={(e) => setMusicPrompt(e.target.value)}
            className="w-full border rounded p-2 text-sm mt-1"
          />
        </label>
      )}
      <div className="flex items-center gap-2">
        <button
          onClick={handleSave}
          disabled={!dirty || saving}
          className="border rounded px-2 py-1 text-xs disabled:opacity-50"
        >
          {saving ? "Saving…" : dirty ? "Save prompt" : "Saved"}
        </button>
        {error && <span className="text-red-600 text-xs">{error}</span>}
      </div>
    </div>
  );
}

export default function PromptsPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [variants, setVariants] = useState<Variant[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [step, setStep] = useState<string | null>("Loading…");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const campaign = await api.getCampaign(id);
        // Prompt review only makes sense after scoping has produced variants to review,
        // and before media is generated. Anything earlier (still scoping) sends back to
        // that step; anything later (already generated) sends to the normal review screen.
        if (campaign.status === "draft" || campaign.status === "awaiting_scope") {
          router.replace(`/campaign/${id}/scope`);
          return;
        }
        if (campaign.status !== "awaiting_prompt_review") {
          router.replace(`/campaign/${id}/variants`);
          return;
        }

        const v = await api.listVariants(id);
        setVariants(v);
        setSelected(new Set(v.map((x: Variant) => x.id)));
        setStep(null);
      } catch (err: any) {
        setError(err.message ?? String(err));
        setStep(null);
      }
    })();
  }, [id, router]);

  function toggle(variantId: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(variantId) ? next.delete(variantId) : next.add(variantId);
      return next;
    });
  }

  function handlePromptSaved(updated: Variant) {
    setVariants((prev) => prev.map((v) => (v.id === updated.id ? updated : v)));
  }

  async function handleGenerate() {
    setError(null);
    try {
      const hasVideo = variants.some((v) => selected.has(v.id) && v.media_type === "video");
      const hasAudio = variants.some(
        (v) => selected.has(v.id) && (v.voiceover_script !== null || v.music_prompt !== null)
      );
      setStep(
        hasVideo
          ? `Generating selected variants — image + video${hasAudio ? " + audio" : ""} generation, this can take a few minutes…`
          : "Generating selected variants — this calls real image generation, may take a minute…"
      );
      await api.generateMedia(id, Array.from(selected));
      router.push(`/campaign/${id}/variants`);
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
      <h1 className="text-xl font-semibold mb-2 mt-2">Review prompts</h1>
      <p className="text-sm text-neutral-500 mb-6">
        Nothing has been generated yet — no cost spent. Edit any prompt below, or uncheck a
        variant to skip it entirely. Only the variants you keep checked get generated.
      </p>

      {step && <p className="text-sm text-neutral-500 mb-4">{step}</p>}
      {error && <p className="text-red-600 text-sm mb-4">{error}</p>}

      <div className="flex flex-col gap-4 mb-8">
        {variants.map((v) => (
          <div key={v.id} className="border rounded p-3 flex flex-col gap-2">
            <label className="flex items-center gap-2 text-sm font-medium flex-wrap">
              <input type="checkbox" checked={selected.has(v.id)} onChange={() => toggle(v.id)} />
              {v.message_angle}
              {v.media_type === "video" && (
                <span className="text-xs font-normal text-neutral-400 border rounded px-1.5 py-0.5">video</span>
              )}
              {v.target_platforms.length > 0 && (
                <span className="text-xs font-normal text-blue-600 border border-blue-200 bg-blue-50 rounded px-1.5 py-0.5">
                  {v.target_platforms.join(", ")}
                </span>
              )}
            </label>
            <EditablePrompt campaignId={id} variant={v} onSaved={handlePromptSaved} />
          </div>
        ))}
      </div>

      <button
        onClick={handleGenerate}
        disabled={!!step || selected.size === 0}
        className="bg-black text-white rounded px-3 py-2 disabled:opacity-50"
      >
        Generate selected ({selected.size})
      </button>
    </div>
  );
}
