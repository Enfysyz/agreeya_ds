import { Badge } from "@/components/ui/badge";
import { Loader2, CheckCircle2, AlertCircle } from "lucide-react";
import { formatDuration } from "@/lib/utils";
import type { AgentEvent } from "@/types";

interface AgentStepProps {
  event: AgentEvent;
  isActive: boolean;
  onClick: () => void;
}

export function AgentStep({ event, isActive, onClick }: AgentStepProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`agent-step ${isActive ? "agent-step--active" : ""}`}
      id={`agent-step-${event.agent}`}
    >
      <div className="agent-step-icon">
        {(() => {
          const Icon = event.icon;
          return <Icon className="h-4 w-4" />;
        })()}
      </div>
      <div className="agent-step-content">
        <span className="agent-step-label">{event.label}</span>
        <span className="agent-step-time">
          {event.timestamp.toLocaleTimeString()}
          {event.durationMs !== undefined && ` • ${formatDuration(event.durationMs)}`}
        </span>
      </div>
      <div className="agent-step-status">
        {event.status === "completed" && (
          <Badge variant="outline" className="badge-success">
            <CheckCircle2 className="h-3 w-3 mr-1" />
            Done
          </Badge>
        )}
        {event.status === "running" && (
          <Badge variant="outline" className="badge-running">
            <Loader2 className="h-3 w-3 mr-1 animate-spin" />
            Running
          </Badge>
        )}
        {event.status === "error" && (
          <Badge variant="destructive">
            <AlertCircle className="h-3 w-3 mr-1" />
            Error
          </Badge>
        )}
      </div>
    </button>
  );
}
