export type CsvValue = string | number | boolean | null | undefined;

export interface CsvColumn {
  id: string;
  name?: string;
}

const normalizeCsvValue = (value: unknown): string => {
  if (value === null || value === undefined) return "";
  if (Array.isArray(value)) {
    return value
      .map((item) => normalizeCsvValue(item))
      .filter((item) => item.length > 0)
      .join(", ");
  }
  if (typeof value === "object") {
    try {
      return JSON.stringify(value);
    } catch {
      return String(value);
    }
  }
  return String(value);
};

export const formatCsvPlainValue = (value: unknown): string => normalizeCsvValue(value);

export const formatCsvValue = (value: unknown): string => {
  const text = normalizeCsvValue(value);
  const escaped = text.replace(/"/g, '""');
  return `"${escaped}"`;
};

export const buildCsvFromRows = (headers: string[], rows: Array<Array<unknown>>): string => {
  if (!headers.length) return "";
  const lines = [headers.map(formatCsvValue).join(",")];
  rows.forEach((row) => {
    const line = headers.map((_, index) => formatCsvValue(row[index])).join(",");
    lines.push(line);
  });
  return lines.join("\n");
};

export const buildCsvFromRecords = (columns: CsvColumn[], rows: Array<Record<string, unknown>>): string => {
  if (!columns.length) return "";
  const headers = columns.map((col) => col.name || col.id);
  const lines = [headers.map(formatCsvValue).join(",")];
  rows.forEach((row) => {
    const line = columns.map((col) => formatCsvValue(row[col.id])).join(",");
    lines.push(line);
  });
  return lines.join("\n");
};

const downloadCsv = (filename: string, csv: string): void => {
  if (typeof document === "undefined" || !csv) return;
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
};

export const downloadCsvFromRows = (
  filename: string,
  headers: string[],
  rows: Array<Array<unknown>>,
): void => {
  const csv = buildCsvFromRows(headers, rows);
  downloadCsv(filename, csv);
};

export const downloadCsvFromRecords = (
  filename: string,
  rows: Array<Record<string, unknown>>,
  columns?: CsvColumn[],
): void => {
  if (!rows.length) return;
  const resolvedColumns =
    columns && columns.length > 0
      ? columns
      : Object.keys(rows[0]).map((id) => ({
          id,
          name: id,
        }));
  const csv = buildCsvFromRecords(resolvedColumns, rows);
  downloadCsv(filename, csv);
};
