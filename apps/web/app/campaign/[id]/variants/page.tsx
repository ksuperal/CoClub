"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
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

export default function VariantsPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [variants, setVariants] = useState<Variant[]>([]);
  const [captions, setCaptions] = useState<Caption[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [step, setStep] = useState<string | null>("Loading…");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const v = await api.listVariants(id);
        setVariants(v);
        setSelected(new Set(v.filter((x: Variant) => x.quality_check_status === "passed").map((x: Variant) => x.id)));

        let c = await api.listCaptions(id);
        if (c.length === 0) {
          setStep("Writing captions & hashtags…");
          await api.generateCopy(id);
          c = await api.listCaptions(id);
        }
        setCaptions(c);
        setStep(null);
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
        Select which variants to approve for posting. Unchecked variants are rejected.
      </p>

      {step && <p className="text-sm text-neutral-500 mb-4">{step}</p>}
      {error && <p className="text-red-600 text-sm mb-4">{error}</p>}

      <div className="grid grid-cols-2 gap-4 mb-8">
        {variants.map((v) => {
          const variantCaptions = captions.filter((c) => c.variant_id === v.id);
          return (
            <div key={v.id} className="border rounded p-3 flex flex-col gap-2">
              <label className="flex items-center gap-2 text-sm font-medium">
                <input type="checkbox" checked={selected.has(v.id)} onChange={() => toggle(v.id)} />
                {v.message_angle}
              </label>
              {v.image_url && (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={v.image_url} alt={v.message_angle} className="rounded" />
              )}
              <p className="text-xs text-neutral-400">
                quality check: {v.quality_check_status}
              </p>
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
