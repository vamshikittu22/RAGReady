import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { AlertCircle, ServerCrash, Clock } from 'lucide-react'

interface DowntimeEntry {
    timestamp: string
    error: string
    message: string
}

function extractReason(entry: DowntimeEntry): string {
    if (entry.error.includes('429') || entry.error.includes('RESOURCE_EXHAUSTED')) {
        return 'Gemini API quota exceeded → Fallback to OpenRouter'
    }
    if (entry.error.includes('timeout') || entry.error.includes('Timeout')) {
        return 'Request timed out'
    }
    if (entry.error.includes('500')) {
        return 'Internal server error'
    }
    return entry.message || 'LLM unavailable'
}

function formatTime(timestamp: string): string {
    const d = new Date(timestamp)
    return d.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: true,
    })
}

export function DowntimeHistory() {
    const { data: history, isLoading, isError } = useQuery<DowntimeEntry[]>({
        queryKey: ['downtime-history'],
        queryFn: api.getDowntimeHistory,
        refetchInterval: 10000,
    })

    if (isLoading) {
        return (
            <div className="flex h-[400px] items-center justify-center text-muted-foreground border border-dashed border-border rounded-lg bg-card/50">
                <ServerCrash className="h-6 w-6 animate-pulse mr-2" />
                <span className="font-mono text-sm uppercase tracking-wider">Analyzing logs...</span>
            </div>
        )
    }

    if (isError) {
        return (
            <div className="flex h-[400px] flex-col items-center justify-center text-red-500 gap-2 border border-dashed border-red-500/20 rounded-lg bg-red-500/5">
                <AlertCircle className="h-8 w-8" />
                <p className="font-mono text-xs uppercase">Error loading history</p>
            </div>
        )
    }

    if (!history?.length) {
        return (
            <div className="flex h-[400px] flex-col items-center justify-center text-emerald-500 gap-3 border border-dashed border-emerald-500/20 rounded-lg bg-emerald-500/5">
                <div className="relative">
                    <div className="absolute inset-0 rounded-full animate-ping bg-emerald-500/20" />
                    <ServerCrash className="relative h-10 w-10 z-10 p-2 bg-emerald-500/10 rounded-full" />
                </div>
                <div className="text-center">
                    <p className="font-mono text-sm uppercase font-bold tracking-widest text-emerald-600 dark:text-emerald-400">100% Uptime</p>
                    <p className="font-mono text-xs text-muted-foreground mt-1">No recorded generation downtime</p>
                </div>
            </div>
        )
    }

    const reversed = [...history].reverse()

    return (
        <div className="space-y-4">
            <div className="flex justify-between items-end border-b pb-4">
                <div>
                    <h2 className="text-lg font-bold text-foreground tracking-tight flex items-center gap-2">
                        <ServerCrash className="h-5 w-5 text-destructive" />
                        Outage History
                    </h2>
                    <p className="text-xs text-muted-foreground font-mono mt-1">
                        LLM generation failures and fallback events
                    </p>
                </div>
                <div className="px-3 py-1 bg-destructive/10 text-destructive border border-destructive/20 rounded-md font-mono text-xs font-bold">
                    {history.length} INCIDENT{history.length > 1 ? 'S' : ''}
                </div>
            </div>

            <div className="overflow-y-auto max-h-[500px] pr-1 custom-scrollbar">
                <div className="border border-border/50 rounded-xl overflow-hidden divide-y divide-border/30">
                    {reversed.map((entry, index) => (
                        <div
                            key={index}
                            className="flex items-center gap-3 px-4 py-2.5 hover:bg-muted/30 transition-colors text-sm"
                        >
                            <AlertCircle className="h-3.5 w-3.5 shrink-0 text-destructive/70" />
                            <span className="shrink-0 font-mono text-xs text-muted-foreground flex items-center gap-1.5">
                                <Clock className="h-3 w-3" />
                                {formatTime(entry.timestamp)}
                            </span>
                            <span className="text-foreground/70 text-xs">—</span>
                            <span className="text-sm text-foreground/80 truncate">
                                {extractReason(entry)}
                            </span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    )
}
