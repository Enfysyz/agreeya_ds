import { ScrollArea } from "@/components/ui/scroll-area";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { X, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { AGENT_META } from "@/types";
import type { AgentEvent } from "@/types";
import type { JSX } from "react";
import Markdown from "react-markdown";

interface AgentDetailPanelProps {
  event: AgentEvent | null;
  onClose: () => void;
}

/**
 * Renders a JSON-like data display for agent output.
 */
function renderValue(value: unknown, depth = 0): JSX.Element {
  if (value === null || value === undefined) {
    return <span className="text-muted-foreground italic">null</span>;
  }

  if (typeof value === "string") {
    // Render long strings as paragraphs
    if (value.length > 80 || value.includes('\n') || value.includes('#') || value.includes('*')) {
      return (
        <div className="detail-text prose prose-sm dark:prose-invert">
          <Markdown>{value}</Markdown>
        </div>
      );
    }
    return <span className="detail-value-string">{value}</span>;
  }

  if (typeof value === "number" || typeof value === "boolean") {
    return <span className="detail-value-primitive">{String(value)}</span>;
  }

  if (Array.isArray(value)) {
    if (value.length === 0) {
      return <span className="text-muted-foreground italic">[]</span>;
    }
    return (
      <ul className="detail-list">
        {value.map((item, i) => (
          <li key={i} className="detail-list-item">
            {typeof item === "object" && item !== null ? (
              renderValue(item, depth + 1)
            ) : (
              <span>{String(item)}</span>
            )}
          </li>
        ))}
      </ul>
    );
  }

  if (typeof value === "object") {
    const entries = Object.entries(value as Record<string, unknown>);
    return (
      <div className={`detail-object ${depth > 0 ? "detail-object--nested" : ""}`}>
        {entries.map(([key, val]) => (
          <div key={key} className="detail-field">
            <span className="detail-field-key">
              {key.replace(/_/g, " ")}
            </span>
            <div className="detail-field-value">{renderValue(val, depth + 1)}</div>
          </div>
        ))}
      </div>
    );
  }

  return <span>{String(value)}</span>;
}

export function AgentDetailPanel({ event, onClose }: AgentDetailPanelProps) {
  if (!event) {
    return (
      <div className="detail-panel detail-panel--empty">
        <div className="detail-empty-state">
          <span className="detail-empty-icon">
            <Search className="h-8 w-8 text-muted-foreground" />
          </span>
          <p className="text-muted-foreground text-sm">
            Click on an agent step to view its output
          </p>
        </div>
      </div>
    );
  }

  const meta = AGENT_META[event.agent];

  return (
    <div className="detail-panel">
      <Card className="detail-card">
        <CardHeader className="detail-card-header">
          <div className="detail-header-row">
            <div className="detail-header-info">
              <span className="detail-agent-icon">
                {(() => {
                  const Icon = event.icon;
                  return <Icon className="h-6 w-6" />;
                })()}
              </span>
              <div>
                <CardTitle className="detail-agent-title">{event.label}</CardTitle>
                {meta && (
                  <p className="detail-agent-desc">{meta.description}</p>
                )}
              </div>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={onClose}
              className="detail-close-btn"
              id="close-detail-panel"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
          <Separator />
        </CardHeader>
        <CardContent className="detail-card-content">
          <ScrollArea className="detail-scroll">
            {event.data ? (
              renderValue(event.data)
            ) : (
              <p className="text-muted-foreground italic">No data available</p>
            )}
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}
