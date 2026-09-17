"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import ReactMarkdown from "react-markdown";
import { api } from "@/lib/api";

// Matches the app's existing text-sm/neutral styling — react-markdown renders plain
// HTML tags, which get no Tailwind Preflight styling here (no @tailwindcss/typography
// plugin installed), so each tag needs its className set explicitly or headings/lists
// render unstyled.
const markdownComponents = {
  p: (props: any) => <p className="mb-2 last:mb-0" {...props} />,
  strong: (props: any) => <strong className="font-semibold" {...props} />,
  ul: (props: any) => <ul className="list-disc pl-5 mb-2" {...props} />,
  ol: (props: any) => <ol className="list-decimal pl-5 mb-2" {...props} />,
  li: (props: any) => <li className="mb-1" {...props} />,
  h1: (props: any) => <h3 className="font-semibold mt-3 mb-1" {...props} />,
  h2: (props: any) => <h3 className="font-semibold mt-3 mb-1" {...props} />,
  h3: (props: any) => <h3 className="font-semibold mt-3 mb-1" {...props} />,
};

type ChatMessage = {
  role: "user" | "assistant";
  text: string;
  image_urls?: string[];
};

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
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [sending, setSending] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedItems, setExpandedItems] = useState<Set<number>>(new Set());
  const [planItemReferences, setPlanItemReferences] = useState<(string | null)[]>([]);
  const [uploadingItemIndex, setUploadingItemIndex] = useState<number | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const itemFileInputRefs = useRef<Record<number, HTMLInputElement | null>>({});

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
            image_urls: t.image_urls,
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
    if ((!text && selectedFiles.length === 0) || sending) return;

    setSending(true);
    setError(null);
    setPlan(null);

    try {
      // Upload images first if any
      let image_urls: string[] | undefined;
      if (selectedFiles.length > 0) {
        image_urls = await api.uploadMoodboardAssets(selectedFiles);
      }

      // Add user message to UI (with image URLs for display)
      setMessages((prev) => [...prev, { role: "user", text, image_urls }]);
      setInput("");
      setSelectedFiles([]);

      // Send message to backend
      const res = await api.sendScopeMessage(id, text, image_urls);
      if (res.kind === "plan") {
        setMessages((prev) => [...prev, { role: "assistant", text: res.summary }]);
        setPlan({ items: res.items, summary: res.summary });
        // Initialize reference array for plan items
        setPlanItemReferences(new Array(res.items.length).fill(null));
      } else {
        setMessages((prev) => [...prev, { role: "assistant", text: res.text }]);
      }
    } catch (err: any) {
      setError(err.message ?? String(err));
    } finally {
      setSending(false);
    }
  }

  async function handleItemReferenceUpload(itemIndex: number, e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadingItemIndex(itemIndex);
    setError(null);
    try {
      const { path } = await api.uploadVariantReference(file);
      setPlanItemReferences((prev) => {
        const next = [...prev];
        next[itemIndex] = path;
        return next;
      });
    } catch (err: any) {
      setError(err.message ?? String(err));
    } finally {
      setUploadingItemIndex(null);
    }
  }

  function handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(e.target.files || []);
    setSelectedFiles((prev) => [...prev, ...files]);
    // Reset input so same file can be selected again if removed
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }

  function removeFile(index: number) {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  }

  function toggleItem(index: number) {
    setExpandedItems((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(index)) {
        newSet.delete(index);
      } else {
        newSet.add(index);
      }
      return newSet;
    });
  }

  async function handleConfirm() {
    setConfirming(true);
    setError(null);
    try {
      await api.confirmScope(id, planItemReferences);
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
            className={`max-w-[85%] rounded px-3 py-2 text-sm ${
              m.role === "user" ? "self-end bg-black text-white" : "self-start bg-neutral-100"
            }`}
          >
            {m.image_urls && m.image_urls.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-2">
                {m.image_urls.map((url, idx) => (
                  <img
                    key={idx}
                    src={url}
                    alt={`Reference ${idx + 1}`}
                    className="max-w-[120px] max-h-[120px] object-cover rounded border"
                    onError={(e) => {
                      console.error('Failed to load image:', url);
                      e.currentTarget.style.display = 'none';
                    }}
                  />
                ))}
              </div>
            )}
            {m.text && m.role === "assistant" && (
              <ReactMarkdown components={markdownComponents}>{m.text}</ReactMarkdown>
            )}
            {m.text && m.role === "user" && <div className="whitespace-pre-wrap">{m.text}</div>}
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
            {plan.items.map((item, i) => {
              const isExpanded = expandedItems.has(i);
              return (
                <div key={i} className="bg-white border border-blue-100 rounded">
                  <button
                    type="button"
                    onClick={() => toggleItem(i)}
                    className="w-full p-2 flex items-center justify-between hover:bg-neutral-50 transition-colors"
                  >
                    <div className="flex items-center gap-1.5 flex-wrap">
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
                    <span className="text-neutral-400 text-sm">{isExpanded ? '−' : '+'}</span>
                  </button>
                  {isExpanded && (
                    <div className="px-2 pb-2 border-t border-neutral-100">
                      <p className="text-neutral-700 text-sm mt-2 mb-3">{item.concept}</p>
                      <div className="border-t pt-2">
                        <label className="text-xs text-neutral-500 block">
                          Style reference (optional)
                          <div className="text-xs text-neutral-400 mb-1">
                            Upload a reference image for the visual style of {item.count > 1 ? `all ${item.count} pieces` : 'this piece'}
                          </div>
                          <input
                            ref={(el) => (itemFileInputRefs.current[i] = el)}
                            type="file"
                            accept="image/*"
                            onChange={(e) => handleItemReferenceUpload(i, e)}
                            disabled={uploadingItemIndex === i || confirming}
                            className="text-xs mt-1"
                          />
                          {uploadingItemIndex === i && <span className="text-xs text-neutral-400 ml-2">Uploading...</span>}
                          {planItemReferences[i] && uploadingItemIndex !== i && (
                            <div className="text-xs text-green-600 mt-1">✓ Reference uploaded</div>
                          )}
                        </label>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
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

      {selectedFiles.length > 0 && (
        <div className="mb-3">
          <p className="text-xs text-neutral-500 mb-2">Moodboard images ({selectedFiles.length})</p>
          <div className="flex flex-wrap gap-2">
            {selectedFiles.map((file, i) => (
              <div key={i} className="relative group">
                <img
                  src={URL.createObjectURL(file)}
                  alt={file.name}
                  className="w-20 h-20 object-cover rounded border"
                />
                <button
                  type="button"
                  onClick={() => removeFile(i)}
                  className="absolute -top-1 -right-1 bg-red-600 text-white rounded-full w-5 h-5 text-xs opacity-0 group-hover:opacity-100 transition-opacity"
                  disabled={sending}
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      <form onSubmit={handleSend} className="flex flex-col gap-2 mb-4">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Describe your campaign or upload moodboard images…"
            className="flex-1 border rounded px-3 py-2 text-sm"
            disabled={sending || confirming}
          />
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            multiple
            onChange={handleFileSelect}
            className="hidden"
          />
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={sending || confirming}
            className="border rounded px-3 py-2 text-sm disabled:opacity-50 hover:bg-neutral-50"
            title="Add moodboard images"
          >
            📎
          </button>
          <button
            type="submit"
            disabled={(!input.trim() && selectedFiles.length === 0) || sending || confirming}
            className="bg-black text-white rounded px-4 py-2 text-sm disabled:opacity-50"
          >
            Send
          </button>
        </div>
        <p className="text-xs text-neutral-400">
          Upload visual references (moodboard, style inspiration, competitor examples) to help guide the creative direction
        </p>
      </form>
    </div>
  );
}
