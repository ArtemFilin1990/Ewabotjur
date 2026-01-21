import "dotenv/config";
import fs from "node:fs";
import path from "node:path";

import { Telegraf, Markup } from "telegraf";
import { nanoid } from "nanoid";

import { CaseSchema, type Case, Scenario } from "./caseSchema.js";
import { initStore } from "./store.js";
import { setByPath, getByPath, parseScalar, nowIso } from "./utils.js";
import { connectDaDataMcp, pickTop } from "./mcpDadata.js";
import { generateBundle } from "./render.js";

function env(name: string, fallback?: string): string {
  const v = process.env[name] ?? fallback;
  if (!v) throw new Error(`Missing env var: ${name}`);
  return v;
}

const OUT_DIR = path.resolve("./out");
const DATA_DIR = path.resolve("./data");
fs.mkdirSync(OUT_DIR, { recursive: true });
fs.mkdirSync(DATA_DIR, { recursive: true });

const store = initStore(env("SQLITE_PATH", "./data/bot.sqlite"));
store.cleanupTTL(Number(env("CASE_TTL_DAYS", "30")));

const mcp = await connectDaDataMcp(
  env("MCP_DADATA_COMMAND", "node"),
  env("MCP_DADATA_ARGS").split(" ").filter(Boolean),
);

const bot = new Telegraf(env("TELEGRAM_BOT_TOKEN"));

function newCase(): Case {
  const now = nowIso();
  const base = {
    case_id: nanoid(10),
    created_at: now,
    updated_at: now,
  };
  return CaseSchema.parse(base);
}

function save(userId: number, c: Case) {
  c.updated_at = nowIso();
  const validated = CaseSchema.parse(c);
  store.upsertCase(userId, validated);
  return validated;
}

function current(userId: number): Case {
  const c = store.getLatestCase(userId);
  if (c) return c;
  const nc = newCase();
  save(userId, nc);
  return nc;
}

function fmtParty(p: any) {
  const name = p?.name || "[[TBD]]";
  const inn = p?.inn ? `, ИНН ${p.inn}` : "";
  const ogrn = p?.ogrn ? `, ОГРН ${p.ogrn}` : "";
  const kpp = p?.kpp ? `, КПП ${p.kpp}` : "";
  return `${name}${inn}${ogrn}${kpp}`;
}

async function showMenu(ctx: any) {
  const kb = Markup.inlineKeyboard([
    [Markup.button.callback("Новый кейс", "NEW_CASE")],
    [Markup.button.callback("Сценарий", "SCENARIO")],
    [Markup.button.callback("Upload: документ", "UPLOAD_DOC"), Markup.button.callback("Upload: вложение", "UPLOAD_ATT")],
    [Markup.button.callback("DaData по ИНН/ОГРН", "DADATA")],
    [Markup.button.callback("Wizard", "WIZARD"), Markup.button.callback("Поля", "FIELDS")],
    [Markup.button.callback("Генерация", "GENERATE")],
  ]);

  await ctx.reply(
    "Команды:\n" +
      "/new — новый кейс\n" +
      "/scenario <name> — сценарий\n" +
      "/set key=value — задать поле\n" +
      "/get key — показать поле\n" +
      "/fields — статус полей\n" +
      "/upload_doc — ждать документ (файл)\n" +
      "/upload_att — ждать вложение (файл)\n" +
      "/dadata <ИНН|ОГРН> [КПП] — заполнить контрагента\n" +
      "/wizard — анкета по сценарию\n" +
      "/generate — собрать файлы\n" +
      "/export_json — выгрузить JSON\n",
    kb,
  );
}

bot.start(async (ctx) => showMenu(ctx));

bot.command("new", async (ctx) => {
  const c = newCase();
  save(ctx.from.id, c);
  await ctx.reply(`Создан кейс: ${c.case_id}\nСценарий: ${c.scenario}`);
});

bot.action("NEW_CASE", async (ctx) => {
  const c = newCase();
  save(ctx.from!.id, c);
  await ctx.reply(`Создан кейс: ${c.case_id}\nСценарий: ${c.scenario}`);
  await ctx.answerCbQuery();
});

bot.command("scenario", async (ctx) => {
  const raw = ctx.message.text.split(" ").slice(1).join(" ").trim();
  if (!raw) {
    await ctx.reply(`Формат: /scenario ${Scenario.options.join(" | ")}`);
    return;
  }
  const parsed = Scenario.safeParse(raw);
  if (!parsed.success) {
    await ctx.reply(`Неизвестный сценарий. Доступно: ${Scenario.options.join(" | ")}`);
    return;
  }
  const c = current(ctx.from.id);
  c.scenario = parsed.data;
  save(ctx.from.id, c);
  await ctx.reply(`Ок. Сценарий: ${c.scenario}`);
});

bot.action("SCENARIO", async (ctx) => {
  const list = Scenario.options.map((s) => [Markup.button.callback(s, `SC_${s}`)]);
  await ctx.reply("Выберите сценарий:", Markup.inlineKeyboard(list));
  await ctx.answerCbQuery();
});

for (const s of Scenario.options) {
  bot.action(`SC_${s}`, async (ctx) => {
    const c = current(ctx.from!.id);
    c.scenario = s as any;
    save(ctx.from!.id, c);
    await ctx.reply(`Ок. Сценарий: ${c.scenario}`);
    await ctx.answerCbQuery();
  });
}

bot.command("set", async (ctx) => {
  const raw = ctx.message.text.replace(/^\/set\s*/i, "").trim();
  const idx = raw.indexOf("=");
  if (idx <= 0) {
    await ctx.reply("Формат: /set key=value\nПример: /set cp.inn=7707083893");
    return;
  }
  const key = raw.slice(0, idx).trim();
  const valRaw = raw.slice(idx + 1).trim();

  const c = current(ctx.from.id);
  const draft: any = structuredClone(c);
  setByPath(draft, key, parseScalar(valRaw));

  const parsed = CaseSchema.safeParse(draft);
  if (!parsed.success) {
    await ctx.reply("Ошибка валидации поля. Проверьте ключ/тип значения.");
    return;
  }

  save(ctx.from.id, parsed.data);
  await ctx.reply(`Ок. ${key} = ${valRaw}`);
});

bot.command("get", async (ctx) => {
  const key = ctx.message.text.replace(/^\/get\s*/i, "").trim();
  if (!key) {
    await ctx.reply("Формат: /get key\nПример: /get cp.inn");
    return;
  }
  const c = current(ctx.from.id);
  const v = getByPath(c as any, key);
  await ctx.reply(v === undefined ? "Пусто." : `Значение: ${JSON.stringify(v, null, 2)}`);
});

async function fieldsText(userId: number) {
  const c = current(userId);
  const lines = [
    `case_id: ${c.case_id}`,
    `scenario: ${c.scenario}`,
    `my: ${fmtParty(c.my)}`,
    `cp: ${fmtParty(c.cp)}`,
    `deal.subject: ${c.deal?.subject || "[[TBD]]"}`,
    `goals.primary: ${c.goals?.primary || "[[TBD]]"}`,
    `input.document_text: ${c.input?.document_text ? "есть" : "нет"}`,
    `document_files: ${(c.input.document_files?.length ?? 0)}`,
    `attachments: ${(c.input.attachments?.length ?? 0)}`,
    `deliverables: ${(c.deliverables ?? []).join(", ") || "—"}`,
  ];
  return lines.join("\n");
}

bot.command("fields", async (ctx) => {
  await ctx.reply(await fieldsText(ctx.from.id));
});

bot.action("FIELDS", async (ctx) => {
  await ctx.reply(await fieldsText(ctx.from!.id));
  await ctx.answerCbQuery();
});

// Upload handling: we do NOT download files; we store tg_file_id + name.
// User flow: /upload_doc then send a file; bot saves file_id into case.input.document_files[]
bot.command("upload_doc", async (ctx) => {
  store.setState(ctx.from.id, { mode: "upload_document", wizard_step: null });
  await ctx.reply("Ок. Пришлите файл-документ (PDF/DOCX/TXT). Я привяжу его к кейсу как document_files[].");
});
bot.command("upload_att", async (ctx) => {
  store.setState(ctx.from.id, { mode: "upload_attachment", wizard_step: null });
  await ctx.reply("Ок. Пришлите файл-вложение. Я привяжу его к кейсу как attachments[].");
});
bot.action("UPLOAD_DOC", async (ctx) => {
  store.setState(ctx.from!.id, { mode: "upload_document", wizard_step: null });
  await ctx.reply("Пришлите файл-документ (PDF/DOCX/TXT).");
  await ctx.answerCbQuery();
});
bot.action("UPLOAD_ATT", async (ctx) => {
  store.setState(ctx.from!.id, { mode: "upload_attachment", wizard_step: null });
  await ctx.reply("Пришлите файл-вложение.");
  await ctx.answerCbQuery();
});

bot.on("document", async (ctx) => {
  const st = store.getState(ctx.from.id);
  if (st.mode !== "upload_document" && st.mode !== "upload_attachment") {
    await ctx.reply("Файл получен, но я не жду загрузку. Используйте /upload_doc или /upload_att.");
    return;
  }

  const doc = ctx.message.document;
  const tg_file_id = doc.file_id;
  const name = doc.file_name ?? "document";

  const c = current(ctx.from.id);
  if (st.mode === "upload_document") {
    c.input.document_files = [...(c.input.document_files ?? []), { name, tg_file_id }];
    save(ctx.from.id, c);
    store.setState(ctx.from.id, { mode: "idle", wizard_step: null });
    await ctx.reply(`Ок. Документ привязан: ${name}`);
  } else {
    c.input.attachments = [...(c.input.attachments ?? []), { name, tg_file_id }];
    save(ctx.from.id, c);
    store.setState(ctx.from.id, { mode: "idle", wizard_step: null });
    await ctx.reply(`Ок. Вложение привязано: ${name}`);
  }
});

// DaData
bot.command("dadata", async (ctx) => {
  const parts = ctx.message.text.split(" ").filter(Boolean);
  if (parts.length < 2) {
    await ctx.reply("Формат: /dadata <ИНН|ОГРН> [КПП]");
    return;
  }
  const query = parts[1];
  const kpp = parts[2];

  const res = await mcp.callTool({
    name: "dadata_find_party_by_inn_or_ogrn",
    arguments: kpp ? { query, kpp } : { query },
  });

  const structured = (res as any).structuredContent ?? {};
  const top = pickTop(structured, 1);
  if (!top.length) {
    await ctx.reply("Ничего не найдено.");
    return;
  }

  const s0 = top[0];
  const data = s0.data as any;

  const c = current(ctx.from.id);
  c.dadata.enabled = true;
  c.dadata.query_inn_or_ogrn = query;
  if (kpp) c.dadata.kpp = kpp;
  c.dadata.snapshot = structured;

  const overwrite = c.dadata.use_as_source_of_truth === true;

  function put(path: string, value: string | undefined) {
    if (!value) return;
    const cur = getByPath(c as any, path);
    if (overwrite || cur == null || cur === "") setByPath(c as any, path, value);
  }

  put("cp.name", String(s0.value || ""));
  put("cp.inn", String(data.inn ?? ""));
  put("cp.ogrn", String(data.ogrn ?? ""));
  put("cp.kpp", String(data.kpp ?? ""));
  put("cp.legal_address", String(data.address?.value ?? ""));
  put("cp.signer.name", String(data.management?.name ?? ""));
  put("cp.signer.position", String(data.management?.post ?? ""));

  save(ctx.from.id, c);

  await ctx.reply(
    "Ок. Контрагент заполнен из DaData:\n" +
      `- ${fmtParty(c.cp)}\n` +
      (c.cp.legal_address ? `- адрес: ${c.cp.legal_address}\n` : "") +
      (c.cp.signer?.name ? `- руководитель: ${c.cp.signer.name} (${c.cp.signer.position || "—"})\n` : ""),
  );
});

bot.action("DADATA", async (ctx) => {
  await ctx.reply("Введите: /dadata 7707083893 или /dadata 7707083893 773601001");
  await ctx.answerCbQuery();
});

// Wizard (FSM-lite)
bot.command("wizard", async (ctx) => {
  store.setState(ctx.from.id, { mode: "wizard", wizard_step: "choose_scenario" });
  const list = Scenario.options.map((s) => [Markup.button.callback(s, `W_SC_${s}`)]);
  await ctx.reply("Wizard: выберите сценарий.", Markup.inlineKeyboard(list));
});

bot.action("WIZARD", async (ctx) => {
  store.setState(ctx.from!.id, { mode: "wizard", wizard_step: "choose_scenario" });
  const list = Scenario.options.map((s) => [Markup.button.callback(s, `W_SC_${s}`)]);
  await ctx.reply("Wizard: выберите сценарий.", Markup.inlineKeyboard(list));
  await ctx.answerCbQuery();
});

for (const s of Scenario.options) {
  bot.action(`W_SC_${s}`, async (ctx) => {
    const c = current(ctx.from!.id);
    c.scenario = s as any;
    save(ctx.from!.id, c);
    store.setState(ctx.from!.id, { mode: "wizard", wizard_step: "deal_subject" });
    await ctx.reply("Wizard: введите deal.subject (одной строкой).");
    await ctx.answerCbQuery();
  });
}

bot.on("text", async (ctx, next) => {
  const st = store.getState(ctx.from.id);
  if (st.mode !== "wizard") return next();

  const msg = ctx.message.text.trim();
  const c = current(ctx.from.id);

  if (st.wizard_step === "deal_subject") {
    c.deal.subject = msg;
    save(ctx.from.id, c);
    store.setState(ctx.from.id, { mode: "wizard", wizard_step: "goals_primary" });
    await ctx.reply("Wizard: введите goals.primary (цель/ожидаемый результат).");
    return;
  }

  if (st.wizard_step === "goals_primary") {
    c.goals.primary = msg;
    save(ctx.from.id, c);
    store.setState(ctx.from.id, { mode: "wizard", wizard_step: "cp_inn_or_name" });
    await ctx.reply("Wizard: введите ИНН/ОГРН контрагента (желательно) или название (если без DaData).");
    return;
  }

  if (st.wizard_step === "cp_inn_or_name") {
    // If looks like INN/OGRN => suggest using /dadata
    if (/^\d{10,15}$/.test(msg)) {
      await ctx.reply(`Принято. Для автозаполнения выполните: /dadata ${msg}`);
      c.cp.inn = msg;
    } else {
      c.cp.name = msg;
    }
    save(ctx.from.id, c);
    store.setState(ctx.from.id, { mode: "idle", wizard_step: null });
    await ctx.reply("Wizard завершён. Проверьте /fields и запускайте /generate.");
    return;
  }

  return next();
});

// Generate bundle
bot.command("generate", async (ctx) => {
  const c = current(ctx.from.id);
  const { bundleName, files } = generateBundle(c);

  const dir = path.join(OUT_DIR, bundleName);
  fs.mkdirSync(dir, { recursive: true });

  for (const f of files) {
    fs.writeFileSync(path.join(dir, f.name), f.content, "utf-8");
  }

  for (const f of files) {
    const full = path.join(dir, f.name);
    await ctx.replyWithDocument({ source: full, filename: f.name });
  }

  await ctx.reply(`Готово. Пакет: ${bundleName}`);
});

bot.action("GENERATE", async (ctx) => {
  const c = current(ctx.from!.id);
  const { bundleName, files } = generateBundle(c);

  const dir = path.join(OUT_DIR, bundleName);
  fs.mkdirSync(dir, { recursive: true });

  for (const f of files) {
    fs.writeFileSync(path.join(dir, f.name), f.content, "utf-8");
  }

  for (const f of files) {
    const full = path.join(dir, f.name);
    await ctx.replyWithDocument({ source: full, filename: f.name });
  }

  await ctx.reply(`Готово. Пакет: ${bundleName}`);
  await ctx.answerCbQuery();
});

bot.command("export_json", async (ctx) => {
  const c = current(ctx.from.id);
  const json = JSON.stringify(c, null, 2);
  const tmp = path.join(OUT_DIR, `case_${c.case_id}.json`);
  fs.writeFileSync(tmp, json, "utf-8");
  await ctx.replyWithDocument({ source: tmp, filename: `case_${c.case_id}.json` });
});

bot.launch();
process.once("SIGINT", () => bot.stop("SIGINT"));
process.once("SIGTERM", () => bot.stop("SIGTERM"));
