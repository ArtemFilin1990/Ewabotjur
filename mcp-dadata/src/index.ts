import "dotenv/config";
import { z } from "zod";

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

import { makeDaDataClient } from "./dadata.js";
import { HttpError } from "./http.js";

function requireEnv(name: string): string {
  const v = process.env[name];
  if (!v) throw new Error(`Missing env var: ${name}`);
  return v;
}

function timeoutMs(): number {
  const raw = process.env.DADATA_TIMEOUT_MS ?? "15000";
  const n = Number(raw);
  return Number.isFinite(n) && n > 0 ? n : 15000;
}

function normalizeError(e: unknown): { message: string; details?: unknown } {
  if (e instanceof HttpError) {
    return {
      message: `DaData HTTP error ${e.status}. Проверьте ключ/лимиты/доступ.`,
      details: e.bodyText,
    };
  }
  if (e instanceof Error) return { message: e.message };
  return { message: "Unknown error", details: e };
}

const server = new McpServer({ name: "dadata-mcp", version: "0.1.0" });

server.registerTool(
  "dadata_find_party_by_inn_or_ogrn",
  {
    title: "DaData: find party by INN/OGRN",
    description:
      "Точный поиск организации/ИП по ИНН или ОГРН через DaData findById/party. Возвращает suggestions[] (value, unrestricted_value, data).",
    inputSchema: z.object({
      query: z.string().min(10).max(15).describe("ИНН (10/12) или ОГРН/ОГРНИП"),
      kpp: z.string().min(9).max(9).optional().describe("КПП (опционально)"),
    }),
    annotations: { readOnlyHint: true, idempotentHint: true, openWorldHint: true },
  },
  async ({ query, kpp }) => {
    try {
      const client = makeDaDataClient(requireEnv("DADATA_API_KEY"), timeoutMs());
      const res = await client.findPartyById(query, kpp);

      return {
        content: [
          { type: "text", text: `OK. Найдено вариантов: ${res.suggestions?.length ?? 0}` },
        ],
        structuredContent: res,
      };
    } catch (e) {
      const err = normalizeError(e);
      return {
        isError: true,
        content: [{ type: "text", text: err.message }],
        structuredContent: err,
      };
    }
  },
);

server.registerTool(
  "dadata_suggest_party",
  {
    title: "DaData: suggest party",
    description:
      "Подсказки по организациям/ИП по названию/ИНН/ОГРН/КПП через DaData suggest/party.",
    inputSchema: z.object({
      query: z.string().min(1).describe("Строка поиска"),
      count: z.number().int().min(1).max(20).default(10),
    }),
    annotations: { readOnlyHint: true, idempotentHint: true, openWorldHint: true },
  },
  async ({ query, count }) => {
    try {
      const client = makeDaDataClient(requireEnv("DADATA_API_KEY"), timeoutMs());
      const res = await client.suggestParty(query, count);

      return {
        content: [{ type: "text", text: `OK. Подсказок: ${res.suggestions?.length ?? 0}` }],
        structuredContent: res,
      };
    } catch (e) {
      const err = normalizeError(e);
      return {
        isError: true,
        content: [{ type: "text", text: err.message }],
        structuredContent: err,
      };
    }
  },
);

server.registerTool(
  "health_ping",
  {
    title: "Health: ping",
    description: "Проверка живости MCP-сервера.",
    inputSchema: z.object({}),
    annotations: { readOnlyHint: true, idempotentHint: true },
  },
  async () => ({
    content: [{ type: "text", text: "ok" }],
    structuredContent: { ok: true },
  }),
);

// Validate API key at startup
// DaData API keys are typically 40 characters long
const MIN_API_KEY_LENGTH = 20;
const apiKey = requireEnv("DADATA_API_KEY");
if (apiKey.length < MIN_API_KEY_LENGTH) {
  console.warn("[mcp-dadata] Warning: DADATA_API_KEY seems too short. Please verify it is correct.");
}

await server.connect(new StdioServerTransport());
