import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { AlertCircle, Clock, ServerCrash } from 'lucide-react'

export function DowntimeHistory() {
    const { data: history, isLoading, isError } = useQuery({
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

    return (
        <div className="space-y-4">
            <div className="flex justify-between items-end border-b pb-4">
                <div>
                    <h2 className="text-lg font-bold text-foreground tracking-tight flex items-center gap-2">
                        <ServerCrash className="h-5 w-5 text-destructive" />
                        Outage History
                    </h2>
                    <p className="text-xs text-muted-foreground font-mono mt-1">
                        Displaying history of website downtime
                    </p>
                </div>
                <div className="px-3 py-1 bg-destructive/10 text-destructive border border-destructive/20 rounded-md font-mono text-xs font-bold">
                    {history.length} INCIDENT{history.length > 1 ? 'S' : ''}
                </div>
            </div>

            <div className="space-y-3 overflow-y-auto max-h-[500px] pr-2 custom-scrollbar">
                {[...history].reverse().map((entry, index) => (
                    <div
                        key={index}
                        className="group relative border border-border/50 bg-card/40 hover:bg-card hover:border-border rounded-xl p-4 transition-all duration-300"
                    >
                        <div className="absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b from-destructive/60 to-amber-500/60 rounded-l-xl opacity-50 group-hover:opacity-100 transition-opacity" />

                        <div className="flex justify-between items-start mb-2 pl-2">
                            <div className="flex items-center gap-2 text-destructive font-bold text-sm">
                                <AlertCircle className="h-4 w-4" />
                                <span>Offline Model Transition</span>
                            </div>
                            <div className="flex items-center gap-1.5 text-[10px] uppercase font-mono bg-background border px-2 py-0.5 rounded text-muted-foreground group-hover:text-foreground transition-colors">
                                <Clock className="h-3 w-3" />
                                {new Date(entry.timestamp).toLocaleString()}
                            </div>
                        </div>

                        <div className="pl-2 space-y-3">
                            <p className="text-sm text-foreground/80 leading-relaxed">
                                {entry.message}
                            </p>

                            <div className="bg-background rounded-md border border-border/50 p-3 overflow-x-auto">
                                <code className="text-[10px] font-mono text-muted-foreground whitespace-pre-wrap break-all">
                                    <span className="text-destructive/80 font-semibold">TRACE:</span> {entry.error}
                                </code>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    )
}
