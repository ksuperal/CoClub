"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { supabase } from "@/lib/supabaseClient";

type Brand = {
  id: string;
  name: string;
  description: string | null;
  extracted_profile: any;
  created_at: string;
};

export default function BrandsPage() {
  const router = useRouter();
  const [brands, setBrands] = useState<Brand[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .listBrands()
      .then(setBrands)
      .catch((err) => setError(err.message ?? String(err)));
  }, []);

  async function handleSignOut() {
    await supabase.auth.signOut();
    router.replace("/login");
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold">Brand Library</h1>
          <p className="text-sm text-neutral-500 mt-1">
            Manage your brand presets for reuse across campaigns
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/brands/new" className="bg-black text-white rounded px-3 py-2 text-sm">
            + Add Brand
          </Link>
          <Link href="/home" className="text-sm text-neutral-500">
            Campaigns
          </Link>
          <Link href="/settings/social" className="text-sm text-neutral-500">
            Social accounts
          </Link>
          <button onClick={handleSignOut} className="text-sm text-neutral-500">
            Sign out
          </button>
        </div>
      </div>

      {error && <p className="text-red-600 text-sm mb-4">{error}</p>}

      {brands === null && !error && <p className="text-sm text-neutral-500">Loading…</p>}

      {brands?.length === 0 && (
        <div className="border border-dashed rounded p-8 text-center">
          <p className="text-sm text-neutral-500 mb-4">No brands yet.</p>
          <Link href="/brands/new" className="bg-black text-white rounded px-3 py-2 text-sm">
            Create your first brand
          </Link>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {brands?.map((brand) => (
          <div
            key={brand.id}
            className="border rounded p-4 hover:bg-neutral-50 transition-colors"
          >
            <div className="flex items-start justify-between mb-2">
              <h3 className="font-medium text-lg">{brand.name}</h3>
              {brand.extracted_profile?.color?.[0] && (
                <div
                  className="w-6 h-6 rounded border"
                  style={{ backgroundColor: brand.extracted_profile.color[0].hex }}
                  title={brand.extracted_profile.color[0].name || "Brand color"}
                />
              )}
            </div>
            {brand.description && (
              <p className="text-sm text-neutral-600 mb-3 line-clamp-2">
                {brand.description}
              </p>
            )}
            {brand.extracted_profile?.style && (
              <p className="text-xs text-neutral-400 mb-3">
                Style: {brand.extracted_profile.style}
              </p>
            )}
            <div className="flex items-center justify-between">
              <Link
                href={`/intake?brand_id=${brand.id}`}
                className="text-sm text-blue-600 hover:underline"
              >
                Create campaign →
              </Link>
              <span className="text-xs text-neutral-400">
                {new Date(brand.created_at).toLocaleDateString()}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
