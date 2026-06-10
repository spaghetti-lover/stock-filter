import type { Provider } from "@/lib/types";

export const MODEL_OPTIONS: Record<Provider, { value: string; label: string }[]> = {
  claude: [
    { value: "claude-sonnet-4-6", label: "Sonnet 4.6" },
    { value: "claude-opus-4-7", label: "Opus 4.7" },
    { value: "claude-haiku-4-5-20251001", label: "Haiku 4.5" },
  ],
  gemini: [
    { value: "gemini-2.5-flash", label: "2.5 Flash" },
    { value: "gemini-2.5-pro", label: "2.5 Pro" },
  ],
  qwen: [
    { value: "qwen-plus", label: "Plus" },
    { value: "qwen-turbo", label: "Turbo" },
    { value: "qwen-max", label: "Max" },
    { value: "qwen3.5-flash", label: "3.5 Flash" },
  ],
};

export const DEFAULT_MODEL: Record<Provider, string> = {
  claude: "claude-sonnet-4-6",
  gemini: "gemini-2.5-flash",
  qwen: "qwen-plus",
};
