"use client";

import { useMemo, useState } from "react";

type Snapshot = {
  id: string;
  post_id: string;
  variant_id: string;
  platform: string;
  likes: number;
  comments: number;
  shares: number;
  views: number;
  engagement_score: number;
  fetched_at: string;
};

// Fixed categorical order — validated together (node scripts/validate_palette.js
// "#2a78d6,#eb6834,#1baf7a" --mode light): PASS on lightness/chroma/CVD-separation/
// normal-vision floor; aqua (tiktok) sits below 3:1 contrast on this light surface,
// which is why it always gets a direct label + the table view, never color alone.
const PLATFORM_COLOR: Record<string, string> = {
  facebook: "#2a78d6",
  instagram: "#eb6834",
  tiktok: "#1baf7a",
};
const PLATFORM_ORDER = ["facebook", "instagram", "tiktok"];

const INK_PRIMARY = "#0b0b0b";
const INK_SECONDARY = "#52514e";
const INK_MUTED = "#898781";
const GRIDLINE = "#e1e0d9";
const SURFACE = "#fcfcfb";

type Point = { t: number; score: number; fetchedAt: string };
type Series = { platform: string; points: Point[] };

// Groups snapshots by platform, then by fetched_at rounded to the nearest minute
// (a single "Refresh metrics" click inserts one row per post in quick succession —
// this merges that batch into one point per platform instead of a jittery cluster),
// summing engagement_score within each bucket.
function aggregate(snapshots: Snapshot[]): Series[] {
  const byPlatform = new Map<string, Map<number, { score: number; fetchedAt: string }>>();
  for (const s of snapshots) {
    const bucket = Math.floor(new Date(s.fetched_at).getTime() / 60000);
    if (!byPlatform.has(s.platform)) byPlatform.set(s.platform, new Map());
    const buckets = byPlatform.get(s.platform)!;
    const existing = buckets.get(bucket);
    if (existing) existing.score += s.engagement_score;
    else buckets.set(bucket, { score: s.engagement_score, fetchedAt: s.fetched_at });
  }

  return PLATFORM_ORDER.filter((p) => byPlatform.has(p)).map((platform) => {
    const points = [...byPlatform.get(platform)!.entries()]
      .map(([bucket, v]) => ({ t: bucket * 60000, score: v.score, fetchedAt: v.fetchedAt }))
      .sort((a, b) => a.t - b.t);
    return { platform, points };
  });
}

const WIDTH = 640;
const HEIGHT = 280;
const MARGIN = { top: 16, right: 16, bottom: 28, left: 40 };
const PLOT_W = WIDTH - MARGIN.left - MARGIN.right;
const PLOT_H = HEIGHT - MARGIN.top - MARGIN.bottom;

export default function MetricsChart({ snapshots }: { snapshots: Snapshot[] }) {
  const [showTable, setShowTable] = useState(false);
  const [hoverT, setHoverT] = useState<number | null>(null);

  const series = useMemo(() => aggregate(snapshots), [snapshots]);
  const allPoints = series.flatMap((s) => s.points);

  if (allPoints.length === 0) {
    return <p className="text-sm text-neutral-400">No metrics yet — click "Refresh metrics" above.</p>;
  }

  const tMin = Math.min(...allPoints.map((p) => p.t));
  const tMax = Math.max(...allPoints.map((p) => p.t));
  const tSpan = tMax - tMin || 1;
  const scoreMax = Math.max(1, ...allPoints.map((p) => p.score));

  const x = (t: number) => MARGIN.left + ((t - tMin) / tSpan) * PLOT_W;
  const y = (score: number) => MARGIN.top + PLOT_H - (score / scoreMax) * PLOT_H;

  // Nearest time bucket to the pointer, across all series — drives the crosshair.
  const allTimes = [...new Set(allPoints.map((p) => p.t))].sort((a, b) => a - b);
  const nearestT =
    hoverT === null ? null : allTimes.reduce((best, t) => (Math.abs(t - hoverT) < Math.abs(best - hoverT) ? t : best));

  const yTicks = [0, 0.5, 1].map((f) => Math.round(scoreMax * f));

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        {series.length >= 2 && (
          <div className="flex items-center gap-3 text-xs">
            {series.map((s) => (
              <span key={s.platform} className="flex items-center gap-1" style={{ color: INK_SECONDARY }}>
                <span
                  className="inline-block w-3 h-0.5 rounded"
                  style={{ backgroundColor: PLATFORM_COLOR[s.platform] ?? INK_MUTED }}
                />
                {s.platform}
              </span>
            ))}
          </div>
        )}
        <button
          onClick={() => setShowTable((v) => !v)}
          className="text-xs border rounded px-2 py-1 ml-auto"
          style={{ color: INK_SECONDARY }}
        >
          {showTable ? "View as chart" : "View as table"}
        </button>
      </div>

      {showTable ? (
        <table className="w-full text-xs border-collapse">
          <thead>
            <tr className="text-left" style={{ color: INK_SECONDARY }}>
              <th className="border-b p-1">Platform</th>
              <th className="border-b p-1">Fetched</th>
              <th className="border-b p-1">Engagement score</th>
            </tr>
          </thead>
          <tbody>
            {series.flatMap((s) =>
              s.points.map((p, i) => (
                <tr key={`${s.platform}-${i}`}>
                  <td className="p-1 flex items-center gap-1">
                    <span
                      className="inline-block w-2.5 h-2.5 rounded-full"
                      style={{ backgroundColor: PLATFORM_COLOR[s.platform] ?? INK_MUTED }}
                    />
                    {s.platform}
                  </td>
                  <td className="p-1" style={{ color: INK_SECONDARY }}>
                    {new Date(p.fetchedAt).toLocaleString()}
                  </td>
                  <td className="p-1 font-medium" style={{ color: INK_PRIMARY }}>
                    {p.score}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      ) : (
        <svg
          viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
          className="w-full h-auto"
          style={{ backgroundColor: SURFACE }}
          onMouseMove={(e) => {
            const rect = e.currentTarget.getBoundingClientRect();
            const px = ((e.clientX - rect.left) / rect.width) * WIDTH;
            setHoverT(tMin + ((px - MARGIN.left) / PLOT_W) * tSpan);
          }}
          onMouseLeave={() => setHoverT(null)}
        >
          {/* gridlines + y-axis ticks — recessive, one step off the surface */}
          {yTicks.map((v, i) => (
            <g key={i}>
              <line
                x1={MARGIN.left}
                x2={WIDTH - MARGIN.right}
                y1={y(v)}
                y2={y(v)}
                stroke={GRIDLINE}
                strokeWidth={1}
              />
              <text x={MARGIN.left - 6} y={y(v)} textAnchor="end" dominantBaseline="middle" fontSize={10} fill={INK_MUTED}>
                {v.toLocaleString()}
              </text>
            </g>
          ))}
          {/* baseline */}
          <line
            x1={MARGIN.left}
            x2={WIDTH - MARGIN.right}
            y1={MARGIN.top + PLOT_H}
            y2={MARGIN.top + PLOT_H}
            stroke={INK_MUTED}
            strokeWidth={1}
          />

          {/* x-axis: min/mid/max time so the chart reads without hovering */}
          {[tMin, (tMin + tMax) / 2, tMax].map((t, i) => (
            <text
              key={i}
              x={x(t)}
              y={MARGIN.top + PLOT_H + 18}
              textAnchor={i === 0 ? "start" : i === 2 ? "end" : "middle"}
              fontSize={9}
              fill={INK_MUTED}
            >
              {new Date(t).toLocaleDateString(undefined, { month: "short", day: "numeric" })}
            </text>
          ))}

          {/* crosshair — solid hairline, tracks the pointer's nearest time bucket */}
          {nearestT !== null && (
            <line
              x1={x(nearestT)}
              x2={x(nearestT)}
              y1={MARGIN.top}
              y2={MARGIN.top + PLOT_H}
              stroke={INK_MUTED}
              strokeWidth={1}
            />
          )}

          {series.map((s) => {
            const color = PLATFORM_COLOR[s.platform] ?? INK_MUTED;
            const path = s.points.map((p, i) => `${i === 0 ? "M" : "L"} ${x(p.t)} ${y(p.score)}`).join(" ");
            const last = s.points[s.points.length - 1];
            return (
              <g key={s.platform}>
                {s.points.length > 1 && <path d={path} fill="none" stroke={color} strokeWidth={2} strokeLinejoin="round" strokeLinecap="round" />}
                {s.points.map((p, i) => (
                  <circle key={i} cx={x(p.t)} cy={y(p.score)} r={4} fill={color} stroke={SURFACE} strokeWidth={2} />
                ))}
                {/* direct end-label — required for tiktok (aqua) since it's below
                    3:1 text contrast on this surface; kept for all series for
                    consistency, since labels never carry the series color anyway */}
                <text x={x(last.t) + 6} y={y(last.score)} fontSize={10} fill={INK_PRIMARY} dominantBaseline="middle">
                  {s.platform}
                </text>
              </g>
            );
          })}

          {/* tooltip: one readout, every series, at the nearest x */}
          {nearestT !== null && (
            <g>
              {(() => {
                const rows = series
                  .map((s) => ({ platform: s.platform, point: s.points.find((p) => p.t === nearestT) }))
                  .filter((r): r is { platform: string; point: Point } => !!r.point);
                if (rows.length === 0) return null;
                const boxW = 150;
                const boxH = 16 + rows.length * 14;
                const boxX = Math.min(x(nearestT) + 8, WIDTH - MARGIN.right - boxW);
                const boxY = MARGIN.top;
                return (
                  <g transform={`translate(${boxX}, ${boxY})`}>
                    <rect width={boxW} height={boxH} fill={SURFACE} stroke={GRIDLINE} rx={4} />
                    <text x={8} y={14} fontSize={9} fill={INK_MUTED}>
                      {new Date(rows[0].point.fetchedAt).toLocaleString()}
                    </text>
                    {rows.map((r, i) => (
                      <g key={r.platform} transform={`translate(8, ${28 + i * 14})`}>
                        <line x1={0} x2={10} y1={-3} y2={-3} stroke={PLATFORM_COLOR[r.platform] ?? INK_MUTED} strokeWidth={2} />
                        <text x={14} y={0} fontSize={10} fill={INK_PRIMARY} fontWeight={600}>
                          {r.point.score}
                        </text>
                        <text x={40} y={0} fontSize={9} fill={INK_SECONDARY}>
                          {r.platform}
                        </text>
                      </g>
                    ))}
                  </g>
                );
              })()}
            </g>
          )}
        </svg>
      )}
    </div>
  );
}
