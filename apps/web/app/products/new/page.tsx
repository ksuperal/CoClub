"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { api } from "@/lib/api";

// Reusable file input hint
const ACCEPTED_FILE_HINT =
  "Accepted: PNG, JPG, WEBP, or PDF (used as a real visual reference for image generation — " +
  "PDF pages are rendered into images automatically). GIF is also accepted but read for text " +
  "only, not usable as a visual reference. You can select multiple files.";
const ACCEPTED_FILE_TYPES = ".png,.jpg,.jpeg,.webp,.pdf,.gif";
const MAX_PRODUCT_FILES = 10;

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

function appendFiles(
  e: React.ChangeEvent<HTMLInputElement>,
  currentFiles: File[],
  setFiles: (files: File[]) => void,
  setError: (error: string | null) => void
): void {
  const newFiles = Array.from(e.target.files ?? []);
  e.target.value = "";
  const combined = [...currentFiles, ...newFiles];
  if (combined.length > MAX_PRODUCT_FILES) {
    setFiles(combined.slice(0, MAX_PRODUCT_FILES));
    setError(`Only the first ${MAX_PRODUCT_FILES} files are kept — up to ${MAX_PRODUCT_FILES} product photos are allowed.`);
  } else {
    setFiles(combined);
    setError(null);
  }
}

export default function NewProductPage() {
  return (
    <Suspense fallback={null}>
      <NewProductPageInner />
    </Suspense>
  );
}

// useSearchParams() (for the ?brand_id= pre-selection) opts this out of static
// rendering and requires a Suspense boundary above it — split out so the default
// export itself stays a plain, staticly-renderable wrapper.
function NewProductPageInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const preSelectedBrandId = searchParams.get("brand_id");

  const [brands, setBrands] = useState<any[]>([]);
  const [loadingBrands, setLoadingBrands] = useState(true);
  const [brandId, setBrandId] = useState(preSelectedBrandId || "");
  const [productName, setProductName] = useState("");
  const [description, setDescription] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [step, setStep] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .listBrands()
      .then((data) => {
        setBrands(data);
        setLoadingBrands(false);
      })
      .catch((err) => {
        console.error("Failed to load brands:", err);
        setLoadingBrands(false);
      });
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (files.length === 0) {
      setError("At least one product photo/file is required.");
      return;
    }

    try {
      setStep(`Uploading ${files.length} product file(s)…`);
      const assetPaths = await api.uploadProductAssets(files);

      setStep("Extracting product profile…");
      const product = await api.createProduct({
        brand_id: brandId,
        name: productName,
        description_text: description || undefined,
        asset_paths: assetPaths,
      });

      // Redirect to products library
      router.push("/products");
    } catch (err: any) {
      setError(err.message ?? String(err));
      setStep(null);
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <Link href="/products" className="text-sm text-neutral-500">
        ← Back to product library
      </Link>
      <h1 className="text-xl font-semibold mb-2 mt-2">Add Product</h1>
      <p className="text-sm text-neutral-500 mb-6">
        Create a product preset that can be reused across multiple campaigns. Product details
        will be extracted once and saved for future use.
      </p>

      <form onSubmit={handleSubmit} className="flex flex-col gap-6">
        <fieldset className="flex flex-col gap-3">
          <legend className="font-medium mb-1">Product Information</legend>

          <div>
            <label className="block text-sm font-medium mb-1">Brand *</label>
            {loadingBrands ? (
              <p className="text-sm text-neutral-500">Loading brands…</p>
            ) : (
              <select
                required
                value={brandId}
                onChange={(e) => setBrandId(e.target.value)}
                className="border rounded px-3 py-2 w-full"
              >
                <option value="">Select a brand…</option>
                {brands.map((brand) => (
                  <option key={brand.id} value={brand.id}>
                    {brand.name}
                  </option>
                ))}
              </select>
            )}
            {brands.length === 0 && !loadingBrands && (
              <p className="text-xs text-neutral-500 mt-1">
                No brands found.{" "}
                <Link href="/brands/new" className="text-blue-600 hover:underline">
                  Create one first
                </Link>
              </p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Product name *</label>
            <input
              placeholder="e.g., iPhone 15 Pro, Nike Air Max, Acme Widget"
              required
              value={productName}
              onChange={(e) => setProductName(e.target.value)}
              className="border rounded px-3 py-2 w-full"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">
              Product description (optional)
            </label>
            <textarea
              placeholder="Supplementary description of the product…"
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="border rounded px-3 py-2 w-full"
            />
            <p className="text-xs text-neutral-400 mt-1">
              Optional — product photos are the primary reference
            </p>
          </div>
        </fieldset>

        <fieldset className="flex flex-col gap-3">
          <legend className="font-medium mb-1">Product Photos</legend>

          <div>
            <label className="block text-sm font-medium mb-1">
              Product photo/file(s) *
            </label>
            <input
              type="file"
              multiple
              required={files.length === 0}
              accept={ACCEPTED_FILE_TYPES}
              onChange={(e) => appendFiles(e, files, setFiles, setError)}
              className="block"
            />
            <p className="text-xs text-neutral-400 mt-1">{ACCEPTED_FILE_HINT}</p>
            <p className="text-xs text-neutral-400 mt-1">
              Up to {MAX_PRODUCT_FILES} files. This is what the AI uses as ground truth for what
              the product actually looks like.
            </p>
            <FileListPreview files={files} onRemove={(i) => setFiles((prev) => prev.filter((_, idx) => idx !== i))} />
          </div>
        </fieldset>

        {error && <p className="text-red-600 text-sm">{error}</p>}
        {step && <p className="text-sm text-neutral-500">{step}</p>}

        <div className="flex gap-3">
          <button
            type="submit"
            disabled={!!step || brands.length === 0}
            className="bg-black text-white rounded px-4 py-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {step ? "Working…" : "Create Product"}
          </button>
          <Link
            href="/products"
            className="border rounded px-4 py-2 text-sm hover:bg-neutral-50"
          >
            Cancel
          </Link>
        </div>
      </form>
    </div>
  );
}
