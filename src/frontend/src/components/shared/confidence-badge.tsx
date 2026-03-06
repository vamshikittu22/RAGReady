import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

interface ConfidenceBadgeProps {
  confidence: number
}

function getConfidenceConfig(confidence: number) {
  const percentage = Math.round(confidence * 100)
  if (confidence >= 0.8) {
    return {
      label: 'High Confidence',
      percentage,
      className: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400',
    }
  }
  if (confidence >= 0.5) {
    return {
      label: 'Medium Confidence',
      percentage,
      className: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400',
    }
  }
  return {
    label: 'Low Confidence',
    percentage,
    className: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
  }
}

export function ConfidenceBadge({ confidence }: ConfidenceBadgeProps) {
  const config = getConfidenceConfig(confidence)

  return (
    <Badge variant="outline" className={cn('border-transparent', config.className)}>
      {config.label} — {config.percentage}%
    </Badge>
  )
}
