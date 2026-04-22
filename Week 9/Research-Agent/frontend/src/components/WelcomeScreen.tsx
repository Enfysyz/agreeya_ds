import { Search, Sparkles, BookOpen, FlaskConical, Globe } from 'lucide-react'

interface WelcomeScreenProps {
  onSuggestionClick: (suggestion: string) => void
}

const suggestions = [
  {
    icon: <Sparkles className="h-4 w-4" />,
    label: 'AI & Machine Learning',
    prompt: 'Latest advancements in large language models and their real-world applications',
  },
  {
    icon: <FlaskConical className="h-4 w-4" />,
    label: 'Science & Technology',
    prompt: 'Recent breakthroughs in quantum computing and their implications',
  },
  {
    icon: <Globe className="h-4 w-4" />,
    label: 'Global Affairs',
    prompt: 'Current state of renewable energy adoption worldwide',
  },
  {
    icon: <BookOpen className="h-4 w-4" />,
    label: 'Research Deep Dive',
    prompt: 'The impact of microplastics on human health based on recent studies',
  },
]

export function WelcomeScreen({ onSuggestionClick }: WelcomeScreenProps) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center px-6 py-12">
      {/* Logo / Hero */}
      <div className="flex flex-col items-center gap-4 mb-10">
        <div className="relative">
          <div className="h-16 w-16 rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center shadow-lg shadow-indigo-200">
            <Search className="h-8 w-8 text-white" />
          </div>
          <div className="absolute -top-1 -right-1 h-5 w-5 rounded-full bg-emerald-400 border-2 border-white flex items-center justify-center">
            <Sparkles className="h-2.5 w-2.5 text-white" />
          </div>
        </div>
        <div className="text-center space-y-2">
          <h1 className="text-2xl font-bold text-foreground tracking-tight">
            Deep Research Agent
          </h1>
          <p className="text-sm text-muted-foreground max-w-md leading-relaxed">
            Ask any research question and watch as the AI agent searches the web, 
            scrapes relevant sources, and synthesizes a comprehensive report in real-time.
          </p>
        </div>
      </div>

      {/* Suggestion Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-xl">
        {suggestions.map((suggestion, index) => (
          <button
            key={index}
            id={`suggestion-${index}`}
            onClick={() => onSuggestionClick(suggestion.prompt)}
            className="group flex items-start gap-3 p-4 rounded-xl border border-border bg-background
              hover:border-indigo-200 hover:bg-indigo-50/50 hover:shadow-sm
              transition-all duration-200 text-left cursor-pointer"
          >
            <span className="mt-0.5 p-1.5 rounded-lg bg-muted group-hover:bg-indigo-100 group-hover:text-indigo-600 transition-colors text-muted-foreground">
              {suggestion.icon}
            </span>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold text-muted-foreground group-hover:text-indigo-600 transition-colors uppercase tracking-wide">
                {suggestion.label}
              </p>
              <p className="text-sm text-foreground/80 mt-0.5 leading-snug line-clamp-2">
                {suggestion.prompt}
              </p>
            </div>
          </button>
        ))}
      </div>

      {/* Footer hint */}
      <div className="mt-10 flex items-center gap-2 text-xs text-muted-foreground/50">
        <div className="h-px w-8 bg-border" />
        <span>Powered by Ollama + DuckDuckGo + Playwright</span>
        <div className="h-px w-8 bg-border" />
      </div>
    </div>
  )
}
