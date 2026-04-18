import { useState } from "react";
import { Check, Copy, Code2 } from "lucide-react";
import { Button } from "@/components/ui/button";

interface SqlCodeBlockProps {
  sql: string;
}

// Simple SQL keyword highlighter
function highlightSQL(sql: string): React.ReactNode[] {
  const keywords = [
    "SELECT", "FROM", "WHERE", "JOIN", "LEFT", "RIGHT", "INNER", "OUTER",
    "ON", "AND", "OR", "NOT", "IN", "AS", "ORDER", "BY", "GROUP", "HAVING",
    "LIMIT", "OFFSET", "INSERT", "UPDATE", "DELETE", "CREATE", "ALTER",
    "DROP", "TABLE", "INTO", "VALUES", "SET", "DISTINCT", "COUNT", "SUM",
    "AVG", "MIN", "MAX", "BETWEEN", "LIKE", "ILIKE", "IS", "NULL", "ASC",
    "DESC", "UNION", "ALL", "EXISTS", "CASE", "WHEN", "THEN", "ELSE", "END",
    "CAST", "COALESCE", "WITH", "OVER", "PARTITION", "RANK", "ROW_NUMBER",
    "CROSS", "FULL", "NATURAL", "USING", "TOP",
  ];

  const tokens = sql.split(/(\s+|,|\(|\)|;|'[^']*'|"[^"]*")/g);
  return tokens.map((token, i) => {
    if (keywords.includes(token.toUpperCase())) {
      return (
        <span key={i} className="text-primary font-semibold">
          {token}
        </span>
      );
    }
    if (/^'[^']*'$/.test(token)) {
      return (
        <span key={i} className="text-emerald-600">
          {token}
        </span>
      );
    }
    if (/^"[^"]*"$/.test(token)) {
      return (
        <span key={i} className="text-amber-600">
          {token}
        </span>
      );
    }
    if (/^\d+(\.\d+)?$/.test(token)) {
      return (
        <span key={i} className="text-sky-600">
          {token}
        </span>
      );
    }
    return <span key={i}>{token}</span>;
  });
}

// Format SQL for readability
function formatSQL(sql: string): string {
  let formatted = sql.trim();
  const breakBefore = [
    "SELECT", "FROM", "WHERE", "JOIN", "LEFT JOIN", "RIGHT JOIN",
    "INNER JOIN", "OUTER JOIN", "ORDER BY", "GROUP BY", "HAVING",
    "LIMIT", "OFFSET", "UNION", "WITH",
  ];
  for (const kw of breakBefore) {
    const regex = new RegExp(`\\b(${kw})\\b`, "gi");
    formatted = formatted.replace(regex, `\n$1`);
  }
  formatted = formatted.replace(/^\n/, "");
  return formatted;
}

export default function SqlCodeBlock({ sql }: SqlCodeBlockProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(sql);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const formatted = formatSQL(sql);

  return (
    <div className="rounded-lg border border-border/60 bg-muted/30 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-1.5 bg-muted/50 border-b border-border/40">
        <div className="flex items-center gap-1.5">
          <Code2 className="h-3 w-3 text-primary/70" />
          <span className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">
            SQL Query
          </span>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleCopy}
          className="h-6 px-2 text-[11px] text-muted-foreground hover:text-foreground"
        >
          {copied ? (
            <>
              <Check className="h-3 w-3 mr-1 text-emerald-500" />
              Copied
            </>
          ) : (
            <>
              <Copy className="h-3 w-3 mr-1" />
              Copy
            </>
          )}
        </Button>
      </div>

      {/* Code */}
      <pre className="sql-code-block px-4 py-3 overflow-x-auto text-foreground/90">
        <code>{highlightSQL(formatted)}</code>
      </pre>
    </div>
  );
}
