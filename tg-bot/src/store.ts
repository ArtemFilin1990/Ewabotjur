import Database from "better-sqlite3";
import { CaseSchema, type Case } from "./caseSchema.js";

type Row = { user_id: number; case_id: string; json: string; updated_at: string; created_at: string };
type StateRow = { user_id: number; state_json: string; updated_at: string };

export type UserState = {
  mode?: "idle" | "upload_document" | "upload_attachment" | "wizard";
  wizard_step?: string | null;
};

export function initStore(sqlitePath: string) {
  const db = new Database(sqlitePath);
  db.pragma("journal_mode = WAL");

  db.exec(`
    CREATE TABLE IF NOT EXISTS cases (
      user_id INTEGER NOT NULL,
      case_id TEXT NOT NULL,
      json TEXT NOT NULL,
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL,
      PRIMARY KEY (user_id, case_id)
    );
    CREATE INDEX IF NOT EXISTS idx_cases_user_updated ON cases(user_id, updated_at);

    CREATE TABLE IF NOT EXISTS user_state (
      user_id INTEGER PRIMARY KEY,
      state_json TEXT NOT NULL,
      updated_at TEXT NOT NULL
    );
  `);

  const upsert = db.prepare(`
    INSERT INTO cases (user_id, case_id, json, created_at, updated_at)
    VALUES (@user_id, @case_id, @json, @created_at, @updated_at)
    ON CONFLICT(user_id, case_id) DO UPDATE SET
      json=excluded.json,
      updated_at=excluded.updated_at
  `);

  const getLatest = db.prepare(`
    SELECT user_id, case_id, json, created_at, updated_at
    FROM cases
    WHERE user_id = ?
    ORDER BY updated_at DESC
    LIMIT 1
  `);

  const getById = db.prepare(`
    SELECT user_id, case_id, json, created_at, updated_at
    FROM cases
    WHERE user_id = ? AND case_id = ?
    LIMIT 1
  `);

  const deleteOlderThan = db.prepare(`
    DELETE FROM cases
    WHERE updated_at < ?
  `);

  const getStateStmt = db.prepare(`SELECT user_id, state_json, updated_at FROM user_state WHERE user_id = ? LIMIT 1`);
  const upsertStateStmt = db.prepare(`
    INSERT INTO user_state (user_id, state_json, updated_at)
    VALUES (@user_id, @state_json, @updated_at)
    ON CONFLICT(user_id) DO UPDATE SET
      state_json=excluded.state_json,
      updated_at=excluded.updated_at
  `);

  function load(row: Row): Case {
    const parsed = JSON.parse(row.json);
    return CaseSchema.parse(parsed);
  }

  function loadState(row: StateRow): UserState {
    try {
      const parsed = JSON.parse(row.state_json);

      if (parsed === null || typeof parsed !== "object") {
        return { mode: "idle", wizard_step: null };
      }

      const obj = parsed as Record<string, unknown>;
      const result: UserState = { mode: "idle", wizard_step: null };

      if (
        obj.mode === "idle" ||
        obj.mode === "upload_document" ||
        obj.mode === "upload_attachment" ||
        obj.mode === "wizard"
      ) {
        result.mode = obj.mode;
      }

      if (typeof obj.wizard_step === "string" || obj.wizard_step === null || obj.wizard_step === undefined) {
        result.wizard_step = obj.wizard_step ?? null;
      }

      return result;
    } catch {
      return { mode: "idle", wizard_step: null };
    }
  }

  return {
    db,
    upsertCase(userId: number, c: Case) {
      upsert.run({
        user_id: userId,
        case_id: c.case_id,
        json: JSON.stringify(c),
        created_at: c.created_at,
        updated_at: c.updated_at,
      });
    },
    getLatestCase(userId: number): Case | null {
      const row = getLatest.get(userId) as Row | undefined;
      if (!row) return null;
      return load(row);
    },
    getCase(userId: number, caseId: string): Case | null {
      const row = getById.get(userId, caseId) as Row | undefined;
      if (!row) return null;
      return load(row);
    },
    cleanupTTL(ttlDays: number) {
      const cutoff = new Date(Date.now() - ttlDays * 24 * 60 * 60 * 1000).toISOString();
      const result = deleteOlderThan.run(cutoff);
      console.log(`[store] cleanupTTL: deleted ${result.changes} cases older than ${cutoff}`);
    },
    getState(userId: number): UserState {
      const row = getStateStmt.get(userId) as StateRow | undefined;
      if (!row) return { mode: "idle", wizard_step: null };
      return loadState(row);
    },
    setState(userId: number, s: UserState) {
      upsertStateStmt.run({
        user_id: userId,
        state_json: JSON.stringify(s),
        updated_at: new Date().toISOString(),
      });
    },
  };
}
