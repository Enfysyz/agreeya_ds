import { Globe, Search, FileText, Brain, ExternalLink, CheckCircle2, Loader2 } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
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

interface ActivityLogProps {
  logs: LogEntry[]
  isActive: boolean
}

export function ActivityLog({ logs, isActive }: ActivityLogProps) {
  if (logs.length === 0) return null

  return (
    <div className="mt-3 space-y-1.5">
      {/* Activity Header */}
      <div className="flex items-center gap-2 mb-2">
        {isActive && (
          <Loader2 className="h-3 w-3 text-muted-foreground animate-spin" />
        )}
        <span className="text-xs font-medium text-muted-foreground tracking-wide uppercase">
          Research Activity
        </span>
        <Badge variant="secondary" className="text-[10px] px-1.5 py-0 h-4 font-mono">
          {logs.length}
        </Badge>
      </div>

      {/* Log Entries */}
      <div className="space-y-1">
        {logs.map((log, index) => {
          const colorClasses = getLogColor(log.message)
          const isLatest = index === logs.length - 1 && isActive

          return (
            <div
              key={index}
              className={`
                flex items-start gap-2 py-1.5 px-2.5 rounded-lg border transition-all duration-300
                ${colorClasses}
                ${isLatest ? 'shadow-sm scale-[1.01]' : 'opacity-80'}
              `}
              style={{
                animationName: 'slideIn',
                animationDuration: '0.3s',
                animationTimingFunction: 'ease-out',
                animationFillMode: 'backwards',
                animationDelay: `${index * 50}ms`,
              }}
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
        })}
      </div>
    </div>
  )
}
