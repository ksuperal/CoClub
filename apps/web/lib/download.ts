// Variant images live in Supabase's public "campaign-variants" bucket — a
// different origin than the app. The `download` attribute on a plain <a> is only
// honored for same-origin URLs (or if the server sends Content-Disposition:
// attachment, which Supabase's public bucket doesn't), so a cross-origin image
// just opens in a new tab instead of saving. Fetching it as a blob first and
// downloading *that* (a same-origin blob: URL) is the standard workaround.
export async function downloadImage(url: string, filename: string): Promise<void> {
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    const blob = await res.blob();
    const objectUrl = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = objectUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(objectUrl);
  } catch {
    // CORS or network failure — fall back to opening it directly so the user can
    // still right-click "Save image as" themselves.
    window.open(url, "_blank", "noopener,noreferrer");
  }
}

// Short, filesystem-safe filename from a variant's message angle.
export function variantFilename(messageAngle: string, variantId: string): string {
  const slug = messageAngle
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 40);
  return `${slug || "variant"}-${variantId.slice(0, 8)}.png`;
}
