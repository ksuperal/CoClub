"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

// Reusable file input hint
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

function appendFiles(
  e: React.ChangeEvent<HTMLInputElement>,
  currentFiles: File[],
  setFiles: (files: File[]) => void
): void {
  const newFiles = Array.from(e.target.files ?? []);
  e.target.value = "";
  setFiles([...currentFiles, ...newFiles]);
}

export default function NewBrandPage() {
  const router = useRouter();
  const [brandName, setBrandName] = useState("");
  const [description, setDescription] = useState("");
  const [guidelineText, setGuidelineText] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [step, setStep] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [nameValidation, setNameValidation] = useState<{
    checking: boolean;
    isDuplicate: boolean;
    message: string | null;
  }>({ checking: false, isDuplicate: false, message: null });

  // Check for duplicate brand names with debounce
  useEffect(() => {
    if (!brandName.trim()) {
      setNameValidation({ checking: false, isDuplicate: false, message: null });
      return;
    }

    setNameValidation({ checking: true, isDuplicate: false, message: null });

    const timeoutId = setTimeout(async () => {
      try {
        const brands = await api.listBrands();
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
  }, [brandName]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    try {
      let assetPaths: string[] = [];
      if (files.length > 0) {
        setStep(`Uploading ${files.length} brand asset(s)…`);
        assetPaths = await api.uploadBrandAssets(files);
      }

      setStep("Extracting brand profile…");
      const brand = await api.createBrand({
        name: brandName,
        description: description || undefined,
        guideline_raw_text: guidelineText,
        guideline_asset_paths: assetPaths,
      });

      // Redirect to brands library with success message
      router.push("/brands");
    } catch (err: any) {
      setError(err.message ?? String(err));
      setStep(null);
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <Link href="/brands" className="text-sm text-neutral-500">
        ← Back to brand library
      </Link>
      <h1 className="text-xl font-semibold mb-2 mt-2">Add Brand</h1>
      <p className="text-sm text-neutral-500 mb-6">
        Create a brand preset that can be reused across multiple campaigns. Brand guidelines
        will be extracted once and saved for future use.
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
            {!nameValidation.checking && !nameValidation.isDuplicate && brandName.trim() && (
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
          <legend className="font-medium mb-1">Brand Guidelines</legend>

          <div>
            <label className="block text-sm font-medium mb-1">
              Guideline text *
            </label>
            <textarea
              placeholder="Paste your brand guideline text (colors, tone, dos/don'ts)…"
              required
              rows={6}
              value={guidelineText}
              onChange={(e) => setGuidelineText(e.target.value)}
              className="border rounded px-3 py-2 w-full"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">
              Guideline file(s) (optional)
            </label>
            <input
              type="file"
              multiple
              accept={ACCEPTED_FILE_TYPES}
              onChange={(e) => appendFiles(e, files, setFiles)}
              className="block"
            />
            <p className="text-xs text-neutral-400 mt-1">{ACCEPTED_FILE_HINT}</p>
            <p className="text-xs text-neutral-400 mt-1">
              Files take priority over text above if provided
            </p>
            <FileListPreview files={files} onRemove={(i) => setFiles((prev) => prev.filter((_, idx) => idx !== i))} />
          </div>
        </fieldset>

        {error && <p className="text-red-600 text-sm">{error}</p>}
        {step && <p className="text-sm text-neutral-500">{step}</p>}

        <div className="flex gap-3">
          <button
            type="submit"
            disabled={!!step || nameValidation.isDuplicate}
            className="bg-black text-white rounded px-4 py-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {step ? "Working…" : "Create Brand"}
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
