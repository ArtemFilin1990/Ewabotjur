import type { Case } from "./caseSchema.js";

export type GeneratedFile = { name: string; content: string };

function nowStamp() {
  const d = new Date();
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  const hh = String(d.getHours()).padStart(2, "0");
  const mi = String(d.getMinutes()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}_${hh}${mi}`;
}

export function generateBundle(c: Case): { bundleName: string; files: GeneratedFile[] } {
  const bundleName = c.files?.bundle_name ?? `${c.scenario}_${c.case_id}_${nowStamp()}`;

  const decision = `Decision: ${c.goals.primary || "Заполните goals.primary и/или приложите документ."}\n`;

  const attachmentsIndex = [
    "# Индекс входных материалов",
    "",
    "## Документ",
    c.input.document_text ? "- document_text: есть" : "- document_text: нет",
    ...(c.input.document_files?.map((f) => `- file: ${f.name} (tg_file_id=${f.tg_file_id})`) ?? ["- files: нет"]),
    "",
    "## Вложения",
    ...(c.input.attachments?.map((f) => `- attachment: ${f.name} (tg_file_id=${f.tg_file_id})`) ?? ["- нет"]),
    "",
  ].join("\n");

  const tbd = [
    "# TBD / Что нужно уточнить",
    "",
    "- [[TBD]] Сторона контрагента: cp.name / cp.signer.*",
    "- [[TBD]] Предмет сделки: deal.subject",
    "- [[TBD]] Документ: вставьте текст или загрузите файл",
    "",
  ].join("\n");

  const risks = [
    "# Таблица рисков",
    "",
    "| № | Риск | Последствия | Вероятность | Влияние | Меры реагирования |",
    "|---:|------|-------------|-------------|---------|-------------------|",
    "| 1 | [[TBD]] | [[TBD]] | Средняя | Высокое | [[TBD]] |",
    "",
  ].join("\n");

  const review = [
    "# Юридический разбор",
    "",
    `Сценарий: ${c.scenario}`,
    "",
    "## Стороны",
    `- Моя компания: ${c.my.name || "[[TBD]]"}; подписант: ${c.my.signer?.name || "[[TBD]]"} (${c.my.signer?.position || "[[TBD]]"})`,
    `- Контрагент: ${c.cp.name || "[[TBD]]"}`,
    "",
    "## Фактура",
    `- Предмет: ${c.deal.subject || "[[TBD]]"}`,
    "",
    "## Замечания",
    "- [[TBD]] Здесь будет разбор пунктов после подключения генерации/шаблонов.",
    "",
  ].join("\n");

  const files: GeneratedFile[] = [];
  const wants = new Set(c.deliverables ?? []);

  if (wants.has("decision")) files.push({ name: "DECISION.txt", content: decision });
  if (wants.has("attachments_index")) files.push({ name: "ATTACHMENTS_INDEX.md", content: attachmentsIndex });
  if (wants.has("tbd")) files.push({ name: "TBD_LIST.md", content: tbd });
  if (wants.has("risks")) files.push({ name: "RISKS.md", content: risks });
  if (wants.has("review")) files.push({ name: "LEGAL_REVIEW.md", content: review });
  if (wants.has("protocol")) files.push({ name: "DISAGREEMENT_PROTOCOL.md", content: "# Протокол разногласий\n\n[[TBD]]\n" });
  if (wants.has("letter")) files.push({ name: "LETTER.md", content: "# Письмо\n\n[[TBD]]\n" });
  if (wants.has("checklist")) files.push({ name: "CHECKLIST.md", content: "# Чеклист\n\n[[TBD]]\n" });

  return { bundleName, files };
}
