import type { Provider } from "./types";

export interface AIFilterCondition {
  key: string;
  label: string;
  params: Record<string, unknown>;
}

export interface AIFilterParseRequest {
  prompt: string;
  provider: Provider;
}

export interface AIFilterParseResponse {
  conditions: AIFilterCondition[];
  summary: string;
  unsupported: string[];
}

export interface AIFilterApplyRequest {
  conditions: AIFilterCondition[];
}

export interface AIFilterParamSpec {
  name: string;
  type: string;
  default: unknown;
  description?: string | null;
}

export interface AIFilterCatalogEntry {
  key: string;
  label_template: string;
  description: string;
  params: AIFilterParamSpec[];
}

export interface AIFilterCatalogResponse {
  entries: AIFilterCatalogEntry[];
}
