import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

type AnyObj = Record<string, unknown>;

export type DaDataSuggestion = {
  value: string;
  unrestricted_value: string;
  data: Record<string, unknown>;
};

export function pickTop(structured: AnyObj, limit = 5): DaDataSuggestion[] {
  const s = (structured?.suggestions as AnyObj[]) ?? [];
  return s.slice(0, limit).map((x) => ({
    value: String(x.value ?? ""),
    unrestricted_value: String(x.unrestricted_value ?? ""),
    data: (x.data as AnyObj) ?? {},
  }));
}

export async function connectDaDataMcp(command: string, args: string[]) {
  const client = new Client({ name: "ewabotjur-tg", version: "0.1.0" });
  const transport = new StdioClientTransport({ command, args });
  await client.connect(transport);
  return client;
}
