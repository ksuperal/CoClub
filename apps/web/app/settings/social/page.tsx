"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";

type SocialAccount = {
  id: string;
  platform: "facebook" | "instagram" | "tiktok";
  external_account_name: string | null;
  status: string;
};

const PLATFORMS: { key: SocialAccount["platform"]; label: string; connectAs: "facebook" | "tiktok"; requirement: string }[] = [
  {
    key: "facebook",
    label: "Facebook",
    connectAs: "facebook",
    requirement: "Requires a Facebook Page — personal profiles can't be posted to.",
  },
  {
    key: "instagram",
    label: "Instagram",
    connectAs: "facebook",
    requirement: "Requires a Business or Creator account, linked to a Facebook Page.",
  },
  {
    key: "tiktok",
    label: "TikTok",
    connectAs: "tiktok",
    requirement: "Requires a Business or Creator account (switch for free in the TikTok app's settings).",
  },
];

export default function SocialSettingsPage() {
  const [accounts, setAccounts] = useState<SocialAccount[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [banner, setBanner] = useState<string | null>(null);
  const [connecting, setConnecting] = useState<string | null>(null);

  async function refresh() {
    try {
      const a = await api.listSocialAccounts();
      setAccounts(a);
    } catch (err: any) {
      setError(err.message ?? String(err));
    }
  }

  useEffect(() => {
    // Read the ?connected=/?error= params the OAuth callback redirects back with.
    // window.location.search instead of useSearchParams avoids a Suspense boundary
    // for what's otherwise a plain client-rendered settings page.
    const params = new URLSearchParams(window.location.search);
    const connected = params.get("connected");
    const err = params.get("error");
    if (connected) setBanner(`Connected: ${connected}`);
    if (err) setError(`Connection failed: ${err}`);
    if (connected || err) window.history.replaceState({}, "", "/settings/social");

    refresh();
  }, []);

  async function handleConnect(connectAs: "facebook" | "tiktok") {
    setConnecting(connectAs);
    setError(null);
    try {
      const { authorize_url } = await api.connectSocial(connectAs);
      window.location.href = authorize_url;
    } catch (err: any) {
      setError(err.message ?? String(err));
      setConnecting(null);
    }
  }

  async function handleDisconnect(id: string) {
    try {
      await api.disconnectSocial(id);
      await refresh();
    } catch (err: any) {
      setError(err.message ?? String(err));
    }
  }

  return (
    <div>
      <Link href="/home" className="text-sm text-neutral-500">
        ← Back to campaigns
      </Link>
      <h1 className="text-xl font-semibold mb-2 mt-2">Social accounts</h1>
      <p className="text-sm text-neutral-500 mb-6">
        Connect the accounts campaigns should post to. Facebook and Instagram connect together
        since Instagram posting uses your linked Facebook Page.
      </p>

      {banner && <p className="text-green-700 text-sm mb-4">{banner}</p>}
      {error && <p className="text-red-600 text-sm mb-4">{error}</p>}

      <div className="flex flex-col gap-3">
        {PLATFORMS.map((p) => {
          const account = accounts?.find((a) => a.platform === p.key);
          return (
            <div key={p.key} className="border rounded p-3 flex items-center justify-between">
              <div>
                <p className="font-medium">{p.label}</p>
                {account ? (
                  <p className="text-sm text-neutral-500">
                    Connected as {account.external_account_name ?? account.id}
                  </p>
                ) : (
                  <>
                    <p className="text-sm text-neutral-400">Not connected</p>
                    <p className="text-xs text-neutral-400 mt-1">{p.requirement}</p>
                  </>
                )}
              </div>
              {account ? (
                <button
                  onClick={() => handleDisconnect(account.id)}
                  className="border rounded px-3 py-2 text-sm"
                >
                  Disconnect
                </button>
              ) : (
                <button
                  onClick={() => handleConnect(p.connectAs)}
                  disabled={connecting === p.connectAs}
                  className="bg-black text-white rounded px-3 py-2 text-sm disabled:opacity-50"
                >
                  {connecting === p.connectAs ? "Redirecting…" : "Connect"}
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
