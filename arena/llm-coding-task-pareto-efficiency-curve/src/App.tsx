import { useState, useMemo, useRef } from "react";
import { MODELS_RAW, computeEffectivePrice, computeParetoFrontier } from "./data/models";

type EnrichedModel = (typeof MODELS_RAW)[0] & {
  effectivePrice: number;
  isPareto: boolean;
  logPrice: number;
};

// ─── Preset scenarios ──────────────────────────────────────────────────────
const PRESETS = [
  { label: "Casual Chat (1:1, no cache)", ioRatio: 1, cache: 0, thinking: 100 },
  { label: "Coding Agent (1:50, 85% cache)", ioRatio: 50, cache: 85, thinking: 100 },
  { label: "RAG System (1:10, 70% cache)", ioRatio: 10, cache: 70, thinking: 100 },
  { label: "Document Analysis (100:1, 95% cache)", ioRatio: 100, cache: 95, thinking: 100 },
  { label: "Vendor Default (1:5, no cache)", ioRatio: 5, cache: 0, thinking: 100 },
];

// ─── Provider colour map ───────────────────────────────────────────────────
const PROVIDER_COLORS: Record<string, string> = {
  Anthropic: "#D97706",
  Google: "#3B82F6",
  OpenAI: "#10B981",
  xAI: "#A78BFA",
  DeepSeek: "#F87171",
  Alibaba: "#FBBF24",
};

const providerColor = (provider: string) => PROVIDER_COLORS[provider] ?? "#94A3B8";

// ─── Chart dimensions ─────────────────────────────────────────────────────
const MARGIN = { top: 30, right: 120, bottom: 60, left: 70 };
const CHART_W = 900;
const CHART_H = 500;
const INNER_W = CHART_W - MARGIN.left - MARGIN.right;
const INNER_H = CHART_H - MARGIN.top - MARGIN.bottom;

const ELO_MIN = 1390;
const ELO_MAX = 1570;
const PRICE_LOG_MIN = Math.log10(0.07);
const PRICE_LOG_MAX = Math.log10(55);

const X_TICKS = [50, 30, 20, 10, 7, 5, 4, 3, 2, 1, 0.7, 0.5, 0.4, 0.3, 0.2, 0.1];
const Y_TICKS = [1400, 1420, 1440, 1460, 1480, 1500, 1520, 1540, 1560];

function xScale(price: number): number {
  const log = Math.log10(Math.max(price, 0.01));
  // reversed: high price = left, low price = right
  return INNER_W * (1 - (log - PRICE_LOG_MIN) / (PRICE_LOG_MAX - PRICE_LOG_MIN));
}

function yScale(elo: number): number {
  return INNER_H * (1 - (elo - ELO_MIN) / (ELO_MAX - ELO_MIN));
}

// ─── Enrich models ────────────────────────────────────────────────────────
function enrichModels(ioRatio: number, cacheRate: number, thinkingOverhead: number): EnrichedModel[] {
  const withPrice = MODELS_RAW.map((m) => ({
    ...m,
    effectivePrice: computeEffectivePrice(m, ioRatio, cacheRate, thinkingOverhead),
    isPareto: false,
    logPrice: 0,
  }));
  const paretoNames = new Set(computeParetoFrontier(withPrice));
  return withPrice.map((m) => ({
    ...m,
    isPareto: paretoNames.has(m.name),
    logPrice: Math.log10(Math.max(m.effectivePrice, 0.01)),
  }));
}

// ─── Main App ─────────────────────────────────────────────────────────────
export default function App() {
  const [ioRatio, setIoRatio] = useState(50);
  const [cacheRate, setCacheRate] = useState(85);
  const [thinkingOverhead, setThinkingOverhead] = useState(100);
  const [activePreset, setActivePreset] = useState<number | null>(1);
  const [tooltip, setTooltip] = useState<{ model: EnrichedModel; x: number; y: number } | null>(null);
  const svgRef = useRef<SVGSVGElement>(null);

  const applyPreset = (idx: number) => {
    const p = PRESETS[idx];
    setIoRatio(p.ioRatio);
    setCacheRate(p.cache);
    setThinkingOverhead(p.thinking);
    setActivePreset(idx);
  };

  const models = useMemo(() => enrichModels(ioRatio, cacheRate, thinkingOverhead), [ioRatio, cacheRate, thinkingOverhead]);
  const paretoModels = useMemo(() => models.filter((m) => m.isPareto).sort((a, b) => a.effectivePrice - b.effectivePrice), [models]);

  // Pareto line path
  const paretoPath = useMemo(() => {
    if (paretoModels.length < 2) return "";
    return paretoModels
      .map((m, i) => {
        const x = xScale(m.effectivePrice);
        const y = yScale(m.eloScore);
        return `${i === 0 ? "M" : "L"}${x},${y}`;
      })
      .join(" ");
  }, [paretoModels]);

  return (
    <div className="min-h-screen bg-[#0f1117] text-white font-sans select-none">
      {/* ── Header ── */}
      <div className="border-b border-slate-700/50 px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-blue-600 flex items-center justify-center">
            <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <div>
            <h1 className="text-lg font-bold text-white tracking-tight">Arena Coding Leaderboard — Pareto Efficiency Curve</h1>
            <p className="text-xs text-slate-400">Arena ELO Score vs. Effective Cost per Million Tokens · Data from arena.ai/leaderboard/code</p>
          </div>
        </div>
      </div>

      {/* ── Controls ── */}
      <div className="border-b border-slate-700/50 px-6 py-4 space-y-4 bg-[#12151c]">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* I/O Ratio */}
          <SliderControl
            label="Input:Output Token Ratio"
            display={`1:${ioRatio}`}
            value={ioRatio}
            min={1}
            max={200}
            step={1}
            onChange={(v) => { setIoRatio(v); setActivePreset(null); }}
          />
          {/* Cache hit rate */}
          <SliderControl
            label="Cache Hit Rate (%)"
            display={`${cacheRate}%`}
            value={cacheRate}
            min={0}
            max={100}
            step={5}
            onChange={(v) => { setCacheRate(v); setActivePreset(null); }}
          />
          {/* Thinking overhead */}
          <SliderControl
            label="Thinking Token Overhead (%)"
            display={`${thinkingOverhead}%`}
            value={thinkingOverhead}
            min={0}
            max={300}
            step={10}
            onChange={(v) => { setThinkingOverhead(v); setActivePreset(null); }}
          />
        </div>

        {/* Preset buttons */}
        <div className="flex flex-wrap gap-2">
          {PRESETS.map((p, i) => (
            <button
              key={i}
              onClick={() => applyPreset(i)}
              className={`px-3 py-1.5 rounded text-xs font-medium border transition-all ${
                activePreset === i
                  ? "bg-slate-100 text-slate-900 border-slate-100"
                  : "bg-transparent text-slate-300 border-slate-600 hover:border-slate-400 hover:text-white"
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* ── SVG Chart ── */}
      <div className="px-4 pt-4 overflow-x-auto">
        <div className="relative" style={{ minWidth: CHART_W }}>
          <svg
            ref={svgRef}
            width="100%"
            viewBox={`0 0 ${CHART_W} ${CHART_H}`}
            style={{ display: "block", margin: "0 auto", maxWidth: CHART_W }}
            onMouseLeave={() => setTooltip(null)}
          >
            <g transform={`translate(${MARGIN.left},${MARGIN.top})`}>
              {/* ── Grid ── */}
              {Y_TICKS.map((elo) => (
                <line
                  key={elo}
                  x1={0}
                  x2={INNER_W}
                  y1={yScale(elo)}
                  y2={yScale(elo)}
                  stroke="rgba(148,163,184,0.1)"
                  strokeWidth={1}
                />
              ))}
              {X_TICKS.map((price) => (
                <line
                  key={price}
                  x1={xScale(price)}
                  x2={xScale(price)}
                  y1={0}
                  y2={INNER_H}
                  stroke="rgba(148,163,184,0.1)"
                  strokeWidth={1}
                />
              ))}

              {/* ── Axes ── */}
              <line x1={0} x2={INNER_W} y1={INNER_H} y2={INNER_H} stroke="#475569" strokeWidth={1} />
              <line x1={0} x2={0} y1={0} y2={INNER_H} stroke="#475569" strokeWidth={1} />

              {/* ── X tick labels ── */}
              {X_TICKS.map((price) => (
                <text
                  key={price}
                  x={xScale(price)}
                  y={INNER_H + 18}
                  fill="#94A3B8"
                  fontSize={10}
                  textAnchor="middle"
                  fontFamily="ui-monospace, monospace"
                >
                  ${price >= 1 ? price : price}
                </text>
              ))}

              {/* ── Y tick labels ── */}
              {Y_TICKS.map((elo) => (
                <text
                  key={elo}
                  x={-8}
                  y={yScale(elo) + 4}
                  fill="#94A3B8"
                  fontSize={10}
                  textAnchor="end"
                  fontFamily="ui-monospace, monospace"
                >
                  {elo.toLocaleString()}
                </text>
              ))}

              {/* ── Axis labels ── */}
              <text
                x={INNER_W / 2}
                y={INNER_H + 48}
                fill="#94A3B8"
                fontSize={12}
                textAnchor="middle"
              >
                $ Price per million tokens (log scale, higher price → left)
              </text>
              <text
                x={-INNER_H / 2}
                y={-52}
                fill="#94A3B8"
                fontSize={12}
                textAnchor="middle"
                transform={`rotate(-90)`}
              >
                Arena Elo Score (Coding)
              </text>

              {/* ── Pareto frontier line ── */}
              {paretoPath && (
                <path
                  d={paretoPath}
                  fill="none"
                  stroke="#F87171"
                  strokeWidth={2}
                  strokeDasharray="8 5"
                  opacity={0.9}
                />
              )}

              {/* ── Non-pareto dots ── */}
              {models
                .filter((m) => !m.isPareto)
                .map((m) => {
                  const x = xScale(m.effectivePrice);
                  const y = yScale(m.eloScore);
                  const color = providerColor(m.provider);
                  const isHovered = tooltip?.model.name === m.name;
                  return (
                    <g key={m.name}>
                      <circle
                        cx={x}
                        cy={y}
                        r={isHovered ? 9 : 5}
                        fill={color}
                        opacity={isHovered ? 1 : 0.7}
                        stroke="rgba(255,255,255,0.2)"
                        strokeWidth={1}
                        style={{ cursor: "pointer", transition: "r 0.1s" }}
                        onMouseEnter={(e) => {
                          const rect = svgRef.current!.getBoundingClientRect();
                          setTooltip({ model: m, x: e.clientX - rect.left, y: e.clientY - rect.top });
                        }}
                        onMouseMove={(e) => {
                          const rect = svgRef.current!.getBoundingClientRect();
                          setTooltip({ model: m, x: e.clientX - rect.left, y: e.clientY - rect.top });
                        }}
                        onMouseLeave={() => setTooltip(null)}
                      />
                      {isHovered && (
                        <text x={x + 9} y={y + 4} fill="#E2E8F0" fontSize={11} fontFamily="ui-monospace,monospace" pointerEvents="none">
                          {m.shortName}
                        </text>
                      )}
                    </g>
                  );
                })}

              {/* ── Pareto dots + labels ── */}
              {paretoModels.map((m) => {
                const x = xScale(m.effectivePrice);
                const y = yScale(m.eloScore);
                const color = providerColor(m.provider);
                const isHovered = tooltip?.model.name === m.name;
                return (
                  <g key={m.name}>
                    {/* outer glow ring */}
                    <circle cx={x} cy={y} r={12} fill="none" stroke={color} strokeWidth={1} opacity={0.3} />
                    <circle
                      cx={x}
                      cy={y}
                      r={isHovered ? 10 : 7}
                      fill={color}
                      stroke="#fff"
                      strokeWidth={1.5}
                      opacity={isHovered ? 1 : 0.9}
                      style={{ cursor: "pointer", transition: "r 0.1s" }}
                      onMouseEnter={(e) => {
                        const rect = svgRef.current!.getBoundingClientRect();
                        setTooltip({ model: m, x: e.clientX - rect.left, y: e.clientY - rect.top });
                      }}
                      onMouseMove={(e) => {
                        const rect = svgRef.current!.getBoundingClientRect();
                        setTooltip({ model: m, x: e.clientX - rect.left, y: e.clientY - rect.top });
                      }}
                      onMouseLeave={() => setTooltip(null)}
                    />
                    {/* Label for pareto models */}
                    <text
                      x={x + 11}
                      y={y + 4}
                      fill="#CBD5E1"
                      fontSize={11}
                      fontFamily="ui-monospace,monospace"
                      pointerEvents="none"
                    >
                      {m.shortName}
                    </text>
                  </g>
                );
              })}
            </g>

            {/* ── Floating Tooltip ── */}
            {tooltip && (
              <TooltipBox tooltip={tooltip} svgW={CHART_W} svgH={CHART_H} />
            )}
          </svg>
        </div>
      </div>

      {/* ── Legend ── */}
      <div className="border-t border-slate-700/50 px-6 py-3 mt-2">
        <div className="flex flex-wrap items-center gap-5">
          <div className="flex items-center gap-2">
            <svg width="28" height="10">
              <line x1="0" y1="5" x2="28" y2="5" stroke="#F87171" strokeWidth="2" strokeDasharray="6 4" />
            </svg>
            <span className="text-xs text-slate-400">Pareto Frontier</span>
          </div>
          <div className="flex items-center gap-1.5">
            <svg width="14" height="14">
              <circle cx="7" cy="7" r="5" fill="#94A3B8" stroke="white" strokeWidth="1.5" />
            </svg>
            <span className="text-xs text-slate-400">Pareto Efficient</span>
          </div>
          <div className="flex items-center gap-1.5">
            <svg width="14" height="14">
              <circle cx="7" cy="7" r="4" fill="#94A3B8" opacity="0.7" />
            </svg>
            <span className="text-xs text-slate-400">Other Models</span>
          </div>
          {Object.entries(PROVIDER_COLORS).map(([provider, color]) => (
            <div key={provider} className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full inline-block" style={{ background: color }} />
              <span className="text-xs text-slate-400">{provider}</span>
            </div>
          ))}
          <div className="ml-auto text-xs text-slate-500">
            {models.length} models · <span className="text-yellow-400">{paretoModels.length}</span> Pareto efficient
          </div>
        </div>
      </div>

      {/* ── Pareto Table ── */}
      <div className="px-6 pb-10">
        <h2 className="text-sm font-semibold text-slate-300 mb-3 mt-2">
          📊 Pareto-Efficient Models (sorted cheapest → most expensive)
        </h2>
        <div className="overflow-x-auto rounded-lg border border-slate-700/50">
          <table className="w-full text-xs border-collapse">
            <thead>
              <tr className="text-left text-slate-500 bg-slate-800/50">
                <th className="px-4 py-2.5 font-medium border-b border-slate-700">Model</th>
                <th className="px-4 py-2.5 font-medium border-b border-slate-700">Provider</th>
                <th className="px-4 py-2.5 font-medium border-b border-slate-700">Arena ELO</th>
                <th className="px-4 py-2.5 font-medium border-b border-slate-700">Input $/M</th>
                <th className="px-4 py-2.5 font-medium border-b border-slate-700">Output $/M</th>
                <th className="px-4 py-2.5 font-medium border-b border-slate-700">Effective $/M</th>
                <th className="px-4 py-2.5 font-medium border-b border-slate-700">Type</th>
              </tr>
            </thead>
            <tbody>
              {paretoModels.map((m, i) => (
                <tr
                  key={m.name}
                  className={`border-b border-slate-800 transition-colors cursor-pointer ${
                    tooltip?.model.name === m.name ? "bg-slate-700/40" : i % 2 === 0 ? "bg-slate-800/20" : ""
                  } hover:bg-slate-700/30`}
                  onMouseEnter={() => setTooltip({ model: m, x: 0, y: 0 })}
                  onMouseLeave={() => setTooltip(null)}
                >
                  <td className="px-4 py-2 font-medium text-white">{m.name}</td>
                  <td className="px-4 py-2">
                    <span
                      className="px-2 py-0.5 rounded text-white text-xs font-medium"
                      style={{
                        background: providerColor(m.provider) + "33",
                        border: `1px solid ${providerColor(m.provider)}55`,
                      }}
                    >
                      {m.provider}
                    </span>
                  </td>
                  <td className="px-4 py-2 font-mono text-green-400 font-bold">{m.eloScore}</td>
                  <td className="px-4 py-2 font-mono text-slate-300">${m.inputPrice}</td>
                  <td className="px-4 py-2 font-mono text-slate-300">${m.outputPrice}</td>
                  <td className="px-4 py-2 font-mono text-yellow-400 font-bold">${m.effectivePrice.toFixed(3)}</td>
                  <td className="px-4 py-2 text-slate-400">
                    {m.isThinking ? (
                      <span className="text-purple-400">🧠 Thinking</span>
                    ) : (
                      <span className="text-slate-500">Standard</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// ─── Slider control ───────────────────────────────────────────────────────
function SliderControl({
  label,
  display,
  value,
  min,
  max,
  step,
  onChange,
}: {
  label: string;
  display: string;
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (v: number) => void;
}) {
  return (
    <div>
      <div className="flex justify-between mb-2">
        <span className="text-xs text-slate-400">{label}</span>
        <span className="text-sm font-mono font-bold text-blue-400">{display}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full accent-blue-500 cursor-pointer"
        style={{ height: "4px" }}
      />
    </div>
  );
}

// ─── Tooltip box ──────────────────────────────────────────────────────────
function TooltipBox({
  tooltip,
  svgW,
  svgH,
}: {
  tooltip: { model: EnrichedModel; x: number; y: number };
  svgW: number;
  svgH: number;
}) {
  const { model, x, y } = tooltip;
  const tw = 220;
  const th = 120;
  const tx = x + 14 > svgW - tw ? x - tw - 10 : x + 14;
  const ty = y + 14 > svgH - th ? y - th - 10 : y + 14;

  return (
    <foreignObject x={tx} y={ty} width={tw} height={th + 20} style={{ overflow: "visible" }}>
      <div
        style={{ background: "rgba(15,18,30,0.97)", border: "1px solid #334155", borderRadius: 8, padding: "10px 14px", minWidth: tw, boxShadow: "0 8px 32px rgba(0,0,0,0.6)" }}
      >
        <p style={{ color: "#fff", fontWeight: 600, fontSize: 12, marginBottom: 4 }}>{model.name}</p>
        <p style={{ color: "#94A3B8", fontSize: 11, marginBottom: 2 }}>
          Provider: <span style={{ color: "#e2e8f0" }}>{model.provider}</span>
        </p>
        <p style={{ color: "#94A3B8", fontSize: 11, marginBottom: 2 }}>
          Arena ELO: <span style={{ color: "#4ade80", fontFamily: "monospace", fontWeight: "bold" }}>{model.eloScore}</span>
        </p>
        <p style={{ color: "#94A3B8", fontSize: 11, marginBottom: 2 }}>
          Effective: <span style={{ color: "#fbbf24", fontFamily: "monospace", fontWeight: "bold" }}>${model.effectivePrice.toFixed(3)}/M</span>
        </p>
        <p style={{ color: "#94A3B8", fontSize: 11, marginBottom: 2 }}>
          API: <span style={{ color: "#e2e8f0", fontFamily: "monospace" }}>${model.inputPrice}/${model.outputPrice}</span>
        </p>
        {model.isPareto && (
          <p style={{ color: "#fde047", fontSize: 11, fontWeight: 600, marginTop: 4 }}>★ Pareto Efficient</p>
        )}
      </div>
    </foreignObject>
  );
}
