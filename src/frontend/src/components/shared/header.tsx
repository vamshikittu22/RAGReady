import { useHealth } from '@/hooks/use-health'
import { BrainCircuit } from 'lucide-react'
import { cn } from '@/lib/utils'

export function Header() {
  const { health, isHealthy, isLoading } = useHealth()

  return (
    <header className="border-b bg-background/95 backdrop-blur supports-backdrop-filter:bg-background/60">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4">
        <div className="flex items-center gap-2">
          <BrainCircuit className="h-6 w-6 text-primary" />
          <h1 className="text-lg font-bold tracking-tight">RAGReady</h1>
        </div>

        <div className="flex items-center gap-3 text-sm">
          {health?.document_count != null && (
            <span className="text-muted-foreground">
              {health.document_count} doc{health.document_count !== 1 ? 's' : ''}
            </span>
          )}
          <div className="flex items-center gap-1.5">
            <span
              className={cn(
                'inline-block h-2 w-2 rounded-full',
                isLoading
                  ? 'animate-pulse bg-amber-400'
                  : isHealthy
                    ? 'bg-emerald-500'
                    : 'bg-red-500'
              )}
            />
            <span className="text-xs text-muted-foreground">
              {isLoading ? 'Checking...' : isHealthy ? 'API Connected' : 'API Unavailable'}
            </span>
          </div>
        </div>
      </div>
    </header>
  )
}
