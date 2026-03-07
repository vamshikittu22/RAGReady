import { useHealth } from '@/hooks/use-health'
import { BrainCircuit } from 'lucide-react'
import { cn } from '@/lib/utils'

export function Header() {
  const { health, isHealthy, isLoading } = useHealth()

  return (
    <header className="sticky top-0 z-50 bg-[#020617]/80 backdrop-blur-md border-b border-border px-8 py-4 flex justify-between items-center shadow-sm">
      <div className="mx-auto flex w-full max-w-7xl items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-primary/10 border border-primary/30 flex items-center justify-center text-primary">
            <BrainCircuit className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-foreground tracking-tight">RAGReady</h1>
            <p className="text-xs text-muted-foreground font-mono mt-0.5">Pipeline Dashboard • OLED Edition</p>
          </div>
        </div>

        <div className="flex items-center gap-4 text-sm font-mono">
          {health?.document_count != null && (
            <span className="text-muted-foreground">
              <strong className="text-primary">{health.document_count}</strong> DOCS
            </span>
          )}
          <div className={cn(
            'px-3 py-1 rounded-full border flex items-center gap-2 text-[10px] tracking-widest uppercase font-bold',
            isLoading ? 'border-amber-500/30 bg-amber-500/10 text-amber-500' :
              isHealthy ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-500' :
                'border-red-500/30 bg-red-500/10 text-red-500'
          )}>
            <div className={cn(
              'w-2 h-2 rounded-full',
              isLoading ? 'bg-amber-500 animate-pulse' :
                isHealthy ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)]' :
                  'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.8)]'
            )} />
            {isLoading ? 'Checking' : isHealthy ? 'Live View' : 'Offline'}
          </div>
        </div>
      </div>
    </header>
  )
}
