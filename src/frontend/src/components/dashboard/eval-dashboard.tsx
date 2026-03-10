import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { EvalResults } from '@/types/api'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { CheckCircle2, XCircle, TrendingUp, Play, Loader2, Clock, FlaskConical } from 'lucide-react'
import { toast } from 'sonner'

interface MetricConfig {
  key: keyof Omit<EvalResults, 'benchmark' | 'meta' | 'error'>
  label: string
  target: number
  isLowerBetter?: boolean
}

const METRICS: MetricConfig[] = [
  { key: 'context_recall', label: 'Context Recall', target: 0.80 },
  { key: 'context_precision', label: 'Context Precision', target: 0.75 },
  { key: 'faithfulness', label: 'Faithfulness', target: 0.85 },
  { key: 'answer_relevancy', label: 'Answer Relevancy', target: 0.80 },
  { key: 'refusal_accuracy', label: 'Refusal Accuracy', target: 0.90 },
  { key: 'citation_accuracy', label: 'Citation Accuracy', target: 0.95 },
  { key: 'hallucination_rate', label: 'Hallucination Rate', target: 0.05, isLowerBetter: true },
]

function MetricCard({ label, value, target, isLowerBetter }: {
  label: string
  value: number
  target: number
  isLowerBetter?: boolean
}) {
  const passed = isLowerBetter ? value <= target : value >= target
  const percentage = isLowerBetter
    ? Math.max(0, Math.min(100, ((target - value) / target) * 100 + 100))
    : Math.min(100, (value / 1) * 100)

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            {label}
          </CardTitle>
          {passed ? (
            <CheckCircle2 className="h-5 w-5 text-emerald-500" />
          ) : (
            <XCircle className="h-5 w-5 text-red-500" />
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex items-baseline gap-2">
          <span className="text-3xl font-bold tabular-nums">
            {(value * 100).toFixed(1)}%
          </span>
          <Badge variant={passed ? 'default' : 'destructive'}>
            {passed ? 'PASS' : 'FAIL'}
          </Badge>
        </div>
        <p className="mt-1 text-xs text-muted-foreground">
          Target: {isLowerBetter ? '≤' : '≥'} {(target * 100).toFixed(0)}%
        </p>
        <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-muted">
          <div
            className={`h-full rounded-full transition-all ${passed ? 'bg-emerald-500' : 'bg-red-500'}`}
            style={{ width: `${Math.min(100, percentage)}%` }}
          />
        </div>
      </CardContent>
    </Card>
  )
}

export function EvalDashboard() {
  const queryClient = useQueryClient()

  const { data, isLoading, isError } = useQuery<EvalResults>({
    queryKey: ['eval-results'],
    queryFn: api.getEvalResults,
    refetchInterval: 5000, // Poll for results while evaluation is running
  })

  const evalMutation = useMutation({
    mutationFn: api.runEvaluation,
    onSuccess: (res) => {
      toast.success(res.message || 'Evaluation started!')
    },
    onError: (err: Error) => {
      toast.error(err.message || 'Failed to start evaluation')
    },
    onSettled: () => {
      // Start polling for results
      queryClient.invalidateQueries({ queryKey: ['eval-results'] })
    },
  })

  const hasResults = data && !data.error && data.context_recall !== undefined

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="space-y-2">
          <div className="h-8 w-96 animate-pulse rounded bg-muted" />
          <div className="h-4 w-64 animate-pulse rounded bg-muted" />
        </div>
        <div className="grid gap-4 sm:grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 7 }).map((_, i) => (
            <div key={i} className="h-40 animate-pulse rounded-xl bg-muted" />
          ))}
        </div>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800 dark:border-red-800 dark:bg-red-950 dark:text-red-200">
        Failed to load evaluation results. Make sure the backend is running.
      </div>
    )
  }

  // No results yet — show prompt to run evaluation
  if (!hasResults) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">
            Evaluation Dashboard — Pipeline Quality Metrics
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Run a live evaluation against your indexed documents to compute real quality metrics.
          </p>
        </div>

        <div className="flex flex-col items-center justify-center gap-4 rounded-xl border border-dashed border-border p-12">
          <div className="relative">
            <div className="absolute inset-0 rounded-full animate-pulse bg-primary/10" />
            <FlaskConical className="relative h-12 w-12 text-primary p-2" />
          </div>
          <div className="text-center">
            <p className="font-semibold text-foreground">No evaluation results yet</p>
            <p className="text-sm text-muted-foreground mt-1">
              Click below to run evaluation queries through the real RAG pipeline
            </p>
          </div>
          <button
            onClick={() => evalMutation.mutate()}
            disabled={evalMutation.isPending}
            className="mt-2 inline-flex items-center gap-2 rounded-lg bg-primary px-6 py-2.5 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
          >
            {evalMutation.isPending ? (
              <><Loader2 className="h-4 w-4 animate-spin" /> Running Evaluation...</>
            ) : (
              <><Play className="h-4 w-4" /> Run Evaluation</>
            )}
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">
            Evaluation Dashboard — Pipeline Quality Metrics
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Real metrics computed by running {data.meta?.total_questions ?? '?'} test queries through the live RAG pipeline.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {data.meta?.timestamp && (
            <span className="flex items-center gap-1.5 text-xs text-muted-foreground font-mono">
              <Clock className="h-3 w-3" />
              {new Date(data.meta.timestamp).toLocaleString()}
            </span>
          )}
          <button
            onClick={() => evalMutation.mutate()}
            disabled={evalMutation.isPending}
            className="inline-flex items-center gap-2 rounded-lg border border-border bg-card px-4 py-2 text-sm font-medium hover:bg-muted transition-colors disabled:opacity-50"
          >
            {evalMutation.isPending ? (
              <><Loader2 className="h-3.5 w-3.5 animate-spin" /> Running...</>
            ) : (
              <><Play className="h-3.5 w-3.5" /> Re-run</>
            )}
          </button>
        </div>
      </div>

      {/* Summary stats */}
      {data.meta && (
        <div className="flex flex-wrap gap-3">
          <Badge variant="outline" className="font-mono text-xs">
            {data.meta.total_questions} questions
          </Badge>
          <Badge variant="outline" className="font-mono text-xs text-emerald-600 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800">
            {data.meta.answered} answered
          </Badge>
          <Badge variant="outline" className="font-mono text-xs text-amber-600 dark:text-amber-400 border-amber-200 dark:border-amber-800">
            {data.meta.refused} refused
          </Badge>
          <Badge variant="outline" className="font-mono text-xs">
            {data.meta.duration_seconds}s runtime
          </Badge>
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
        {METRICS.map((metric) => (
          <MetricCard
            key={metric.key}
            label={metric.label}
            value={data[metric.key]}
            target={metric.target}
            isLowerBetter={metric.isLowerBetter}
          />
        ))}
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-primary" />
            <CardTitle>Retrieval Benchmark — Naive vs Hybrid</CardTitle>
          </div>
          <CardDescription>
            Hybrid retrieval (Dense + Sparse + RRF) compared to naive dense-only search
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <div className="mb-1 flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Naive Dense Retrieval</span>
                <span className="font-medium tabular-nums">
                  {(data.benchmark.naive_recall * 100).toFixed(0)}%
                </span>
              </div>
              <div className="h-3 w-full overflow-hidden rounded-full bg-muted">
                <div
                  className="h-full rounded-full bg-red-400"
                  style={{ width: `${data.benchmark.naive_recall * 100}%` }}
                />
              </div>
            </div>
            <div>
              <div className="mb-1 flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Hybrid Retrieval (Dense + BM25 + RRF)</span>
                <span className="font-medium tabular-nums">
                  {(data.benchmark.hybrid_recall * 100).toFixed(0)}%
                </span>
              </div>
              <div className="h-3 w-full overflow-hidden rounded-full bg-muted">
                <div
                  className="h-full rounded-full bg-emerald-500"
                  style={{ width: `${data.benchmark.hybrid_recall * 100}%` }}
                />
              </div>
            </div>
            <p className="text-sm font-medium text-emerald-600 dark:text-emerald-400">
              ↑ {data.benchmark.improvement} improvement with hybrid retrieval
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
