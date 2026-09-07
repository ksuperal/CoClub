"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { CAMPAIGN_TYPES } from "@/lib/constants";

// Shown next to every file input so it's clear upfront what's usable and how.
const ACCEPTED_FILE_HINT =
  "Accepted: PNG, JPG, WEBP, or PDF (used as a real visual reference for image generation — " +
  "PDF pages are rendered into images automatically). GIF is also accepted but read for text " +
  "only, not usable as a visual reference. You can select multiple files.";
const ACCEPTED_FILE_TYPES = ".png,.jpg,.jpeg,.webp,.pdf,.gif";

function FileListPreview({ files }: { files: File[] }) {
  if (files.length === 0) return null;
  return (
    <ul className="text-xs text-neutral-500 list-disc list-inside">
      {files.map((f, i) => (
        <li key={i}>
          {f.name} ({(f.size / 1024).toFixed(0)} KB)
        </li>
      ))}
    </ul>
  );
}

export default function IntakePage() {
  const router = useRouter();
  const [brandName, setBrandName] = useState("");
  const [guidelineText, setGuidelineText] = useState("");
  const [files, setFiles] = useState<File[]>([]);

  const [includeProduct, setIncludeProduct] = useState(true);
  const [productName, setProductName] = useState("");
  const [productFiles, setProductFiles] = useState<File[]>([]);
  const [productDescription, setProductDescription] = useState("");

  const [campaignType, setCampaignType] = useState("product_launch");
  const [brief, setBrief] = useState("");
  const [variantCount, setVariantCount] = useState(4);
  const [step, setStep] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (includeProduct && productFiles.length === 0) {
      setError(
        "At least one product photo/file is required — or uncheck 'This campaign is about a specific product'."
      );
      return;
    }

    try {
      let assetPaths: string[] = [];
      if (files.length > 0) {
        setStep(`Uploading ${files.length} brand asset(s)…`);
        assetPaths = await api.uploadBrandAssets(files);
      }

      setStep("Extracting brand profile…");
      const brand = await api.createBrand({
        name: brandName,
        guideline_raw_text: guidelineText,
        guideline_asset_paths: assetPaths,
      });

      let productId: string | null = null;
      if (includeProduct && productFiles.length > 0) {
        setStep(`Uploading ${productFiles.length} product file(s)…`);
        const productAssetPaths = await api.uploadProductAssets(productFiles);

        setStep("Extracting product profile…");
        const product = await api.createProduct({
          brand_id: brand.id,
          name: productName,
          description_text: productDescription || undefined,
          asset_paths: productAssetPaths,
        });
        productId = product.id;
      }

      setStep("Creating campaign…");
      const campaign = await api.createCampaign({
        brand_id: brand.id,
        product_id: productId,
        campaign_type: campaignType,
        brief,
        variant_count: variantCount,
      });

      setStep("Generating ad variants — this calls real image generation, may take a minute…");
      await api.generateVariants(campaign.id);

      router.push(`/campaign/${campaign.id}/variants`);
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
      <h1 className="text-xl font-semibold mb-6 mt-2">New campaign</h1>
      <form onSubmit={handleSubmit} className="flex flex-col gap-6">
        <fieldset className="flex flex-col gap-3">
          <legend className="font-medium mb-1">Brand</legend>
          <input
            placeholder="Brand name"
            required
            value={brandName}
            onChange={(e) => setBrandName(e.target.value)}
            className="border rounded px-3 py-2"
          />
          <textarea
            placeholder="Paste your brand guideline text (colors, tone, dos/don'ts)…"
            required
            rows={6}
            value={guidelineText}
            onChange={(e) => setGuidelineText(e.target.value)}
            className="border rounded px-3 py-2"
          />
          <label className="text-sm text-neutral-600">
            Brand guideline file(s) — optional, but takes priority over the text above if provided
            <input
              type="file"
              multiple
              accept={ACCEPTED_FILE_TYPES}
              onChange={(e) => setFiles(Array.from(e.target.files ?? []))}
              className="block mt-1"
            />
            <span className="block text-xs text-neutral-400 mt-1">{ACCEPTED_FILE_HINT}</span>
            <FileListPreview files={files} />
          </label>
        </fieldset>

        <fieldset className="flex flex-col gap-3">
          <legend className="font-medium mb-1">Product</legend>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={includeProduct}
              onChange={(e) => setIncludeProduct(e.target.checked)}
            />
            This campaign is about a specific product
          </label>

          {includeProduct && (
            <>
              <input
                placeholder="Product name"
                required={includeProduct}
                value={productName}
                onChange={(e) => setProductName(e.target.value)}
                className="border rounded px-3 py-2"
              />
              <label className="text-sm text-neutral-600">
                Product photo/file(s) — required, this is what the AI uses as ground truth for what
                the product actually looks like
                <input
                  type="file"
                  multiple
                  required={includeProduct && productFiles.length === 0}
                  accept={ACCEPTED_FILE_TYPES}
                  onChange={(e) => setProductFiles(Array.from(e.target.files ?? []))}
                  className="block mt-1"
                />
                <span className="block text-xs text-neutral-400 mt-1">{ACCEPTED_FILE_HINT}</span>
                <FileListPreview files={productFiles} />
              </label>
              <textarea
                placeholder="Product description (optional — supplementary to the photo)"
                rows={3}
                value={productDescription}
                onChange={(e) => setProductDescription(e.target.value)}
                className="border rounded px-3 py-2"
              />
            </>
          )}
        </fieldset>

        <fieldset className="flex flex-col gap-3">
          <legend className="font-medium mb-1">Campaign</legend>
          <select
            value={campaignType}
            onChange={(e) => setCampaignType(e.target.value)}
            className="border rounded px-3 py-2"
          >
            {CAMPAIGN_TYPES.map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
          <textarea
            placeholder="What do you want to promote? (product, event, offer…)"
            required
            rows={3}
            value={brief}
            onChange={(e) => setBrief(e.target.value)}
            className="border rounded px-3 py-2"
          />
          <label className="text-sm text-neutral-600 flex items-center gap-2">
            Number of variants to generate
            <input
              type="number"
              min={1}
              max={10}
              value={variantCount}
              onChange={(e) => setVariantCount(Number(e.target.value))}
              className="border rounded px-2 py-1 w-20"
            />
            <span className="text-neutral-400">(each is a real, billed image-gen call)</span>
          </label>
        </fieldset>

        {error && <p className="text-red-600 text-sm">{error}</p>}
        {step && <p className="text-sm text-neutral-500">{step}</p>}

        <button
          type="submit"
          disabled={!!step}
          className="bg-black text-white rounded px-3 py-2 disabled:opacity-50"
        >
          {step ? "Working…" : "Generate variants"}
        </button>
      </form>
    </div>
  );
}
