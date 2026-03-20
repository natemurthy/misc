export interface ModelData {
  name: string;
  shortName: string;
  eloScore: number;
  inputPrice: number;  // $ per million tokens
  outputPrice: number; // $ per million tokens
  provider: string;
  color: string;
  isThinking?: boolean;
  contextWindow?: string;
}

// Arena Coding Leaderboard Data (ELO scores from arena.ai/leaderboard/code)
// Prices in $ per million tokens
export const MODELS_RAW: ModelData[] = [
  // Top tier models matching the screenshot
  {
    name: "Opus 4.6 (thinking)",
    shortName: "Opus 4.6 (thinking)",
    eloScore: 1547,
    inputPrice: 5,
    outputPrice: 25,
    provider: "Anthropic",
    color: "#D97706",
    isThinking: true,
  },
  {
    name: "Opus 4.6",
    shortName: "Opus 4.6",
    eloScore: 1549,
    inputPrice: 5,
    outputPrice: 25,
    provider: "Anthropic",
    color: "#D97706",
  },
  {
    name: "Gemini 3.1 Pro",
    shortName: "Gemini 3.1 Pro",
    eloScore: 1543,
    inputPrice: 2,
    outputPrice: 12,
    provider: "Google",
    color: "#3B82F6",
  },
  {
    name: "Sonnet 4.6",
    shortName: "Sonnet 4.6",
    eloScore: 1518,
    inputPrice: 3,
    outputPrice: 15,
    provider: "Anthropic",
    color: "#D97706",
  },
  {
    name: "Gemini 3 Pro",
    shortName: "Gemini 3 Pro",
    eloScore: 1509,
    inputPrice: 2,
    outputPrice: 12,
    provider: "Google",
    color: "#3B82F6",
  },
  {
    name: "Grok 4.1 (thinking)",
    shortName: "Grok 4.1 (thinking)",
    eloScore: 1507,
    inputPrice: 1.75,
    outputPrice: 14,
    provider: "xAI",
    color: "#8B5CF6",
    isThinking: true,
  },
  {
    name: "GPT-5.2",
    shortName: "GPT-5.2",
    eloScore: 1497,
    inputPrice: 1.75,
    outputPrice: 14,
    provider: "OpenAI",
    color: "#10B981",
  },
  {
    name: "Grok 4.1",
    shortName: "Grok 4.1",
    eloScore: 1495,
    inputPrice: 1.75,
    outputPrice: 14,
    provider: "xAI",
    color: "#8B5CF6",
  },
  {
    name: "GPT-5.1 (high)",
    shortName: "GPT-5.1 (high)",
    eloScore: 1493,
    inputPrice: 1.75,
    outputPrice: 14,
    provider: "OpenAI",
    color: "#10B981",
  },
  {
    name: "Gemini 3 Flash",
    shortName: "Gemini 3 Flash",
    eloScore: 1507,
    inputPrice: 0.5,
    outputPrice: 3,
    provider: "Google",
    color: "#3B82F6",
  },
  {
    name: "Gemini 3 Flash (thinking-min)",
    shortName: "Gemini 3 Flash (thinking-min)",
    eloScore: 1499,
    inputPrice: 0.5,
    outputPrice: 3,
    provider: "Google",
    color: "#3B82F6",
    isThinking: true,
  },
  {
    name: "Qwen3-235B",
    shortName: "Qwen3-235B",
    eloScore: 1481,
    inputPrice: 0.26,
    outputPrice: 2.08,
    provider: "Alibaba",
    color: "#F59E0B",
  },
  {
    name: "Owen3 Max",
    shortName: "Owen3 Max",
    eloScore: 1482,
    inputPrice: 4.5,
    outputPrice: 18,
    provider: "Alibaba",
    color: "#F59E0B",
  },
  {
    name: "Haiku 4.5",
    shortName: "Haiku 4.5",
    eloScore: 1480,
    inputPrice: 1,
    outputPrice: 5,
    provider: "Anthropic",
    color: "#D97706",
  },
  {
    name: "Gemini 2.5 Pro",
    shortName: "Gemini 2.5 Pro",
    eloScore: 1467,
    inputPrice: 1.25,
    outputPrice: 10,
    provider: "Google",
    color: "#3B82F6",
  },
  {
    name: "GPT-5",
    shortName: "GPT-5",
    eloScore: 1464,
    inputPrice: 3.5,
    outputPrice: 10.5,
    provider: "OpenAI",
    color: "#10B981",
  },
  {
    name: "o3",
    shortName: "o3",
    eloScore: 1461,
    inputPrice: 2,
    outputPrice: 8,
    provider: "OpenAI",
    color: "#10B981",
    isThinking: true,
  },
  {
    name: "DeepSeek R1",
    shortName: "DeepSeek R1",
    eloScore: 1464,
    inputPrice: 0.55,
    outputPrice: 2.19,
    provider: "DeepSeek",
    color: "#EF4444",
    isThinking: true,
  },
  {
    name: "GPT-4.1",
    shortName: "GPT-4.1",
    eloScore: 1462,
    inputPrice: 2,
    outputPrice: 8,
    provider: "OpenAI",
    color: "#10B981",
  },
  {
    name: "DeepSeek V3.2 (thinking)",
    shortName: "DeepSeek V3.2 (thinking)",
    eloScore: 1470,
    inputPrice: 0.28,
    outputPrice: 1.12,
    provider: "DeepSeek",
    color: "#EF4444",
    isThinking: true,
  },
  {
    name: "DeepSeek V3.2",
    shortName: "DeepSeek V3.2",
    eloScore: 1462,
    inputPrice: 0.28,
    outputPrice: 1.12,
    provider: "DeepSeek",
    color: "#EF4444",
  },
  {
    name: "Gemini 3.1 Flash-L",
    shortName: "Gemini 3.1 Flash-L",
    eloScore: 1459,
    inputPrice: 0.5,
    outputPrice: 1.5,
    provider: "Google",
    color: "#3B82F6",
  },
  {
    name: "Grok 4.1 Fast",
    shortName: "Grok 4.1 Fast",
    eloScore: 1456,
    inputPrice: 0.26,
    outputPrice: 0.40,
    provider: "xAI",
    color: "#8B5CF6",
  },
  {
    name: "GPT-4.1 Mini",
    shortName: "GPT-4.1 Mini",
    eloScore: 1440,
    inputPrice: 0.4,
    outputPrice: 1.6,
    provider: "OpenAI",
    color: "#10B981",
  },
  {
    name: "o4-mini",
    shortName: "o4-mini",
    eloScore: 1430,
    inputPrice: 1.1,
    outputPrice: 4.4,
    provider: "OpenAI",
    color: "#10B981",
    isThinking: true,
  },
  {
    name: "GPT-4.1 Nano",
    shortName: "GPT-4.1 Nano",
    eloScore: 1415,
    inputPrice: 0.1,
    outputPrice: 0.4,
    provider: "OpenAI",
    color: "#10B981",
  },
  {
    name: "Gemini 2.5 Flash",
    shortName: "Gemini 2.5 Flash",
    eloScore: 1420,
    inputPrice: 0.3,
    outputPrice: 2.5,
    provider: "Google",
    color: "#3B82F6",
  },
  {
    name: "DeepSeek V3.1",
    shortName: "DeepSeek V3.1",
    eloScore: 1435,
    inputPrice: 0.27,
    outputPrice: 1.10,
    provider: "DeepSeek",
    color: "#EF4444",
  },
  {
    name: "Claude 3.7 Sonnet",
    shortName: "Claude 3.7 Sonnet",
    eloScore: 1425,
    inputPrice: 3,
    outputPrice: 15,
    provider: "Anthropic",
    color: "#D97706",
  },
  {
    name: "Qwen3-235B (thinking)",
    shortName: "Qwen3-235B (thinking)",
    eloScore: 1470,
    inputPrice: 0.26,
    outputPrice: 2.08,
    provider: "Alibaba",
    color: "#F59E0B",
    isThinking: true,
  },
];

// Compute effective price per million tokens given ratio and cache settings
export function computeEffectivePrice(
  model: ModelData,
  inputOutputRatio: number,   // e.g. 50 means 1:50
  cacheHitRate: number,       // 0-100
  thinkingOverhead: number,   // 0-200 percentage
): number {
  // input:output ratio - inputOutputRatio means 1 input : inputOutputRatio output
  const totalParts = 1 + inputOutputRatio;
  const inputFraction = 1 / totalParts;
  const outputFraction = inputOutputRatio / totalParts;

  let effectiveInput = model.inputPrice;
  let effectiveOutput = model.outputPrice;

  // Apply cache hit rate discount on input
  const cacheRate = cacheHitRate / 100;
  effectiveInput = effectiveInput * (1 - cacheRate * 0.9); // cache gives ~90% discount on input

  // Apply thinking token overhead - adds % extra to output tokens for thinking models
  if (model.isThinking && thinkingOverhead > 0) {
    const overhead = thinkingOverhead / 100;
    effectiveOutput = effectiveOutput * (1 + overhead);
  }

  return effectiveInput * inputFraction + effectiveOutput * outputFraction;
}

export function computeParetoFrontier(models: (ModelData & { effectivePrice: number })[]): string[] {
  // Sort by price ascending
  const sorted = [...models].sort((a, b) => a.effectivePrice - b.effectivePrice);
  
  const pareto: string[] = [];
  let maxElo = -Infinity;
  
  for (const model of sorted) {
    if (model.eloScore > maxElo) {
      maxElo = model.eloScore;
      pareto.push(model.name);
    }
  }
  
  return pareto;
}
