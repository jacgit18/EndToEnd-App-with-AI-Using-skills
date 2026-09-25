import { useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import {
  api,
  DATE_FORMATS,
  type DateFormat,
  type ImportMapping,
  type ImportPreview,
  type ImportResult,
} from "./api/client";

const DATE_FORMAT_LABELS: Record<DateFormat, string> = {
  iso: "YYYY-MM-DD",
  mdy: "MM/DD/YYYY",
  dmy: "DD/MM/YYYY",
};

// Per account-value choice: "" = not decided yet, EXCLUDE = leave those rows out,
// otherwise an account id. Import stays disabled until every value is decided, so
// a value is never silently skipped or dumped into a default account.
const EXCLUDE = "exclude";

type Mode = "single" | "multi";

export default function ImportPage() {
  const queryClient = useQueryClient();
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [result, setResult] = useState<ImportResult | null>(null);

  const [dateColumn, setDateColumn] = useState("");
  const [amountColumn, setAmountColumn] = useState("");
  const [descriptionColumn, setDescriptionColumn] = useState("");
  const [dateFormat, setDateFormat] = useState<DateFormat | "">("");
  const [invertSign, setInvertSign] = useState(false);
  const [mode, setMode] = useState<Mode>("single");
  const [accountId, setAccountId] = useState("");
  const [accountColumn, setAccountColumn] = useState("");
  const [choices, setChoices] = useState<Record<string, string>>({});

  const accounts = useQuery({
    queryKey: ["accounts", { includeArchived: false }],
    queryFn: () => api.listAccounts(),
  });
  const history = useQuery({ queryKey: ["imports"], queryFn: () => api.listImports() });

  const previewFile = useMutation({
    mutationFn: (f: File) => api.previewImport(f),
    onSuccess: (p) => {
      setPreview(p);
      setResult(null);
      // A new file has new headers and new values: nothing carries over.
      setDateColumn("");
      setAmountColumn("");
      setDescriptionColumn("");
      setDateFormat("");
      setAccountColumn("");
      setChoices({});
    },
  });

  const runImport = useMutation({
    mutationFn: (args: { file: File; mapping: ImportMapping; accountId?: number }) =>
      api.createImport(args.file, args.mapping, args.accountId),
    onSuccess: (r) => {
      setResult(r);
      queryClient.invalidateQueries({ queryKey: ["imports"] });
      queryClient.invalidateQueries({ queryKey: ["accounts"] });
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
    },
  });

  const activeAccounts = accounts.data ?? [];
  const accountNames = new Map(activeAccounts.map((a) => [a.id, a.name]));
  const values = preview && accountColumn ? (preview.distinct_values[accountColumn] ?? []) : [];
  const columnsPicked =
    dateColumn && amountColumn && descriptionColumn && new Set([dateColumn, amountColumn, descriptionColumn]).size === 3;
  const accountsReady =
    mode === "single"
      ? accountId !== ""
      : accountColumn !== "" &&
        ![dateColumn, amountColumn, descriptionColumn].includes(accountColumn) &&
        values.length > 0 &&
        values.every((v) => (choices[v] ?? "") !== "");
  const ready = !!file && !!preview && !!columnsPicked && dateFormat !== "" && accountsReady;

  function handleFile(f: File | null) {
    setFile(f);
    setPreview(null);
    setResult(null);
    if (f) previewFile.mutate(f);
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!ready || !file || !dateFormat) return;
    const mapping: ImportMapping = {
      date_column: dateColumn,
      amount_column: amountColumn,
      description_column: descriptionColumn,
      date_format: dateFormat,
      invert_sign: invertSign,
    };
    if (mode === "multi") {
      mapping.account_column = accountColumn;
      mapping.account_map = Object.fromEntries(
        values.map((v) => [v, choices[v] === EXCLUDE ? null : Number(choices[v])]),
      );
      runImport.mutate({ file, mapping });
    } else {
      runImport.mutate({ file, mapping, accountId: Number(accountId) });
    }
  }

  const headerOptions = (headers: string[]) =>
    headers.map((h) => (
      <option key={h} value={h}>
        {h}
      </option>
    ));

  return (
    <section style={{ fontFamily: "system-ui, sans-serif", padding: "2rem" }}>
      <p>
        <Link to="/">← Transactions</Link>
      </p>
      <h2>Import CSV</h2>

      <label>
        CSV file{" "}
        <input
          type="file"
          accept=".csv,text/csv"
          onChange={(e) => handleFile(e.target.files?.[0] ?? null)}
        />
      </label>
      {previewFile.isError && (
        <p role="alert" style={{ color: "crimson" }}>{(previewFile.error as Error).message}</p>
      )}

      {preview && (
        <form onSubmit={handleSubmit} style={{ marginTop: "1rem" }}>
          <p>
            {preview.row_count} rows. First {preview.rows.length}:
          </p>
          <table>
            <thead>
              <tr>
                {preview.headers.map((h) => (
                  <th key={h} style={{ textAlign: "left" }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {preview.rows.map((r, i) => (
                <tr key={i}>
                  {r.map((c, j) => (
                    <td key={j}>{c}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>

          <div style={{ display: "grid", gap: "0.5rem", margin: "1rem 0", maxWidth: "32rem" }}>
            <label>
              Date column{" "}
              <select value={dateColumn} onChange={(e) => setDateColumn(e.target.value)}>
                <option value="">Choose…</option>
                {headerOptions(preview.headers)}
              </select>
            </label>
            <label>
              Amount column{" "}
              <select value={amountColumn} onChange={(e) => setAmountColumn(e.target.value)}>
                <option value="">Choose…</option>
                {headerOptions(preview.headers)}
              </select>
            </label>
            <label>
              Description column{" "}
              <select value={descriptionColumn} onChange={(e) => setDescriptionColumn(e.target.value)}>
                <option value="">Choose…</option>
                {headerOptions(preview.headers)}
              </select>
            </label>
            <label>
              Date format{" "}
              <select value={dateFormat} onChange={(e) => setDateFormat(e.target.value as DateFormat | "")}>
                <option value="">Choose…</option>
                {DATE_FORMATS.map((f) => (
                  <option key={f} value={f}>
                    {DATE_FORMAT_LABELS[f]}
                  </option>
                ))}
              </select>
            </label>
            <label>
              <input type="checkbox" checked={invertSign} onChange={(e) => setInvertSign(e.target.checked)} />{" "}
              Invert sign (file shows spending as positive)
            </label>
          </div>

          <fieldset style={{ maxWidth: "32rem" }}>
            <legend>Which account?</legend>
            <label>
              <input type="radio" name="mode" checked={mode === "single"} onChange={() => setMode("single")} /> One
              account for the whole file
            </label>{" "}
            <label>
              <input type="radio" name="mode" checked={mode === "multi"} onChange={() => setMode("multi")} /> The file
              has an account column
            </label>

            {mode === "single" ? (
              <p>
                <label>
                  Account{" "}
                  <select value={accountId} onChange={(e) => setAccountId(e.target.value)}>
                    <option value="">Choose…</option>
                    {activeAccounts.map((a) => (
                      <option key={a.id} value={a.id}>
                        {a.name}
                      </option>
                    ))}
                  </select>
                </label>
              </p>
            ) : (
              <div>
                <p>
                  <label>
                    Account column{" "}
                    <select
                      value={accountColumn}
                      onChange={(e) => {
                        setAccountColumn(e.target.value);
                        setChoices({});
                      }}
                    >
                      <option value="">Choose…</option>
                      {headerOptions(Object.keys(preview.distinct_values))}
                    </select>
                  </label>
                </p>
                {values.map((v) => (
                  <p key={v} style={{ margin: "0.25rem 0" }}>
                    <label>
                      {v}{" "}
                      <select
                        aria-label={`Account for ${v}`}
                        value={choices[v] ?? ""}
                        onChange={(e) => setChoices({ ...choices, [v]: e.target.value })}
                      >
                        <option value="">Choose…</option>
                        <option value={EXCLUDE}>Don't import these rows</option>
                        {activeAccounts.map((a) => (
                          <option key={a.id} value={a.id}>
                            {a.name}
                          </option>
                        ))}
                      </select>
                    </label>
                  </p>
                ))}
              </div>
            )}
          </fieldset>

          <p>
            <button type="submit" disabled={!ready || runImport.isPending}>
              Import
            </button>
          </p>
        </form>
      )}

      {runImport.isError && (
        <p role="alert" style={{ color: "crimson" }}>{(runImport.error as Error).message}</p>
      )}

      {result && (
        <div role="status">
          <h3>Import finished</h3>
          <p>
            Imported {result.imported_count}, skipped {result.skipped_count} duplicates, rejected{" "}
            {result.rejected_count}
            {result.excluded_count > 0 && `, left out ${result.excluded_count}`}.
          </p>
          {result.batches.length > 1 && (
            <ul>
              {result.batches.map((b) => (
                <li key={b.batch_id}>
                  {accountNames.get(b.account_id) ?? `Account ${b.account_id}`}: imported {b.imported_count}, skipped{" "}
                  {b.skipped_count}
                </li>
              ))}
            </ul>
          )}
          {result.rejected.length > 0 && (
            <>
              <p>Rejected rows{result.rejected_count > result.rejected.length && " (first 100)"}:</p>
              <ul>
                {result.rejected.map((r) => (
                  <li key={r.line}>
                    Line {r.line}: {r.reason}
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      )}

      <h3>History</h3>
      <table>
        <thead>
          <tr>
            <th style={{ textAlign: "left" }}>When</th>
            <th style={{ textAlign: "left" }}>File</th>
            <th style={{ textAlign: "left" }}>Account</th>
            <th>Imported</th>
            <th>Skipped</th>
            <th>Rejected</th>
          </tr>
        </thead>
        <tbody>
          {history.data?.map((b) => (
            <tr key={b.id}>
              <td>{new Date(b.created_at).toLocaleString()}</td>
              <td>{b.filename}</td>
              <td>{accountNames.get(b.account_id) ?? `Account ${b.account_id}`}</td>
              <td>{b.imported_count}</td>
              <td>{b.skipped_count}</td>
              <td>{b.rejected_count}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
