import { useState } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { BookOpen, FileText, X, Star, ChevronRight, ChevronDown } from "lucide-react";
import type { Citation } from "@/lib/api";

interface CitationsPanelProps {
  allCitations: Citation[];
  usedCitations: Citation[];
  isOpen: boolean;
  onClose: () => void;
}

function getFileName(source: string): string {
  const parts = source.split("/");
  return parts[parts.length - 1] || source;
}

function scoreColor(score: number) {
  if (score >= 0.8) return "bg-emerald-500/15 text-emerald-600 border-emerald-200";
  if (score >= 0.5) return "bg-amber-500/15 text-amber-600 border-amber-200";
  return "bg-red-500/15 text-red-500 border-red-200";
}

export function CitationsPanel({
  allCitations,
  usedCitations,
  isOpen,
  onClose,
}: CitationsPanelProps) {
  const [expandedIndexes, setExpandedIndexes] = useState<Set<number>>(new Set());

  const toggleExpand = (index: number) => {
    setExpandedIndexes((prev) => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  };

  // Build a set of used citation identifiers (source + page + score) to mark highlights
  const usedSet = new Set(
    usedCitations.map((c) => `${c.source}::${c.page ?? ""}::${c.score}`)
  );

  const isUsed = (c: Citation) =>
    usedSet.has(`${c.source}::${c.page ?? ""}::${c.score}`);

  const usedCount = usedCitations.length;
  const totalCount = allCitations.length;

  return (
    <div
      className={`fixed top-0 right-0 h-full bg-card border-l border-border z-50
        transition-all duration-300 ease-in-out shadow-[-4px_0_20px_rgba(0,0,0,0.08)]
        ${isOpen ? "w-[440px] translate-x-0" : "w-0 translate-x-full"}`}
    >
      {isOpen && (
        <div className="flex flex-col h-full animate-fade-in w-[440px]">
          {/* Header */}
          <div className="flex items-center justify-between px-5 py-4 border-b border-border flex-shrink-0">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-primary/10 border border-primary/15 flex items-center justify-center">
                <BookOpen className="w-4 h-4 text-primary" />
              </div>
              <div>
                <h2 className="text-sm font-semibold text-foreground">Sources &amp; Citations</h2>
                <p className="text-xs text-muted-foreground">
                  {totalCount} retrieved · {usedCount} used in answer
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="w-8 h-8 rounded-lg hover:bg-secondary flex items-center justify-center transition-colors cursor-pointer flex-shrink-0"
            >
              <X className="w-4 h-4 text-muted-foreground" />
            </button>
          </div>

          {/* Legend */}
          {usedCount > 0 && (
            <div className="px-5 py-2.5 bg-primary/5 border-b border-border flex items-center gap-3 flex-shrink-0">
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <div className="w-3 h-3 rounded-sm bg-primary/15 border border-primary/30" />
                <span>Used in answer (top {usedCount})</span>
              </div>
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <div className="w-3 h-3 rounded-sm bg-secondary border border-border" />
                <span>Retrieved but not used</span>
              </div>
            </div>
          )}

          {/* Citations List */}
          <ScrollArea className="flex-1 min-h-0">
            <div className="p-4 space-y-3">
              {allCitations.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-16 text-center">
                  <BookOpen className="w-10 h-10 text-muted-foreground/30 mb-3" />
                  <p className="text-sm text-muted-foreground">No citations available</p>
                </div>
              ) : (
                allCitations.map((citation, index) => {
                  const used = isUsed(citation);
                  const expanded = expandedIndexes.has(index);
                  return (
                    <Card
                      key={index}
                      className={`transition-all duration-200 ${
                        used
                          ? "border-primary/30 bg-primary/5 shadow-sm"
                          : "border-border bg-card hover:bg-secondary/20"
                      }`}
                    >
                      <CardContent className="p-4">
                        {/* Card Header */}
                        <div className="flex items-start justify-between gap-2 mb-3">
                          <div className="flex items-center gap-2 min-w-0">
                            <div className={`w-6 h-6 rounded-md flex items-center justify-center flex-shrink-0 ${
                              used ? "bg-primary/15" : "bg-secondary"
                            }`}>
                              {used
                                ? <Star className="w-3 h-3 text-primary fill-primary" />
                                : <FileText className="w-3 h-3 text-muted-foreground" />
                              }
                            </div>
                            <span className={`text-xs font-medium truncate ${
                              used ? "text-foreground" : "text-muted-foreground"
                            }`}>
                              {getFileName(citation.source)}
                            </span>
                          </div>
                          <div className="flex items-center gap-1.5 flex-shrink-0">
                            {used && (
                              <Badge className="text-[10px] px-1.5 py-0 h-5 bg-primary/15 text-primary border border-primary/25 font-medium">
                                Used
                              </Badge>
                            )}
                            {citation.page != null && (
                              <Badge
                                variant="outline"
                                className="text-[10px] px-1.5 py-0 h-5 border-border text-muted-foreground"
                              >
                                p.{citation.page}
                              </Badge>
                            )}
                            {citation.score > 0 && (
                              <Badge
                                variant="secondary"
                                className={`text-[10px] px-1.5 py-0 h-5 border ${scoreColor(citation.score)}`}
                              >
                                {(citation.score * 100).toFixed(0)}%
                              </Badge>
                            )}
                          </div>
                        </div>

                        {/* Source path */}
                        <p className="text-[10px] text-muted-foreground/60 mb-2 truncate font-mono">
                          {citation.source}
                        </p>

                        <Separator className="mb-3 bg-border/50" />

                        {/* Content */}
                        <p className={`text-xs leading-relaxed text-muted-foreground transition-all duration-300 ${
                          expanded ? "" : "line-clamp-5"
                        }`}>
                          {citation.content}
                        </p>

                        {/* Expand / Collapse toggle */}
                        <button
                          onClick={() => toggleExpand(index)}
                          className="flex items-center gap-1 mt-2 text-[10px] text-primary/50 hover:text-primary transition-colors cursor-pointer"
                        >
                          {expanded
                            ? <ChevronDown className="w-3 h-3" />
                            : <ChevronRight className="w-3 h-3" />
                          }
                          <span>{expanded ? "Collapse" : "Expand"}</span>
                        </button>
                      </CardContent>
                    </Card>
                  );
                })
              )}
            </div>
          </ScrollArea>
        </div>
      )}
    </div>
  );
}
