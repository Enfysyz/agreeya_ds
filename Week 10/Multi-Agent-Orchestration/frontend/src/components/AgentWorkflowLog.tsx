import { useState } from "react";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { ChevronDown, ChevronRight, Loader2 } from "lucide-react";
import { AgentStep } from "@/components/AgentStep";
import type { AgentEvent } from "@/types";

interface AgentWorkflowLogProps {
  events: AgentEvent[];
  isStreaming: boolean;
  selectedAgent: string | null;
  onSelectAgent: (agent: string) => void;
}

export function AgentWorkflowLog({
  events,
  isStreaming,
  selectedAgent,
  onSelectAgent,
}: AgentWorkflowLogProps) {
  const [isOpen, setIsOpen] = useState(true);

  if (events.length === 0 && !isStreaming) return null;

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen} className="workflow-log">
      <CollapsibleTrigger className="workflow-trigger" id="workflow-toggle">
        <div className="workflow-trigger-content">
          {isOpen ? (
            <ChevronDown className="h-4 w-4" />
          ) : (
            <ChevronRight className="h-4 w-4" />
          )}
          <span className="workflow-trigger-label">
            Agent Workflow
          </span>
          <span className="workflow-trigger-count">
            {events.length} step{events.length !== 1 ? "s" : ""}
          </span>
          {isStreaming && (
            <Loader2 className="h-3.5 w-3.5 animate-spin text-primary ml-2" />
          )}
        </div>
      </CollapsibleTrigger>
      <CollapsibleContent>
        <div className="workflow-steps">
          {events.map((event, index) => (
            <div key={`${event.agent}-${index}`} className="workflow-step-wrapper">
              {index > 0 && <div className="workflow-connector" />}
              <AgentStep
                event={event}
                isActive={selectedAgent === `${event.agent}-${index}`}
                onClick={() => onSelectAgent(`${event.agent}-${index}`)}
              />
            </div>
          ))}
          {isStreaming && (
            <div className="workflow-step-wrapper">
              <div className="workflow-connector" />
              <div className="agent-step agent-step--pending">
                <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                <span className="text-sm text-muted-foreground">
                  Processing next agent…
                </span>
              </div>
            </div>
          )}
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
}
