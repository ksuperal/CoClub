"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { CAMPAIGN_TYPES } from "@/lib/constants";

// Shown next to every file input so it's clear upfront what's usable and how.
const ACCEPTED_FILE_HINT =
  "Accepted: PNG, JPG, WEBP, or PDF (used as a real visual reference for image generation — " +
  "PDF pages are rendered into images automatically). GIF is also accepted but read for text " +
  "only, not usable as a visual reference. You can select multiple files.";
const ACCEPTED_FILE_TYPES = ".png,.jpg,.jpeg,.webp,.pdf,.gif";

function FileListPreview({ files, onRemove }: { files: File[]; onRemove: (index: number) => void }) {
  if (files.length === 0) return null;
  return (
    <ul className="text-xs text-neutral-500">
      {files.map((f, i) => (
        <li key={i} className="flex items-center gap-2">
          <span className="list-disc list-inside">
            • {f.name} ({(f.size / 1024).toFixed(0)} KB)
          </span>
          <button type="button" onClick={() => onRemove(i)} className="text-red-500 hover:underline">
            Remove
          </button>
        </li>
      ))}
    </ul>
  );
}

const MAX_PRODUCT_FILES = 10;

function appendFiles(
  e: React.ChangeEvent<HTMLInputElement>,
  currentFiles: File[],
  setFiles: (files: File[]) => void,
  max?: number
): string | null {
  const newFiles = Array.from(e.target.files ?? []);
  e.target.value = "";
  const combined = [...currentFiles, ...newFiles];
  if (max && combined.length > max) {
    setFiles(combined.slice(0, max));
    return `Only the first ${max} files are kept — up to ${max} product photos are allowed.`;
  }
  setFiles(combined);
  return null;
}

export default function IntakePage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const preSelectedBrandId = searchParams.get("brand_id");

  // Brand section
  const [brandMode, setBrandMode] = useState<"select" | "create">("select");
  const [selectedBrandId, setSelectedBrandId] = useState<string>(preSelectedBrandId || "");
  const [brands, setBrands] = useState<any[]>([]);
  const [loadingBrands, setLoadingBrands] = useState(true);

  // New brand fields (only if creating new)
  const [brandName, setBrandName] = useState("");
  const [brandDescription, setBrandDescription] = useState("");
  const [guidelineText, setGuidelineText] = useState("");
  const [files, setFiles] = useState<File[]>([]);

  // Product section
  const [includeProduct, setIncludeProduct] = useState(true);
  const [productName, setProductName] = useState("");
  const [productFiles, setProductFiles] = useState<File[]>([]);
  const [productDescription, setProductDescription] = useState("");

  // Campaign section
  const [campaignType, setCampaignType] = useState("product_launch");
  const [brief, setBrief] = useState("");
  const [step, setStep] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Brand name validation
  const [nameValidation, setNameValidation] = useState<{
    checking: boolean;
    isDuplicate: boolean;
    message: string | null;
  }>({ checking: false, isDuplicate: false, message: null });

  // Check for duplicate brand names with debounce (only in create mode)
  useEffect(() => {
    if (brandMode !== "create" || !brandName.trim()) {
      setNameValidation({ checking: false, isDuplicate: false, message: null });
      return;
    }

    setNameValidation({ checking: true, isDuplicate: false, message: null });

    const timeoutId = setTimeout(async () => {
      try {
        const duplicate = brands.find(
          (b: any) => b.name.toLowerCase() === brandName.trim().toLowerCase()
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
  }, [brandName, brandMode, brands]);

  // Load brands on mount
  useEffect(() => {
    api
      .listBrands()
      .then((data) => {
        setBrands(data);
        setLoadingBrands(false);
        // If we have brands and no pre-selected brand, default to select mode
        if (data.length > 0 && !preSelectedBrandId) {
          setBrandMode("select");
        } else if (data.length === 0) {
          // No brands exist, force create mode
          setBrandMode("create");
        }
      })
      .catch((err) => {
        console.error("Failed to load brands:", err);
        setLoadingBrands(false);
        setBrandMode("create"); // Fallback to create if loading fails
      });
  }, [preSelectedBrandId]);

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
      let brandId = selectedBrandId;

      // Create new brand if in create mode
      if (brandMode === "create") {
        let assetPaths: string[] = [];
        if (files.length > 0) {
          setStep(`Uploading ${files.length} brand asset(s)…`);
          assetPaths = await api.uploadBrandAssets(files);
        }

        setStep("Extracting brand profile…");
        const brand = await api.createBrand({
          name: brandName,
          description: brandDescription || undefined,
          guideline_raw_text: guidelineText,
          guideline_asset_paths: assetPaths,
        });
        brandId = brand.id;
      }

      if (!brandId) {
        setError("Please select a brand or create a new one");
        return;
      }

      // Create product if needed
      let productId: string | null = null;
      if (includeProduct && productFiles.length > 0) {
        setStep(`Uploading ${productFiles.length} product file(s)…`);
        const productAssetPaths = await api.uploadProductAssets(productFiles);

        setStep("Extracting product profile…");
        const product = await api.createProduct({
          brand_id: brandId,
          name: productName,
          description_text: productDescription || undefined,
          asset_paths: productAssetPaths,
        });
        productId = product.id;
      }

      // Create campaign
      setStep("Creating campaign…");
      const campaign = await api.createCampaign({
        brand_id: brandId,
        product_id: productId,
        campaign_type: campaignType,
        brief,
      });

      router.push(`/campaign/${campaign.id}/scope`);
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
        {/* Brand Section */}
        <fieldset className="flex flex-col gap-3">
          <legend className="font-medium mb-1">Brand</legend>

          {loadingBrands ? (
            <p className="text-sm text-neutral-500">Loading brands…</p>
          ) : (
            <>
              {brands.length > 0 && (
                <div className="flex gap-3 mb-2">
                  <button
                    type="button"
                    onClick={() => setBrandMode("select")}
                    className={`px-3 py-1.5 text-sm rounded border ${
                      brandMode === "select"
                        ? "bg-black text-white border-black"
                        : "border-neutral-300 hover:bg-neutral-50"
                    }`}
                  >
                    Select existing brand
                  </button>
                  <button
                    type="button"
                    onClick={() => setBrandMode("create")}
                    className={`px-3 py-1.5 text-sm rounded border ${
                      brandMode === "create"
                        ? "bg-black text-white border-black"
                        : "border-neutral-300 hover:bg-neutral-50"
                    }`}
                  >
                    Create new brand
                  </button>
                </div>
              )}

              {brandMode === "select" ? (
                <>
                  <select
                    value={selectedBrandId}
                    onChange={(e) => setSelectedBrandId(e.target.value)}
                    required
                    className="border rounded px-3 py-2"
                  >
                    <option value="">Select a brand…</option>
                    {brands.map((brand) => (
                      <option key={brand.id} value={brand.id}>
                        {brand.name}
                        {brand.description ? ` — ${brand.description.slice(0, 50)}${brand.description.length > 50 ? '...' : ''}` : ''}
                      </option>
                    ))}
                  </select>
                  <div className="flex items-center gap-2 text-sm text-neutral-500">
                    <span>Don't see your brand?</span>
                    <Link href="/brands/new" className="text-blue-600 hover:underline">
                      Add it to your library →
                    </Link>
                  </div>
                </>
              ) : (
                <>
                  <div>
                    <input
                      placeholder="Brand name"
                      required
                      value={brandName}
                      onChange={(e) => setBrandName(e.target.value)}
                      className={`border rounded px-3 py-2 w-full ${
                        nameValidation.isDuplicate
                          ? "border-red-500 focus:border-red-500 focus:ring-red-500"
                          : ""
                      }`}
                    />
                    {nameValidation.checking && (
                      <p className="text-xs text-neutral-400 mt-1">Checking availability...</p>
                    )}
                    {nameValidation.isDuplicate && nameValidation.message && (
                      <p className="text-xs text-red-600 mt-1">{nameValidation.message}</p>
                    )}
                    {!nameValidation.checking && !nameValidation.isDuplicate && brandName.trim() && (
                      <p className="text-xs text-green-600 mt-1">✓ Name is available</p>
                    )}
                  </div>
                  <textarea
                    placeholder="Brand description (optional) — e.g., industry, positioning, target audience"
                    rows={2}
                    value={brandDescription}
                    onChange={(e) => setBrandDescription(e.target.value)}
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
                      onChange={(e) => appendFiles(e, files, setFiles)}
                      className="block mt-1"
                    />
                    <span className="block text-xs text-neutral-400 mt-1">{ACCEPTED_FILE_HINT}</span>
                    <FileListPreview files={files} onRemove={(i) => setFiles((prev) => prev.filter((_, idx) => idx !== i))} />
                  </label>
                </>
              )}
            </>
          )}
        </fieldset>

        {/* Product Section */}
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
                  onChange={(e) => {
                    const warning = appendFiles(e, productFiles, setProductFiles, MAX_PRODUCT_FILES);
                    setError(warning);
                  }}
                  className="block mt-1"
                />
                <span className="block text-xs text-neutral-400 mt-1">
                  {ACCEPTED_FILE_HINT} Up to {MAX_PRODUCT_FILES} files.
                </span>
                <FileListPreview
                  files={productFiles}
                  onRemove={(i) => setProductFiles((prev) => prev.filter((_, idx) => idx !== i))}
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

        {/* Campaign Section */}
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
          <p className="text-xs text-neutral-400">
            Next step asks how big a campaign you want — how many posts, which platforms,
            image or video — in your own words, before anything is written or generated.
          </p>
        </fieldset>

        {error && <p className="text-red-600 text-sm">{error}</p>}
        {step && <p className="text-sm text-neutral-500">{step}</p>}

        <button
          type="submit"
          disabled={!!step || (brandMode === "create" && nameValidation.isDuplicate)}
          className="bg-black text-white rounded px-3 py-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {step ? "Working…" : "Continue"}
        </button>
      </form>
    </div>
  );
}
