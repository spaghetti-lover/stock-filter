import type { Choice } from "./ChoiceStep";

export const ANALYSTS: Choice[] = [
  { code: "market", label: "Market Analyst", hint: "price action, indicators, momentum" },
  { code: "social", label: "Social Media Analyst", hint: "sentiment, virality, retail mood" },
  { code: "news", label: "News Analyst", hint: "macro headlines, filings, events" },
  { code: "fundamentals", label: "Fundamentals Analyst", hint: "ratios, earnings, balance sheet" },
];

export const RESEARCH_DEPTH: Choice[] = [
  {
    code: "shallow",
    label: "Shallow",
    hint: "quick research, few debate and strategy discussion rounds",
  },
  {
    code: "medium",
    label: "Medium",
    hint: "middle ground, moderate debate rounds and strategy discussion",
  },
  {
    code: "deep",
    label: "Deep",
    hint: "comprehensive research, in-depth debate and strategy discussion",
  },
];

export const LLM_PROVIDERS: Choice[] = [
  { code: "openai", label: "OpenAI" },
  { code: "google", label: "Google" },
  { code: "anthropic", label: "Anthropic" },
  { code: "xai", label: "xAI" },
  { code: "deepseek", label: "DeepSeek" },
  { code: "qwen", label: "Qwen" },
  { code: "glm", label: "GLM" },
  { code: "openrouter", label: "OpenRouter" },
  { code: "azure", label: "Azure OpenAI" },
  { code: "ollama", label: "Ollama" },
];

interface ProviderEngines {
  quick: Choice[];
  deep: Choice[];
}

export const PROVIDER_ENGINES: Record<string, ProviderEngines> = {
  anthropic: {
    quick: [
      { code: "claude-sonnet-4-6", label: "Claude Sonnet 4.6", hint: "Best speed and intelligence balance" },
      { code: "claude-haiku-4-5", label: "Claude Haiku 4.5", hint: "Fast, near-instant responses" },
      { code: "claude-sonnet-4-5", label: "Claude Sonnet 4.5", hint: "Agents and coding" },
    ],
    deep: [
      { code: "claude-opus-4-7", label: "Claude Opus 4.7", hint: "Most intelligent, agents and coding" },
      { code: "claude-opus-4-5", label: "Claude Opus 4.5", hint: "Premium, max intelligence" },
      { code: "claude-sonnet-4-6", label: "Claude Sonnet 4.6", hint: "Best speed and intelligence balance" },
      { code: "claude-sonnet-4-5", label: "Claude Sonnet 4.5", hint: "Agents and coding" },
    ],
  },
  openai: {
    quick: [
      { code: "gpt-4o-mini", label: "GPT-4o mini", hint: "Cheap, fast" },
      { code: "gpt-4o", label: "GPT-4o", hint: "Balanced default" },
      { code: "gpt-4.1-mini", label: "GPT-4.1 mini", hint: "Updated mini reasoning" },
    ],
    deep: [
      { code: "gpt-5", label: "GPT-5", hint: "Frontier reasoning" },
      { code: "gpt-4.1", label: "GPT-4.1", hint: "Strong coding and tools" },
      { code: "o4", label: "o4", hint: "Reasoning-tuned" },
    ],
  },
  google: {
    quick: [
      { code: "gemini-2.5-flash", label: "Gemini 2.5 Flash", hint: "Fast multimodal" },
      { code: "gemini-2.0-flash", label: "Gemini 2.0 Flash", hint: "Cheap default" },
    ],
    deep: [
      { code: "gemini-2.5-pro", label: "Gemini 2.5 Pro", hint: "Long-context reasoning" },
      { code: "gemini-2.0-pro", label: "Gemini 2.0 Pro", hint: "Solid baseline" },
    ],
  },
  xai: {
    quick: [
      { code: "grok-3-fast", label: "Grok 3 Fast", hint: "Quick responses" },
    ],
    deep: [
      { code: "grok-3", label: "Grok 3", hint: "Heavy reasoning" },
    ],
  },
  deepseek: {
    quick: [{ code: "deepseek-chat", label: "DeepSeek Chat", hint: "General purpose" }],
    deep: [{ code: "deepseek-reasoner", label: "DeepSeek Reasoner", hint: "Chain-of-thought" }],
  },
  qwen: {
    quick: [{ code: "qwen-2.5-7b", label: "Qwen 2.5 7B", hint: "Light and quick" }],
    deep: [{ code: "qwen-2.5-72b", label: "Qwen 2.5 72B", hint: "Large reasoning" }],
  },
  glm: {
    quick: [{ code: "glm-4-flash", label: "GLM-4 Flash", hint: "Fast Chinese-tuned" }],
    deep: [{ code: "glm-4-plus", label: "GLM-4 Plus", hint: "Premium reasoning" }],
  },
  openrouter: {
    quick: [
      { code: "or-claude-haiku", label: "openrouter / claude-haiku-4.5" },
      { code: "or-gpt-4o-mini", label: "openrouter / gpt-4o-mini" },
    ],
    deep: [
      { code: "or-claude-opus", label: "openrouter / claude-opus-4.7" },
      { code: "or-gpt-5", label: "openrouter / gpt-5" },
    ],
  },
  azure: {
    quick: [{ code: "az-gpt-4o-mini", label: "Azure GPT-4o mini" }],
    deep: [{ code: "az-gpt-4o", label: "Azure GPT-4o" }],
  },
  ollama: {
    quick: [{ code: "llama-3.1-8b", label: "Llama 3.1 8B (local)", hint: "Fast local" }],
    deep: [{ code: "llama-3.1-70b", label: "Llama 3.1 70B (local)", hint: "Heavy local" }],
  },
};

export const EFFORT_LEVELS: Choice[] = [
  { code: "high", label: "High", hint: "recommended", badge: "rec" },
  { code: "medium", label: "Medium", hint: "balanced" },
  { code: "low", label: "Low", hint: "faster, cheaper" },
];
