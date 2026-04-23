import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { ChevronDown, ChevronRight, Globe, Search, FileText, Brain, ExternalLink, CheckCircle2, Loader2 } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useState } from 'react'
import type { LogEntry } from '@/types'

function getLogIcon(message: string) {
  if (message.toLowerCase().includes('initializing')) return <Brain className="h-3.5 w-3.5" />
  if (message.toLowerCase().includes('found source')) return <Search className="h-3.5 w-3.5" />
  if (message.toLowerCase().includes('navigating')) return <Globe className="h-3.5 w-3.5" />
  if (message.toLowerCase().includes('analyzing')) return <FileText className="h-3.5 w-3.5" />
  if (message.toLowerCase().includes('synthesizing')) return <Brain className="h-3.5 w-3.5" />
  return <CheckCircle2 className="h-3.5 w-3.5" />
}

function getLogColor(message: string): string {
  if (message.toLowerCase().includes('initializing')) return 'text-indigo-600 bg-indigo-50 border-indigo-200'
  if (message.toLowerCase().includes('found source')) return 'text-emerald-600 bg-emerald-50 border-emerald-200'
  if (message.toLowerCase().includes('navigating')) return 'text-sky-600 bg-sky-50 border-sky-200'
  if (message.toLowerCase().includes('analyzing')) return 'text-amber-600 bg-amber-50 border-amber-200'
  if (message.toLowerCase().includes('synthesizing')) return 'text-violet-600 bg-violet-50 border-violet-200'
  return 'text-slate-600 bg-slate-50 border-slate-200'
}

function LogItem({ log, isLatest, isActive }: { log: LogEntry, isLatest?: boolean, isActive?: boolean }) {
  const colorClasses = getLogColor(log.message)
  return (
    <div
      className={`
        flex items-start gap-2 py-1.5 px-2.5 rounded-lg border transition-all duration-300
        ${colorClasses}
        ${isLatest ? 'shadow-sm scale-[1.01]' : 'opacity-80'}
      `}
    >
      <span className="mt-0.5 shrink-0">{getLogIcon(log.message)}</span>
      <div className="flex-1 min-w-0">
        <p className="text-xs font-medium leading-snug">{log.message}</p>
        {log.url && (
          <a
            href={log.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 mt-0.5 text-[11px] opacity-70 hover:opacity-100 transition-opacity truncate"
          >
            <ExternalLink className="h-2.5 w-2.5 shrink-0" />
            <span className="truncate">{log.url}</span>
          </a>
        )}
      </div>
      {isLatest && isActive && (
        <Loader2 className="h-3 w-3 animate-spin mt-0.5 shrink-0" />
      )}
    </div>
  )
}

interface ActivityLogProps {
  logs: LogEntry[]
  isActive: boolean
  onSourceSelect?: (url: string) => void
  selectedSourceUrl?: string | null
}

function SourceCollapsible({ url, logs, onSourceSelect, selectedSourceUrl, isActive }: { url: string, logs: LogEntry[], onSourceSelect?: (url: string) => void, selectedSourceUrl?: string | null, isActive: boolean }) {
  const [isOpen, setIsOpen] = useState(false)
  const isSelected = selectedSourceUrl === url

  const handleToggle = (open: boolean) => {
    setIsOpen(open)
    if (open && onSourceSelect) {
      onSourceSelect(url)
    }
  }

  if (!isActive) {
    return (
      <div className={`border rounded-md overflow-hidden transition-colors ${isSelected ? 'border-indigo-300 ring-1 ring-indigo-100' : 'bg-white'}`}>
        <Button variant="ghost" size="sm" onClick={() => onSourceSelect && onSourceSelect(url)} className={`w-full flex items-center justify-between p-2 h-auto rounded-none ${isSelected ? 'bg-indigo-50/50 hover:bg-indigo-50' : 'hover:bg-slate-50'}`}>
          <div className="flex items-center gap-2 overflow-hidden w-full mr-2">
            <Globe className={`h-3.5 w-3.5 shrink-0 ${isSelected ? 'text-indigo-600' : 'text-slate-400'}`} />
            <span className={`text-xs truncate ${isSelected ? 'font-semibold text-indigo-700' : 'text-slate-600'}`} title={url}>{url}</span>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <a href={url} target="_blank" rel="noopener noreferrer" onClick={(e) => e.stopPropagation()} className="hover:text-indigo-600 text-slate-400 transition-colors" title="Visit source website">
              <ExternalLink className="h-3.5 w-3.5" />
            </a>
            <ChevronRight className={`h-3.5 w-3.5 ${isSelected ? 'text-indigo-600' : 'text-slate-400 opacity-0 group-hover:opacity-100'}`} />
          </div>
        </Button>
      </div>
    )
  }

  return (
    <Collapsible open={isOpen} onOpenChange={handleToggle} className={`border rounded-md overflow-hidden transition-colors ${isSelected ? 'border-indigo-300 ring-1 ring-indigo-100' : 'bg-white'}`}>
      <CollapsibleTrigger asChild>
        <Button variant="ghost" size="sm" className={`w-full flex items-center justify-between p-2 h-auto rounded-none ${isSelected ? 'bg-indigo-50/50 hover:bg-indigo-50' : 'hover:bg-slate-50'}`}>
          <div className="flex items-center gap-2 overflow-hidden w-full mr-2">
            <Globe className={`h-3.5 w-3.5 shrink-0 ${isSelected ? 'text-indigo-600' : 'text-slate-400'}`} />
            <span className={`text-xs truncate ${isSelected ? 'font-semibold text-indigo-700' : 'text-slate-600'}`} title={url}>{url}</span>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <a href={url} target="_blank" rel="noopener noreferrer" onClick={(e) => e.stopPropagation()} className="hover:text-indigo-600 text-slate-400 transition-colors" title="Visit source website">
              <ExternalLink className="h-3.5 w-3.5" />
            </a>
            {isOpen ? <ChevronDown className="h-3.5 w-3.5 text-slate-400" /> : <ChevronRight className="h-3.5 w-3.5 text-slate-400" />}
          </div>
        </Button>
      </CollapsibleTrigger>
      <CollapsibleContent className="p-2 border-t bg-slate-50/50 space-y-1">
        {logs.map((log, idx) => (
          <LogItem key={`src-${idx}`} log={log} />
        ))}
      </CollapsibleContent>
    </Collapsible>
  )
}

export function ActivityLog({ logs, isActive, onSourceSelect, selectedSourceUrl }: ActivityLogProps) {
  if (logs.length === 0) return null

  if (isActive) {
    return (
      <div className="mt-3 space-y-1.5">
        <div className="flex items-center gap-2 mb-2">
          <Loader2 className="h-3 w-3 text-muted-foreground animate-spin" />
          <span className="text-xs font-medium text-muted-foreground tracking-wide uppercase">
            Research Activity
          </span>
          <Badge variant="secondary" className="text-[10px] px-1.5 py-0 h-4 font-mono">
            {logs.length}
          </Badge>
        </div>
        <div className="space-y-1">
          {logs.map((log, index) => (
            <LogItem key={index} log={log} isLatest={index === logs.length - 1} isActive={isActive} />
          ))}
        </div>
      </div>
    )
  }

  const generalLogs = logs.filter(l => !l.url)
  const sourceLogsMap = logs.reduce((acc, log) => {
    if (log.url) {
      if (!acc[log.url]) acc[log.url] = []
      acc[log.url].push(log)
    }
    return acc
  }, {} as Record<string, LogEntry[]>)

  return (
    <div className="space-y-3 pt-2">
      {generalLogs.length > 0 && (
        <div className="space-y-1">
          {generalLogs.map((log, index) => (
            <LogItem key={`gen-${index}`} log={log} />
          ))}
        </div>
      )}

      {Object.keys(sourceLogsMap).length > 0 && (
        <div className="space-y-2">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider px-1">Sources Explored</div>
          <div className="space-y-1.5">
            {Object.entries(sourceLogsMap).map(([url, sourceLogs]) => (
              <SourceCollapsible 
                key={url} 
                url={url} 
                logs={sourceLogs} 
                onSourceSelect={onSourceSelect}
                selectedSourceUrl={selectedSourceUrl}
                isActive={isActive}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
