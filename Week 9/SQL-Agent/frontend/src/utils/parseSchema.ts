import type { ParsedTable, ParsedColumn } from "../types";

export function parseSchema(raw: string): ParsedTable[] {
  const tables: ParsedTable[] = [];
  const lines = raw.split("\n");
  let currentTable: ParsedTable | null = null;

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) {
      if (currentTable && currentTable.columns.length > 0) {
        tables.push(currentTable);
        currentTable = null;
      }
      continue;
    }

    const tableMatch = trimmed.match(/^Table:\s*"(.+)"$/);
    if (tableMatch) {
      if (currentTable && currentTable.columns.length > 0) {
        tables.push(currentTable);
      }
      currentTable = { name: tableMatch[1], columns: [] };
      continue;
    }

    const colMatch = trimmed.match(
      /^-\s*"(.+?)"\s*\((.+?)\)(?:\s*\[(PK|FK)\])?$/
    );
    if (colMatch && currentTable) {
      const col: ParsedColumn = {
        name: colMatch[1],
        type: colMatch[2],
        key: colMatch[3] as "PK" | "FK" | undefined,
      };
      currentTable.columns.push(col);
    }
  }

  if (currentTable && currentTable.columns.length > 0) {
    tables.push(currentTable);
  }

  return tables;
}
