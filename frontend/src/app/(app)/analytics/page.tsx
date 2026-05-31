import { ArrowUp, BarChart3, DollarSign, TrendingUp } from "lucide-react"

import { Alert, AlertDescription } from "@/components/ui/alert"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { backendFetch } from "@/lib/api/backend"

import { AggregateChart } from "./aggregate-chart"
import { PeriodSelector } from "./period-selector"

type Summary = {
  total_consumption: number
  average_daily: number
  peak_consumption: number
  peak_timestamp: string
  lowest_consumption: number
  lowest_timestamp: string
  total_cost?: number | null
  period_start: string
  period_end: string
  data_points: number
}

type Aggregated = {
  period_start: string
  period_end: string
  total: number
  average: number
  min: number
  max: number
  count: number
}

type Cost = {
  period_start: string
  period_end: string
  total_kwh: number
  cost_per_kwh: number
  total_cost: number
  currency: string
}

type SearchParams = Promise<{ days?: string; period?: string; rate?: string }>

const PERIODS = {
  hour: { label: "Hourly", days: 2 },
  day: { label: "Daily", days: 30 },
  week: { label: "Weekly", days: 90 },
  month: { label: "Monthly", days: 365 },
}

export default async function AnalyticsPage({ searchParams }: { searchParams: SearchParams }) {
  const { period: periodParam, rate: rateParam } = await searchParams
  const period = (periodParam ?? "day") as keyof typeof PERIODS
  const rate = parseFloat(rateParam ?? "0.12")

  const days = PERIODS[period]?.days ?? 30
  const end = new Date()
  const start = new Date(end.getTime() - days * 24 * 60 * 60 * 1000)
  const qsBase = `start_date=${start.toISOString()}&end_date=${end.toISOString()}`

  const [summaryRes, aggRes, costRes] = await Promise.all([
    backendFetch<Summary>(`/analytics/summary?${qsBase}&cost_per_kwh=${rate}`),
    backendFetch<Aggregated[]>(`/analytics/aggregated?${qsBase}&period=${period}`),
    backendFetch<Cost>(`/analytics/cost?${qsBase}&cost_per_kwh=${rate}`),
  ])

  const summary = summaryRes.data
  const aggregated = aggRes.data ?? []
  const cost = costRes.data
  const err = summaryRes.error || aggRes.error || costRes.error

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Analytics</h1>
          <p className="text-sm text-muted-foreground">
            Aggregated consumption, peaks, and cost over time.
          </p>
        </div>
        <PeriodSelector period={period} rate={rate} />
      </header>

      {err && (
        <Alert variant="destructive">
          <AlertDescription>Failed to load analytics: {err}</AlertDescription>
        </Alert>
      )}

      <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          icon={BarChart3}
          label="Total consumption"
          value={summary ? `${Math.round(summary.total_consumption).toLocaleString()} kWh` : "—"}
        />
        <StatCard
          icon={TrendingUp}
          label="Daily average"
          value={summary ? `${Math.round(summary.average_daily).toLocaleString()} kWh` : "—"}
        />
        <StatCard
          icon={ArrowUp}
          label="Peak"
          value={summary ? `${summary.peak_consumption.toFixed(1)} kWh` : "—"}
          accent="text-orange-600"
          sub={summary && new Date(summary.peak_timestamp).toLocaleString()}
        />
        <StatCard
          icon={DollarSign}
          label="Estimated cost"
          value={cost ? `${cost.currency} ${cost.total_cost.toFixed(2)}` : "—"}
          accent="text-emerald-600"
          sub={cost && `@ ${cost.cost_per_kwh.toFixed(3)}/kWh`}
        />
      </section>

      <Card>
        <CardHeader>
          <CardTitle>{PERIODS[period]?.label} consumption</CardTitle>
        </CardHeader>
        <CardContent>
          {aggregated.length === 0 ? (
            <p className="py-12 text-center text-sm text-muted-foreground">
              No data in this period.
            </p>
          ) : (
            <AggregateChart data={aggregated} />
          )}
        </CardContent>
      </Card>
    </div>
  )
}

function StatCard({
  icon: Icon,
  label,
  value,
  accent,
  sub,
}: {
  icon: React.ComponentType<{ className?: string }>
  label: string
  value: string
  accent?: string
  sub?: string | false | null
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{label}</CardTitle>
        <Icon className={`size-4 ${accent ?? "text-muted-foreground"}`} />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {sub && <p className="mt-1 text-xs text-muted-foreground">{sub}</p>}
      </CardContent>
    </Card>
  )
}
