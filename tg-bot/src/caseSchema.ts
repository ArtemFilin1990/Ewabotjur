import { z } from "zod";

export const Scenario = z.enum([
  "contract_review",
  "risk_table",
  "disagreement_protocol",
  "claim_response",
  "pretrial_letter",
  "lawsuit_position",
  "negotiation_email",
  "client_explain",
  "compliance_check",
  "due_diligence_brief",
]);

export const Jurisdiction = z.enum(["RU", "CIS", "EU", "OTHER"]);
export const LawBranch = z.enum(["civil", "commercial", "procurement", "labor", "tax", "IP", "admin", "other"]);
export const Language = z.enum(["ru", "en"]);
export const Urgency = z.enum(["today", "24h", "3d", "week", "no_rush"]);
export const RiskAppetite = z.enum(["low", "medium", "high"]);

export const OutputFormat = z.enum(["md", "docx", "pdf"]);
export const OutputVerbosity = z.enum(["tight", "standard", "detailed"]);

export const Deliverable = z.enum([
  "decision",
  "review",
  "risks",
  "tbd",
  "protocol",
  "letter",
  "checklist",
  "attachments_index",
]);

export const DealType = z.enum([
  "supply",
  "services",
  "подряд",
  "аренда",
  "перевозка",
  "агентирование",
  "NDA",
  "SLA",
  "license",
  "other",
]);

export const VatMode = z.enum(["incl", "excl", "none", "unknown"]);
export const Currency = z.enum(["RUB", "USD", "EUR", "CNY", "OTHER"]);

export const RiskMatrixScale = z.enum(["3x3", "5x5"]);
export const RiskFocus = z.enum([
  "payment",
  "delivery",
  "quality",
  "liability",
  "IP",
  "termination",
  "disputes",
  "force_majeure",
  "confidentiality",
  "penalties",
  "guarantees",
]);

export const DisputeStage = z.enum(["pretense", "negotiation", "pretrial", "lawsuit", "enforcement"]);
export const SigningMethod = z.enum(["paper", "edo", "scan", "kval_signature"]);
export const YesNoConsent = z.enum(["yes", "no", "with_consent"]);

export const ContactRole = z.enum(["lawyer", "accountant", "procurement", "sales", "ceo", "other"]);

export const BankSchema = z.object({
  name: z.string().optional(),
  bik: z.string().optional(),
  rs: z.string().optional(),
  ks: z.string().optional(),
});

export const SignerSchema = z.object({
  name: z.string().default(""),
  position: z.string().default(""),
  basis: z.string().optional(),
  passport: z.string().optional(),
});

export const PartySchema = z.object({
  name: z.string().default(""),
  short_name: z.string().optional(),
  inn: z.string().optional(),
  kpp: z.string().optional(),
  ogrn: z.string().optional(),
  legal_address: z.string().optional(),
  actual_address: z.string().optional(),
  email: z.string().optional(),
  phone: z.string().optional(),
  bank: BankSchema.optional(),
  signer: SignerSchema.default({ name: "", position: "" }),
});

export const CaseSchema = z.object({
  case_id: z.string(),
  created_at: z.string(),
  updated_at: z.string(),

  scenario: Scenario.default("contract_review"),
  jurisdiction: Jurisdiction.default("RU"),
  law_branch: LawBranch.default("commercial"),
  language: Language.default("ru"),
  urgency: Urgency.default("no_rush"),
  risk_appetite: RiskAppetite.default("medium"),

  output_format: OutputFormat.default("md"),
  output_verbosity: OutputVerbosity.default("standard"),
  deliverables: z.array(Deliverable).default(["decision", "review", "risks", "tbd"]),

  my: PartySchema.default({ name: "", signer: { name: "", position: "" } }),
  cp: PartySchema.default({ name: "", signer: { name: "", position: "" } }),

  contacts: z
    .array(
      z.object({
        role: ContactRole,
        name: z.string(),
        email: z.string().optional(),
        phone: z.string().optional(),
      }),
    )
    .optional(),

  deal: z
    .object({
      subject: z.string().default(""),
      type: DealType.default("other"),
      scope: z.string().optional(),
      price: z
        .object({
          total: z.number().optional(),
          currency: Currency.optional(),
          vat: VatMode.optional(),
        })
        .optional(),
      payment: z.object({ terms: z.string().optional() }).optional(),
      delivery: z
        .object({
          incoterms: z.string().optional(),
          place: z.string().optional(),
          schedule: z.string().optional(),
        })
        .optional(),
      acceptance: z.object({ process: z.string().optional() }).optional(),
      warranty: z.string().optional(),
      penalties_expected: z.string().optional(),
      dependencies: z.string().optional(),
    })
    .default({ subject: "", type: "other" }),

  input: z
    .object({
      document_text: z.string().optional(),
      document_files: z.array(z.object({ name: z.string(), tg_file_id: z.string() })).optional(),
      attachments: z.array(z.object({ name: z.string(), tg_file_id: z.string() })).optional(),
      version_label: z.string().optional(),
      conflicts_note: z.string().optional(),
    })
    .default({}),

  goals: z
    .object({
      primary: z.string().default(""),
      secondary: z.string().optional(),
      must_keep: z.array(z.string()).optional(),
      must_change: z.array(z.string()).optional(),
      red_lines: z.array(z.string()).optional(),
      acceptable_tradeoffs: z.array(z.string()).optional(),
      negotiation_style: z.enum(["soft", "firm", "aggressive", "legalistic"]).optional(),
    })
    .default({ primary: "" }),

  compliance: z
    .object({
      sanctions_check_required: z.boolean().optional(),
      beneficial_owner_required: z.boolean().optional(),
      anti_corruption_clause_required: z.boolean().optional(),
      data_processing: z.enum(["none", "personal_data", "commercial_secret", "both"]).optional(),
      confidentiality_level: z.enum(["low", "medium", "high"]).optional(),
      export_control: z.boolean().optional(),
      ndas_present: z.boolean().optional(),
    })
    .optional(),

  risk_matrix: z
    .object({
      scale: RiskMatrixScale.optional(),
      focus: z.array(RiskFocus).optional(),
    })
    .optional(),

  dispute: z
    .object({
      stage: DisputeStage.optional(),
      claim_type: z.string().optional(),
      amount: z.number().optional(),
      dates: z
        .object({
          incident_date: z.string().optional(),
          claim_received_date: z.string().optional(),
          deadline_date: z.string().optional(),
        })
        .optional(),
      facts: z.string().optional(),
      evidence_files: z.array(z.object({ name: z.string(), tg_file_id: z.string() })).optional(),
      counterparty_position: z.string().optional(),
      our_position: z.string().optional(),
      desired_outcome: z.string().optional(),
      settlement_range: z.string().optional(),
    })
    .optional(),

  contract: z
    .object({
      governing_law: z.string().optional(),
      jurisdiction_court: z.string().optional(),
      arbitration: z.boolean().optional(),
      notice_channel: z.string().optional(),
      signing_method: SigningMethod.optional(),
      force_majeure_expected: z.string().optional(),
      assignment_allowed: YesNoConsent.optional(),
      subcontract_allowed: YesNoConsent.optional(),
      limitation_of_liability_expected: z.string().optional(),
      unilateral_termination_allowed: YesNoConsent.optional(),
      price_change_rules: z.string().optional(),
    })
    .optional(),

  files: z
    .object({
      bundle_name: z.string().optional(),
      include_toc: z.boolean().optional(),
      include_version_stamp: z.boolean().optional(),
      include_sources: z.boolean().optional(),
      naming_template: z.string().optional(),
    })
    .optional(),

  dadata: z
    .object({
      enabled: z.boolean().default(true),
      query_inn_or_ogrn: z.string().optional(),
      kpp: z.string().optional(),
      use_as_source_of_truth: z.boolean().default(false),
      snapshot: z.unknown().optional(),
    })
    .default({ enabled: true, use_as_source_of_truth: false }),
});

export type Case = z.infer<typeof CaseSchema>;
