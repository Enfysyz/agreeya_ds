import { ScrollArea } from "@/components/ui/scroll-area";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { BookOpen, FileText, X, ChevronRight } from "lucide-react";
import type { Citation } from "@/lib/api";

interface CitationsPanelProps {
  citations: Citation[];
  isOpen: boolean;
  onClose: () => void;
}

function getFileName(source: string): string {
  const parts = source.split("/");
  return parts[parts.length - 1] || source;
}

export function CitationsPanel({
  citations,
  isOpen,
  onClose,
}: CitationsPanelProps) {
  return (
    <div
      className={`fixed top-0 right-0 h-full bg-card/95 backdrop-blur-xl border-l border-border z-50 
        transition-all duration-300 ease-in-out shadow-[-8px_0_30px_rgba(0,0,0,0.3)]
        ${isOpen ? "w-[420px] translate-x-0" : "w-0 translate-x-full"}`}
    >
      {isOpen && (
        <div className="flex flex-col h-full animate-fade-in">
          {/* Header */}
          <div className="flex items-center justify-between p-5 border-b border-border">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-primary/15 flex items-center justify-center">
                <BookOpen className="w-4 h-4 text-primary" />
              </div>
              <div>
                <h2 className="text-sm font-semibold">Sources & Citations</h2>
                <p className="text-xs text-muted-foreground">
                  {citations.length} source{citations.length > 1 ? "s" : ""}{" "}
                  found
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="w-8 h-8 rounded-lg hover:bg-secondary flex items-center justify-center transition-colors cursor-pointer"
            >
              <X className="w-4 h-4 text-muted-foreground" />
            </button>
          </div>

          {/* Citations List */}
          <ScrollArea className="flex-1 px-4 py-3">
            <div className="space-y-3 pb-6">
              {citations.map((citation, index) => (
                <Card
                  key={index}
                  className="border-border/50 bg-secondary/30 hover:bg-secondary/60 transition-all duration-200 group"
                >
                  <CardContent className="p-4">
                    {/* Citation Header */}
                    <div className="flex items-start justify-between gap-2 mb-3">
                      <div className="flex items-center gap-2 min-w-0">
                        <div className="w-6 h-6 rounded-md bg-primary/10 flex items-center justify-center flex-shrink-0">
                          <FileText className="w-3 h-3 text-primary" />
                        </div>
                        <span className="text-xs font-medium truncate text-foreground">
                          {getFileName(citation.source)}
                        </span>
                      </div>
                      <div className="flex items-center gap-1.5 flex-shrink-0">
                        {citation.page != null && (
                          <Badge
                            variant="outline"
                            className="text-[10px] px-1.5 py-0 h-5 border-border/50"
                          >
                            p.{citation.page}
                          </Badge>
                        )}
                        {citation.score > 0 && (
                          <Badge
                            variant="secondary"
                            className={`text-[10px] px-1.5 py-0 h-5 ${
                              citation.score >= 0.8
                                ? "bg-emerald-500/15 text-emerald-400"
                                : citation.score >= 0.5
                                ? "bg-amber-500/15 text-amber-400"
                                : "bg-red-500/15 text-red-400"
                            }`}
                          >
                            {(citation.score * 100).toFixed(0)}%
                          </Badge>
                        )}
                      </div>
                    </div>

                    <Separator className="mb-3 bg-border/30" />

                    {/* Citation Content */}
                    <p className="text-xs leading-relaxed text-muted-foreground line-clamp-6 group-hover:line-clamp-none transition-all duration-300">
                      {citation.content}
                    </p>

                    {/* Expand hint */}
                    <div className="flex items-center gap-1 mt-2 text-[10px] text-primary/50 group-hover:text-primary/80 transition-colors">
                      <ChevronRight className="w-3 h-3" />
                      <span className="group-hover:hidden">
                        Hover to expand
                      </span>
                      <span className="hidden group-hover:inline">
                        Full text shown
                      </span>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </ScrollArea>
        </div>
      )}
    </div>
  );
}
