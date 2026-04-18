import { useEffect, useState } from "react";
import {
  Database,
  Table2,
  KeyRound,
  Link,
  ChevronRight,
  Loader2,
  Search,
} from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Input } from "@/components/ui/input";
import { fetchSchema } from "@/api";
import { parseSchema } from "@/utils/parseSchema";
import type { ParsedTable } from "@/types";

export default function SchemaPanel() {
  const [tables, setTables] = useState<ParsedTable[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [openTables, setOpenTables] = useState<Set<string>>(new Set());

  useEffect(() => {
    fetchSchema()
      .then((res) => {
        const parsed = parseSchema(res.schema);
        setTables(parsed);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const toggle = (name: string) => {
    setOpenTables((prev) => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name);
      else next.add(name);
      return next;
    });
  };

  const filteredTables = tables.filter(
    (t) =>
      t.name.toLowerCase().includes(search.toLowerCase()) ||
      t.columns.some((c) =>
        c.name.toLowerCase().includes(search.toLowerCase())
      )
  );

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-3 text-muted-foreground">
        <Loader2 className="h-5 w-5 animate-spin" />
        <span className="text-sm">Loading schema…</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-2 px-4 text-center">
        <Database className="h-8 w-8 text-destructive/60" />
        <p className="text-sm text-destructive font-medium">
          Failed to load schema
        </p>
        <p className="text-xs text-muted-foreground">{error}</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-4 pt-4 pb-3 border-b border-border/60">
        <div className="flex items-center gap-2 mb-3">
          <div className="flex items-center justify-center w-7 h-7 rounded-md bg-primary/10">
            <Database className="h-3.5 w-3.5 text-primary" />
          </div>
          <div>
            <h2 className="text-sm font-semibold tracking-tight">
              Database Schema
            </h2>
            <p className="text-[11px] text-muted-foreground">
              {tables.length} tables • Northwind DB
            </p>
          </div>
        </div>
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
          <Input
            id="schema-search"
            placeholder="Search tables or columns…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="h-8 pl-8 text-xs bg-muted/50 border-border/50 placeholder:text-muted-foreground/60"
          />
        </div>
      </div>

      {/* Tables */}
      <ScrollArea className="flex-1">
        <div className="p-2 space-y-0.5">
          {filteredTables.map((table) => (
            <Collapsible
              key={table.name}
              open={openTables.has(table.name)}
              onOpenChange={() => toggle(table.name)}
            >
              <CollapsibleTrigger className="flex items-center gap-2 w-full px-2.5 py-2 rounded-md text-sm hover:bg-accent/70 transition-colors group cursor-pointer">
                <ChevronRight
                  className={`h-3.5 w-3.5 text-muted-foreground transition-transform duration-200 ${
                    openTables.has(table.name) ? "rotate-90" : ""
                  }`}
                />
                <Table2 className="h-3.5 w-3.5 text-primary/70" />
                <span className="font-medium text-[13px] truncate">
                  {table.name}
                </span>
                <Badge
                  variant="secondary"
                  className="ml-auto text-[10px] px-1.5 py-0 h-4 font-normal"
                >
                  {table.columns.length}
                </Badge>
              </CollapsibleTrigger>
              <CollapsibleContent>
                <div className="ml-5 pl-3.5 border-l border-border/50 space-y-px py-1">
                  {table.columns.map((col) => (
                    <div
                      key={col.name}
                      className="flex items-center gap-2 px-2 py-1 rounded text-xs group hover:bg-muted/60 transition-colors"
                    >
                      {col.key === "PK" ? (
                        <KeyRound className="h-3 w-3 text-amber-500 shrink-0" />
                      ) : col.key === "FK" ? (
                        <Link className="h-3 w-3 text-blue-500 shrink-0" />
                      ) : (
                        <span className="w-3 h-3 shrink-0" />
                      )}
                      <span className="font-mono text-foreground/80 truncate">
                        {col.name}
                      </span>
                      <span className="ml-auto text-[10px] text-muted-foreground font-mono shrink-0">
                        {col.type}
                      </span>
                    </div>
                  ))}
                </div>
              </CollapsibleContent>
            </Collapsible>
          ))}

          {filteredTables.length === 0 && (
            <div className="text-center py-8 text-xs text-muted-foreground">
              No tables match "{search}"
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
