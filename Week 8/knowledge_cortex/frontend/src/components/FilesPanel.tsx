import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { FileText, FolderOpen, Database, X } from "lucide-react";

interface FilesPanelProps {
  files: string[];
  totalFiles: number;
  isOpen: boolean;
  isLoading: boolean;
  onClose: () => void;
}

function getFileName(path: string): string {
  const parts = path.split("/");
  return parts[parts.length - 1] || path;
}

export function FilesPanel({
  files,
  totalFiles,
  isOpen,
  isLoading,
  onClose,
}: FilesPanelProps) {
  return (
    <div
      className={`fixed top-0 right-0 h-full bg-card/95 backdrop-blur-xl border-l border-border z-50
        transition-all duration-300 ease-in-out shadow-[-8px_0_30px_rgba(0,0,0,0.3)]
        ${isOpen ? "w-[380px] translate-x-0" : "w-0 translate-x-full"}`}
    >
      {isOpen && (
        <div className="flex flex-col h-full animate-fade-in">
          {/* Header */}
          <div className="flex items-center justify-between p-5 border-b border-border">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-primary/15 flex items-center justify-center">
                <Database className="w-4 h-4 text-primary" />
              </div>
              <div>
                <h2 className="text-sm font-semibold">Indexed Documents</h2>
                <p className="text-xs text-muted-foreground">
                  {totalFiles} file{totalFiles !== 1 ? "s" : ""} in knowledge base
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

          {/* File List */}
          <ScrollArea className="flex-1 px-4 py-3">
            {isLoading ? (
              <div className="space-y-2">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-14 rounded-lg shimmer" />
                ))}
              </div>
            ) : files.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <FolderOpen className="w-12 h-12 text-muted-foreground/30 mb-3" />
                <p className="text-sm text-muted-foreground">
                  No documents indexed yet
                </p>
                <p className="text-xs text-muted-foreground/60 mt-1">
                  Drop PDFs into backend/docs to get started
                </p>
              </div>
            ) : (
              <div className="space-y-2 pb-6">
                {files.map((file, index) => (
                  <Card
                    key={index}
                    className="border-border/50 bg-secondary/30 hover:bg-secondary/50 transition-all duration-200"
                  >
                    <CardContent className="p-3 flex items-center gap-3">
                      <div className="w-9 h-9 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                        <FileText className="w-4 h-4 text-primary" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium truncate">
                          {getFileName(file)}
                        </p>
                        <p className="text-[11px] text-muted-foreground truncate">
                          {file}
                        </p>
                      </div>
                      <Badge
                        variant="secondary"
                        className="text-[10px] px-1.5 py-0 h-5 bg-emerald-500/15 text-emerald-400 flex-shrink-0"
                      >
                        indexed
                      </Badge>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </ScrollArea>
        </div>
      )}
    </div>
  );
}
