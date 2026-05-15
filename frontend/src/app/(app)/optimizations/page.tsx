import {
  AirVent,
  Battery,
  DollarSign,
  Lightbulb,
  Sparkles,
  TrendingDown,
  Zap,
} from "lucide-react"

import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { backendFetch } from "@/lib/api/backend"

type Severity = "info" | "warning" | "critical"
type Category = "hvac" | "lighting" | "renewable" | "baseline" | "scheduling"

type Recommendation = {
  id: string
  title: string
  category: Category
  severity: Severity
  description: string
  suggestion: string
  estimated_savings_kwh: number
  estimated_savings_usd: number
  confidence: number
  supporting_metrics: Record<string, number>
}

type Report = {
  period_start: string
  period_end: string
  cost_per_kwh: number
  total_recommendations: number
  total_estimated_savings_kwh: number
  total_estimated_savings_usd: number
  recommendations: Recommendation[]
}

const CATEGORY_ICON: Record<Category, typeof AirVent> = {
  hvac: AirVent,
  lighting: Lightbulb,
  renewable: Battery,
  baseline: TrendingDown,
  scheduling: Zap,
}

const CATEGORY_LABEL: Record<Category, string> = {
  hvac: "HVAC",
  lighting: "Lighting",
  renewable: "Renewable",
  baseline: "Baseline",
  scheduling: "Scheduling",
}

type SearchParams = Promise<{ days?: string }>

export default async function OptimizationsPage({
  searchParams,
}: {
  searchParams: SearchParams
}) {
  const { days: daysParam } = await searchParams
  const days = Math.max(1, Math.min(parseInt(daysParam ?? "30", 10) || 30, 365))

  const { data, error } = await backendFetch<Report>(`/optimizations/?days=${days}`)
  const recs = data?.recommendations ?? []

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-bold tracking-tight">Optimizations</h1>
        <p className="text-sm text-muted-foreground">
          Actionable recommendations to reduce energy waste, ranked by projected monthly savings.
        </p>
      </header>

      <Alert>
        <Sparkles className="size-4" />
        <AlertDescription>
          <strong>How this works:</strong> A rules engine scans the last {days} days of energy
          readings for patterns that correlate with waste — HVAC running while empty, lights left
          on, unused renewable generation, weekend phantom loads. Each finding projects savings to
          a monthly horizon so you can compare them.
        </AlertDescription>
      </Alert>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>Failed to load recommendations: {error}</AlertDescription>
        </Alert>
      )}

      <section className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Recommendations
            </CardTitle>
            <Sparkles className="size-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{recs.length}</div>
            <p className="mt-1 text-xs text-muted-foreground">in {days}-day window</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Projected savings (kWh / month)
            </CardTitle>
            <TrendingDown className="size-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-emerald-600">
              {(data?.total_estimated_savings_kwh ?? 0).toFixed(0)}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Projected savings (USD / month)
            </CardTitle>
            <DollarSign className="size-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-emerald-600">
              ${(data?.total_estimated_savings_usd ?? 0).toFixed(2)}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Critical findings
            </CardTitle>
            <Zap className="size-4 text-destructive" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-destructive">
              {recs.filter((r) => r.severity === "critical").length}
            </div>
          </CardContent>
        </Card>
      </section>

      <section className="space-y-4">
        {recs.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <p className="text-sm text-muted-foreground">
                No optimization opportunities detected in the last {days} days. Healthy operation.
              </p>
            </CardContent>
          </Card>
        ) : (
          recs.map((rec) => <RecommendationCard key={rec.id} rec={rec} />)
        )}
      </section>
    </div>
  )
}

function RecommendationCard({ rec }: { rec: Recommendation }) {
  const Icon = CATEGORY_ICON[rec.category] ?? Sparkles
  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="flex items-start gap-3">
            <div className="rounded-md bg-muted p-2">
              <Icon className="size-5 text-foreground" />
            </div>
            <div>
              <CardTitle className="text-lg">{rec.title}</CardTitle>
              <div className="mt-1 flex flex-wrap gap-1.5">
                <Badge variant="outline">{CATEGORY_LABEL[rec.category]}</Badge>
                <Badge variant={severityVariant(rec.severity)}>{rec.severity}</Badge>
                <Badge variant="ghost">
                  confidence {(rec.confidence * 100).toFixed(0)}%
                </Badge>
              </div>
            </div>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold text-emerald-600">
              ${rec.estimated_savings_usd.toFixed(2)}
              <span className="ml-1 text-xs font-normal text-muted-foreground">/ month</span>
            </div>
            <p className="text-xs text-muted-foreground">
              ≈ {rec.estimated_savings_kwh.toFixed(0)} kWh / month
            </p>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-sm">{rec.description}</p>
        <div className="rounded-md border border-dashed bg-muted/30 p-3">
          <p className="text-xs font-semibold uppercase text-muted-foreground">
            Recommended action
          </p>
          <p className="mt-1 text-sm">{rec.suggestion}</p>
        </div>
        {Object.keys(rec.supporting_metrics).length > 0 && (
          <details className="text-xs text-muted-foreground">
            <summary className="cursor-pointer select-none">Supporting metrics</summary>
            <dl className="mt-2 grid grid-cols-2 gap-x-4 gap-y-1">
              {Object.entries(rec.supporting_metrics).map(([k, v]) => (
                <div key={k} className="flex justify-between gap-2">
                  <dt className="font-mono">{k}</dt>
                  <dd className="font-mono">{v}</dd>
                </div>
              ))}
            </dl>
          </details>
        )}
      </CardContent>
    </Card>
  )
}

function severityVariant(s: Severity) {
  if (s === "critical") return "destructive" as const
  if (s === "warning") return "default" as const
  return "secondary" as const
}
