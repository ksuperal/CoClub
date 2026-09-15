"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { supabase } from "@/lib/supabaseClient";

type Product = {
  id: string;
  brand_id: string;
  name: string;
  description_text: string | null;
  asset_paths?: string[];
  extracted_profile: any;
  created_at: string;
};

type Brand = {
  id: string;
  name: string;
};

export default function ProductsPage() {
  const router = useRouter();
  const [products, setProducts] = useState<Product[] | null>(null);
  const [brands, setBrands] = useState<Brand[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      api.listProducts(),
      api.listBrands(),
    ])
      .then(([productsData, brandsData]) => {
        setProducts(productsData);
        setBrands(brandsData);
      })
      .catch((err) => setError(err.message ?? String(err)));
  }, []);

  async function handleSignOut() {
    await supabase.auth.signOut();
    router.replace("/login");
  }

  async function handleDelete(productId: string, productName: string) {
    if (!confirm(`Remove "${productName}" from your product library?\n\nThe product will be hidden from the library but campaigns using it will continue to work.`)) {
      return;
    }

    setDeleting(productId);
    setError(null);

    try {
      await api.deleteProduct(productId);
      // Remove from list
      setProducts((prev) => prev?.filter((p) => p.id !== productId) ?? null);
    } catch (err: any) {
      setError(err.message ?? String(err));
    } finally {
      setDeleting(null);
    }
  }

  function getBrandName(brandId: string): string {
    return brands.find((b) => b.id === brandId)?.name || "Unknown brand";
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold">Product Library</h1>
          <p className="text-sm text-neutral-500 mt-1">
            Manage your product presets for reuse across campaigns
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/products/new" className="bg-black text-white rounded px-3 py-2 text-sm">
            + Add Product
          </Link>
          <Link href="/brands" className="text-sm text-neutral-500">
            Brands
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

      {products === null && !error && <p className="text-sm text-neutral-500">Loading…</p>}

      {products?.length === 0 && (
        <div className="border border-dashed rounded p-8 text-center">
          <p className="text-sm text-neutral-500 mb-4">No products yet.</p>
          <Link href="/products/new" className="bg-black text-white rounded px-3 py-2 text-sm">
            Create your first product
          </Link>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {products?.map((product) => (
          <div
            key={product.id}
            className="border rounded p-4 hover:bg-neutral-50 transition-colors"
          >
            {product.asset_paths?.[0] && (
              <div className="mb-3">
                <img
                  src={supabase.storage.from("product-assets").getPublicUrl(product.asset_paths[0]).data.publicUrl}
                  alt={product.name}
                  className="w-full h-32 object-cover rounded"
                  onError={(e) => {
                    e.currentTarget.style.display = 'none';
                  }}
                />
              </div>
            )}
            <h3 className="font-medium text-lg mb-1">{product.name}</h3>
            <p className="text-xs text-neutral-400 mb-2">
              {getBrandName(product.brand_id)}
            </p>
            {product.description_text && (
              <p className="text-sm text-neutral-600 mb-3 line-clamp-2">
                {product.description_text}
              </p>
            )}
            {product.extracted_profile?.category && (
              <p className="text-xs text-neutral-400 mb-3">
                Category: {product.extracted_profile.category}
              </p>
            )}
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-3">
                <Link
                  href={`/intake?brand_id=${product.brand_id}&product_id=${product.id}`}
                  className="text-sm text-blue-600 hover:underline"
                >
                  Create campaign →
                </Link>
                <Link
                  href={`/products/${product.id}/edit`}
                  className="text-xs text-neutral-500 hover:text-neutral-700"
                >
                  Edit
                </Link>
                <button
                  onClick={() => handleDelete(product.id, product.name)}
                  disabled={deleting === product.id}
                  className="text-xs text-red-600 hover:text-red-700 disabled:opacity-50"
                >
                  {deleting === product.id ? "Removing..." : "Remove"}
                </button>
              </div>
              <span className="text-xs text-neutral-400">
                {new Date(product.created_at).toLocaleDateString()}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
