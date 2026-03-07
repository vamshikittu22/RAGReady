import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { CheckCircle2, XCircle, TrendingUp } from 'lucide-react'

interface EvalResults {
  context_recall: number
  context_precision: number
  faithfulness: number
  answer_relevancy: number
  refusal_accuracy: number
  citation_accuracy: number
  hallucination_rate: number
  benchmark: {
    naive_recall: number
    hybrid_recall: number
    improvement: string
  }
}

interface MetricConfig {
  key: keyof Omit<EvalResults, 'benchmark'>
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
            {isLowerBetter
              ? (value * 100).toFixed(1) + '%'
              : (value * 100).toFixed(1) + '%'}
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
  const [data, setData] = useState<EvalResults | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch('/eval-results.json')
      .then((res) => {
        if (!res.ok) throw new Error(`Failed to load: ${res.status}`)
        return res.json() as Promise<EvalResults>
      })
      .then(setData)
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'Failed to load evaluation results')
      })
  }, [])

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800 dark:border-red-800 dark:bg-red-950 dark:text-red-200">
        Failed to load evaluation results: {error}
      </div>
    )
  }

  if (!data) {
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

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">
          Evaluation Dashboard — Automated Quality Metrics
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">
          CI/CD quality gates evaluated against a golden dataset of 51 Q&A pairs.
          Metrics are computed automatically on every pull request.
        </p>
      </div>

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
