"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useParams } from "next/navigation";
import { api } from "@/lib/api";

export default function EditBrandPage() {
  const router = useRouter();
  const params = useParams();
  const brandId = params.id as string;

  const [brand, setBrand] = useState<any>(null);
  const [brandName, setBrandName] = useState("");
  const [description, setDescription] = useState("");
  const [brandVoiceId, setBrandVoiceId] = useState("");
  const [voices, setVoices] = useState<Array<{ voice_id: string; name: string; description: string }>>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [nameValidation, setNameValidation] = useState<{
    checking: boolean;
    isDuplicate: boolean;
    message: string | null;
  }>({ checking: false, isDuplicate: false, message: null });

  // Load brand data and available voices
  useEffect(() => {
    Promise.all([
      api.getBrand(brandId),
      api.getAvailableVoices().catch(() => []), // Non-fatal if voices fail to load
    ])
      .then(([brandData, voicesData]) => {
        setBrand(brandData);
        setBrandName(brandData.name);
        setDescription(brandData.description || "");
        setBrandVoiceId(brandData.brand_voice_id || "");
        setVoices(voicesData);
      })
      .catch((err) => setError(err.message ?? String(err)))
      .finally(() => setLoading(false));
  }, [brandId]);

  // Check for duplicate brand names with debounce
  useEffect(() => {
    if (!brandName.trim() || brandName === brand?.name) {
      setNameValidation({ checking: false, isDuplicate: false, message: null });
      return;
    }

    setNameValidation({ checking: true, isDuplicate: false, message: null });

    const timeoutId = setTimeout(async () => {
      try {
        const brands = await api.listBrands();
        const duplicate = brands.find(
          (b: any) => b.id !== brandId && b.name.toLowerCase() === brandName.trim().toLowerCase()
        );

        if (duplicate) {
          setNameValidation({
            checking: false,
            isDuplicate: true,
            message: `A brand named "${duplicate.name}" already exists. Please choose a different name.`,
          });
        } else {
          setNameValidation({ checking: false, isDuplicate: false, message: null });
        }
      } catch (err) {
        // Silently fail validation check
        setNameValidation({ checking: false, isDuplicate: false, message: null });
      }
    }, 500); // 500ms debounce

    return () => clearTimeout(timeoutId);
  }, [brandName, brand, brandId]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSaving(true);

    try {
      await api.updateBrand(brandId, {
        name: brandName,
        description: description || undefined,
        brand_voice_id: brandVoiceId || undefined,
      });

      // Redirect back to brands library
      router.push("/brands");
    } catch (err: any) {
      setError(err.message ?? String(err));
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto">
        <p className="text-sm text-neutral-500">Loading…</p>
      </div>
    );
  }

  if (error && !brand) {
    return (
      <div className="max-w-2xl mx-auto">
        <p className="text-red-600 text-sm">{error}</p>
        <Link href="/brands" className="text-sm text-neutral-500 mt-4 inline-block">
          ← Back to brand library
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto">
      <Link href="/brands" className="text-sm text-neutral-500">
        ← Back to brand library
      </Link>
      <h1 className="text-xl font-semibold mb-2 mt-2">Edit Brand</h1>
      <p className="text-sm text-neutral-500 mb-6">
        Update your brand's basic information and voice settings. Brand guidelines cannot be edited
        after creation.
      </p>

      <form onSubmit={handleSubmit} className="flex flex-col gap-6">
        <fieldset className="flex flex-col gap-3">
          <legend className="font-medium mb-1">Brand Information</legend>

          <div>
            <label className="block text-sm font-medium mb-1">Brand name *</label>
            <input
              placeholder="e.g., Nike, Apple, Acme Corp"
              required
              value={brandName}
              onChange={(e) => setBrandName(e.target.value)}
              className={`border rounded px-3 py-2 w-full ${
                nameValidation.isDuplicate
                  ? "border-red-500 focus:border-red-500 focus:ring-red-500"
                  : "border-gray-300"
              }`}
            />
            {nameValidation.checking && (
              <p className="text-xs text-neutral-400 mt-1">Checking availability...</p>
            )}
            {nameValidation.isDuplicate && nameValidation.message && (
              <p className="text-xs text-red-600 mt-1">{nameValidation.message}</p>
            )}
            {!nameValidation.checking && !nameValidation.isDuplicate && brandName.trim() && brandName !== brand?.name && (
              <p className="text-xs text-green-600 mt-1">✓ Name is available</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">
              Brand description (optional)
            </label>
            <textarea
              placeholder="High-level description (industry, positioning, target audience)…"
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="border rounded px-3 py-2 w-full"
            />
            <p className="text-xs text-neutral-400 mt-1">
              e.g., "Global sports brand focused on athletes, innovative, performance-driven"
            </p>
          </div>
        </fieldset>

        <fieldset className="flex flex-col gap-3">
          <legend className="font-medium mb-1">Voice Settings</legend>

          <div>
            <label className="block text-sm font-medium mb-1">
              Brand voice (optional)
            </label>
            <select
              value={brandVoiceId}
              onChange={(e) => setBrandVoiceId(e.target.value)}
              className="border rounded px-3 py-2 w-full"
            >
              <option value="">Default voice</option>
              {voices.map((voice) => (
                <option key={voice.voice_id} value={voice.voice_id}>
                  {voice.name} - {voice.description}
                </option>
              ))}
            </select>
            <p className="text-xs text-neutral-400 mt-1">
              Voice used for video voiceovers across all campaigns using this brand
            </p>
          </div>
        </fieldset>

        {error && <p className="text-red-600 text-sm">{error}</p>}

        <div className="flex gap-3">
          <button
            type="submit"
            disabled={saving || nameValidation.isDuplicate}
            className="bg-black text-white rounded px-4 py-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {saving ? "Saving…" : "Save Changes"}
          </button>
          <Link
            href="/brands"
            className="border rounded px-4 py-2 text-sm hover:bg-neutral-50"
          >
            Cancel
          </Link>
        </div>
      </form>
    </div>
  );
}
