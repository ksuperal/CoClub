"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

const CAMPAIGN_TYPES = [
  ["product_launch", "Product launch"],
  ["event_announcement", "Event announcement"],
  ["promo_offer", "Promo / offer"],
  ["brand_awareness", "Brand awareness"],
  ["other", "Other"],
];

export default function IntakePage() {
  const router = useRouter();
  const [brandName, setBrandName] = useState("");
  const [guidelineText, setGuidelineText] = useState("");
  const [file, setFile] = useState<File | null>(null);

  const [includeProduct, setIncludeProduct] = useState(true);
  const [productName, setProductName] = useState("");
  const [productFile, setProductFile] = useState<File | null>(null);
  const [productDescription, setProductDescription] = useState("");

  const [campaignType, setCampaignType] = useState("product_launch");
  const [brief, setBrief] = useState("");
  const [variantCount, setVariantCount] = useState(4);
  const [step, setStep] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (includeProduct && !productFile) {
      setError("A product photo/file is required — or uncheck 'This campaign is about a specific product'.");
      return;
    }

    try {
      let assetPaths: string[] = [];
      if (file) {
        setStep("Uploading brand asset…");
        const { path } = await api.uploadBrandAsset(file);
        assetPaths = [path];
      }

      setStep("Extracting brand profile…");
      const brand = await api.createBrand({
        name: brandName,
        guideline_raw_text: guidelineText,
        guideline_asset_paths: assetPaths,
      });

      let productId: string | null = null;
      if (includeProduct && productFile) {
        setStep("Uploading product photo…");
        const { path } = await api.uploadProductAsset(productFile);

        setStep("Extracting product profile…");
        const product = await api.createProduct({
          brand_id: brand.id,
          name: productName,
          description_text: productDescription || undefined,
          asset_paths: [path],
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
      <h1 className="text-xl font-semibold mb-6">New campaign</h1>
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
            Brand guideline file (optional, but takes priority over the text above if provided)
            <input type="file" onChange={(e) => setFile(e.target.files?.[0] ?? null)} className="block mt-1" />
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
                Product photo/file (required — this is what the AI uses as ground truth for what
                the product actually looks like)
                <input
                  type="file"
                  required={includeProduct}
                  onChange={(e) => setProductFile(e.target.files?.[0] ?? null)}
                  className="block mt-1"
                />
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
