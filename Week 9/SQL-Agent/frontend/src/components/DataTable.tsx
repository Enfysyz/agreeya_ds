import { useState } from "react";
import { TableIcon, ChevronLeft, ChevronRight, Download } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface DataTableProps {
  data: Record<string, unknown>[];
}

const PAGE_SIZE = 10;

export default function DataTable({ data }: DataTableProps) {
  const [page, setPage] = useState(0);

  if (!data || data.length === 0) return null;

  const columns = Object.keys(data[0]);
  const totalPages = Math.ceil(data.length / PAGE_SIZE);
  const pageData = data.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  const handleExportCSV = () => {
    const header = columns.join(",");
    const rows = data.map((row) =>
      columns.map((col) => {
        const val = row[col];
        const str = val === null || val === undefined ? "" : String(val);
        return str.includes(",") ? `"${str}"` : str;
      }).join(",")
    );
    const csv = [header, ...rows].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "query_result.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="rounded-lg border border-border/60 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 bg-muted/30 border-b border-border/40">
        <div className="flex items-center gap-2">
          <TableIcon className="h-3.5 w-3.5 text-primary/70" />
          <span className="text-xs font-medium text-muted-foreground">
            Query Results
          </span>
          <Badge variant="secondary" className="text-[10px] px-1.5 py-0 h-4 font-normal">
            {data.length} row{data.length !== 1 ? "s" : ""}
          </Badge>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleExportCSV}
          className="h-6 px-2 text-[11px] text-muted-foreground hover:text-foreground"
        >
          <Download className="h-3 w-3 mr-1" />
          CSV
        </Button>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent border-border/40">
              {columns.map((col) => (
                <TableHead
                  key={col}
                  className="text-xs font-semibold text-foreground/70 bg-muted/20 whitespace-nowrap h-9 px-3"
                >
                  {col}
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {pageData.map((row, i) => (
              <TableRow
                key={i}
                className="border-border/30 hover:bg-accent/40 transition-colors"
              >
                {columns.map((col) => (
                  <TableCell
                    key={col}
                    className="text-xs py-2 px-3 whitespace-nowrap font-mono text-foreground/80"
                  >
                    {row[col] === null || row[col] === undefined
                      ? "—"
                      : String(row[col])}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between px-3 py-2 bg-muted/20 border-t border-border/30">
          <span className="text-[11px] text-muted-foreground">
            Page {page + 1} of {totalPages}
          </span>
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
              className="h-6 w-6 p-0"
            >
              <ChevronLeft className="h-3.5 w-3.5" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
              disabled={page === totalPages - 1}
              className="h-6 w-6 p-0"
            >
              <ChevronRight className="h-3.5 w-3.5" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
