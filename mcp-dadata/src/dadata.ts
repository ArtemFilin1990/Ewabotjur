import { postJson } from "./http.js";

const BASE = "https://suggestions.dadata.ru/suggestions/api/4_1/rs";

export type DaDataSuggestion = {
  value: string;
  unrestricted_value: string;
  data: Record<string, unknown>;
};

export type DaDataResponse = {
  suggestions: DaDataSuggestion[];
};

export function makeDaDataClient(apiKey: string, timeoutMs: number) {
  const headers = { Authorization: `Token ${apiKey}` };

  return {
    async findPartyById(query: string, kpp?: string): Promise<DaDataResponse> {
      const body: Record<string, unknown> = { query };
      if (kpp) body.kpp = kpp;
      return postJson<DaDataResponse>(`${BASE}/findById/party`, body, headers, timeoutMs);
    },

    async suggestParty(query: string, count = 10): Promise<DaDataResponse> {
      return postJson<DaDataResponse>(`${BASE}/suggest/party`, { query, count }, headers, timeoutMs);
    },
  };
}
