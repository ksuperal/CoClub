"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";

type ChatMessage = { role: "user" | "assistant"; text: string };

type PlanItem = {
  media_type: string;
  target_platforms: string[];
  count: number;
  include_voiceover?: boolean;
  include_music?: boolean;
  concept: string;
};

const PLATFORM_LABELS: Record<string, string> = { instagram: "Instagram", tiktok: "TikTok", facebook: "Facebook" };

const OPENING_QUESTION =
  "How big a campaign do you want? Tell me roughly how many pieces, which platform(s) " +
  "(Instagram / TikTok / Facebook), and image or video — e.g. \"IG 9 posts\" or \"TikTok 2 " +
  "short videos with voiceover.\" I'll turn that into a concrete plan for you to confirm.";

export default function ScopePage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [plan, setPlan] = useState<{ items: PlanItem[]; summary: string } | null>(null);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    (async () => {
      try {
        const campaign = await api.getCampaign(id);
        if (campaign.status === "draft") {
          setMessages([{ role: "assistant", text: OPENING_QUESTION }]);
        } else if (campaign.status === "awaiting_scope") {
          const existing: ChatMessage[] = (campaign.scope_conversation ?? []).map((t: any) => ({
            role: t.role,
            text: t.text,
          }));
          setMessages(existing.length > 0 ? existing : [{ role: "assistant", text: OPENING_QUESTION }]);
          if (campaign.content_plan) {
            // A plan was already finalized on a previous visit — show it again for confirmation.
            setPlan({ items: campaign.content_plan, summary: existing[existing.length - 1]?.text ?? "" });
          }
        } else {
          // Scoping is done (or was skipped) — nothing to do here anymore.
          router.replace(`/campaign/${id}/prompts`);
          return;
        }
        setLoading(false);
      } catch (err: any) {
        setError(err.message ?? String(err));
        setLoading(false);
      }
    })();
  }, [id, router]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, sending]);

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || sending) return;

    setMessages((prev) => [...prev, { role: "user", text }]);
    setInput("");
    setSending(true);
    setError(null);
    setPlan(null);
    try {
      const res = await api.sendScopeMessage(id, text);
      if (res.kind === "plan") {
        setMessages((prev) => [...prev, { role: "assistant", text: res.summary }]);
        setPlan({ items: res.items, summary: res.summary });
      } else {
        setMessages((prev) => [...prev, { role: "assistant", text: res.text }]);
      }
    } catch (err: any) {
      setError(err.message ?? String(err));
    } finally {
      setSending(false);
    }
  }

  async function handleConfirm() {
    setConfirming(true);
    setError(null);
    try {
      await api.confirmScope(id);
      router.push(`/campaign/${id}/prompts`);
    } catch (err: any) {
      setError(err.message ?? String(err));
      setConfirming(false);
    }
  }

  if (loading) return <p className="text-sm text-neutral-500">Loading…</p>;

  return (
    <div className="flex flex-col h-[calc(100vh-3rem)] max-w-2xl mx-auto">
      <Link href="/home" className="text-sm text-neutral-500 mb-2">
        ← Back to campaigns
      </Link>
      <h1 className="text-xl font-semibold mb-1">How big a campaign?</h1>
      <p className="text-xs text-neutral-400 mb-4">
        Nothing is written or generated yet — just deciding scope. Describe it in your own
        words; I'll ask a follow-up if I need more, or propose a plan once I have enough.
      </p>

      <div ref={scrollRef} className="flex-1 overflow-y-auto border rounded p-4 flex flex-col gap-3 mb-4">
        {messages.map((m, i) => (
          <div
            key={i}
            className={`max-w-[85%] rounded px-3 py-2 text-sm whitespace-pre-wrap ${
              m.role === "user" ? "self-end bg-black text-white" : "self-start bg-neutral-100"
            }`}
          >
            {m.text}
          </div>
        ))}
        {sending && <p className="self-start text-sm text-neutral-400">Thinking…</p>}
      </div>

      {plan && (
        <div className="border border-blue-200 bg-blue-50 rounded p-3 mb-4 text-sm">
          <p className="font-medium mb-3">
            Plan ready — {plan.items.reduce((sum, item) => sum + item.count, 0)} piece(s) total
          </p>
          <div className="flex flex-col gap-2 mb-3">
            {plan.items.map((item, i) => (
              <div key={i} className="bg-white border border-blue-100 rounded p-2">
                <div className="flex items-center gap-1.5 flex-wrap mb-1">
                  <span className="text-xs font-semibold bg-blue-100 text-blue-700 rounded px-1.5 py-0.5">
                    {item.count}× {item.media_type}
                  </span>
                  {item.target_platforms.map((p) => (
                    <span key={p} className="text-xs text-neutral-600 border rounded px-1.5 py-0.5">
                      {PLATFORM_LABELS[p] ?? p}
                    </span>
                  ))}
                  {item.include_voiceover && (
                    <span className="text-xs text-neutral-500 border rounded px-1.5 py-0.5">voiceover</span>
                  )}
                  {item.include_music && (
                    <span className="text-xs text-neutral-500 border rounded px-1.5 py-0.5">music</span>
                  )}
                </div>
                <p className="text-neutral-700">{item.concept}</p>
              </div>
            ))}
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleConfirm}
              disabled={confirming}
              className="bg-black text-white rounded px-3 py-1.5 text-sm disabled:opacity-50"
            >
              {confirming ? "Starting…" : "Looks good — continue"}
            </button>
            <span className="text-xs text-neutral-500">
              or keep typing below to change it
            </span>
          </div>
        </div>
      )}

      {error && <p className="text-red-600 text-sm mb-2">{error}</p>}

      <form onSubmit={handleSend} className="flex gap-2 mb-4">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type a message…"
          className="flex-1 border rounded px-3 py-2 text-sm"
          disabled={sending || confirming}
        />
        <button
          type="submit"
          disabled={!input.trim() || sending || confirming}
          className="bg-black text-white rounded px-4 py-2 text-sm disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </div>
  );
}
