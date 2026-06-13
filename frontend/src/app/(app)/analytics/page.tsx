import {
  ArrowDownRight,
  ArrowUp,
  ArrowUpRight,
  BarChart3,
  DollarSign,
  TrendingDown,
  TrendingUp,
} from "lucide-react"

import { Alert, AlertDescription } from "@/components/ui/alert"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { backendFetch } from "@/lib/api/backend"

import { AggregateChart } from "./aggregate-chart"
import {
  DistributionChart,
  FactorsChart,
  HourlyProfileChart,
  OccupancyChart,
  RenewableChart,
  TempScatterChart,
  WeekdayChart,
} from "./breakdown-charts"
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

type Comparison = {
  current_period: Aggregated
  comparison_period: Aggregated
  difference: number
  percentage_change: number
  comparison_type: string
}

type Trends = {
  period_days: number
  data_points: number
  trend_direction: "increasing" | "decreasing" | "stable"
  trend_percentage: number
}

type Breakdown = {
  hourly_profile: { hour: number; average: number; max: number; count: number }[]
  weekday_profile: { weekday: number; average: number; count: number }[]
  temperature_scatter: { temperature: number; consumption: number; hvac: boolean }[]
  factors: {
    hvac: { on: number | null; off: number | null }
    lighting: { on: number | null; off: number | null }
    holiday: { on: number | null; off: number | null }
  }
  occupancy_profile: { occupancy: number; average: number; count: number }[]
  renewable_timeseries: { timestamp: string; consumption: number; renewable: number }[]
  distribution: { range_start: number; range_end: number; count: number }[]
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

  const [summaryRes, aggRes, costRes, compareRes, trendsRes, breakdownRes] = await Promise.all([
    backendFetch<Summary>(`/analytics/summary?${qsBase}&cost_per_kwh=${rate}`),
    backendFetch<Aggregated[]>(`/analytics/aggregated?${qsBase}&period=${period}`),
    backendFetch<Cost>(`/analytics/cost?${qsBase}&cost_per_kwh=${rate}`),
    backendFetch<Comparison>(
      `/analytics/compare?current_start=${start.toISOString()}&current_end=${end.toISOString()}&comparison_type=previous_period`,
    ),
    backendFetch<Trends>(`/analytics/trends?days=${days}`),
    backendFetch<Breakdown>(`/analytics/breakdown?${qsBase}`),
  ])

  const summary = summaryRes.data
  const aggregated = aggRes.data ?? []
  const cost = costRes.data
  const comparison = compareRes.data
  const trends = trendsRes.data
  const breakdown = breakdownRes.data
  const err =
    summaryRes.error || aggRes.error || costRes.error || breakdownRes.error

  const pct = comparison?.percentage_change ?? 0
  const trendUp = trends?.trend_direction === "increasing"

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Analytics</h1>
          <p className="text-sm text-muted-foreground">
            Consumption patterns, drivers, costs, and trends over time.
          </p>
        </div>
        <PeriodSelector period={period} />
      </header>

      {err && (
        <Alert variant="destructive">
          <AlertDescription>Failed to load analytics: {err}</AlertDescription>
        </Alert>
      )}

      <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <StatCard
          icon={BarChart3}
          label="Total consumption"
          value={summary ? `${Math.round(summary.total_consumption).toLocaleString()} kWh` : "—"}
          sub={summary && `${summary.data_points.toLocaleString()} readings`}
        />
        <StatCard
          icon={TrendingUp}
          label="Daily average"
          value={summary ? `${Math.round(summary.average_daily).toLocaleString()} kWh` : "—"}
        />
        <StatCard
          icon={ArrowUp}
          label="Peak reading"
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
        <StatCard
          icon={pct >= 0 ? ArrowUpRight : ArrowDownRight}
          label="Vs previous period"
          value={comparison ? `${pct >= 0 ? "+" : ""}${pct.toFixed(1)}%` : "—"}
          accent={pct >= 0 ? "text-destructive" : "text-emerald-600"}
          sub={
            comparison &&
            `${Math.round(comparison.comparison_period.total).toLocaleString()} → ${Math.round(comparison.current_period.total).toLocaleString()} kWh`
          }
        />
        <StatCard
          icon={trendUp ? TrendingUp : TrendingDown}
          label="Trend"
          value={trends ? trends.trend_direction : "—"}
          accent={trendUp ? "text-destructive" : "text-emerald-600"}
          sub={trends && `${trends.trend_percentage >= 0 ? "+" : ""}${trends.trend_percentage}% over ${trends.period_days} days`}
        />
      </section>

      <ChartCard title={`${PERIODS[period]?.label} consumption`}>
        {aggregated.length === 0 ? (
          <EmptyChart />
        ) : (
          <AggregateChart data={aggregated} />
        )}
      </ChartCard>

      <section className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <ChartCard
          title="Time-of-day profile"
          description="Average and max consumption for each hour of the day"
        >
          {breakdown?.hourly_profile?.length ? (
            <HourlyProfileChart data={breakdown.hourly_profile} />
          ) : (
            <EmptyChart />
          )}
        </ChartCard>

        <ChartCard
          title="Day-of-week profile"
          description="Average reading by weekday"
        >
          {breakdown?.weekday_profile?.length ? (
            <WeekdayChart data={breakdown.weekday_profile} />
          ) : (
            <EmptyChart />
          )}
        </ChartCard>

        <ChartCard
          title="Temperature vs consumption"
          description="Each point is one reading, split by HVAC state"
        >
          {breakdown?.temperature_scatter?.length ? (
            <TempScatterChart data={breakdown.temperature_scatter} />
          ) : (
            <EmptyChart />
          )}
        </ChartCard>

        <ChartCard
          title="Consumption distribution"
          description="How readings spread across kWh ranges"
        >
          {breakdown?.distribution?.length ? (
            <DistributionChart data={breakdown.distribution} />
          ) : (
            <EmptyChart />
          )}
        </ChartCard>

        <ChartCard
          title="Equipment & context impact"
          description="Average consumption with HVAC / lighting on vs off, holidays vs regular days"
        >
          {breakdown?.factors ? <FactorsChart data={breakdown.factors} /> : <EmptyChart />}
        </ChartCard>

        <ChartCard
          title="Occupancy impact"
          description="Average consumption by number of people present"
        >
          {breakdown?.occupancy_profile?.length ? (
            <OccupancyChart data={breakdown.occupancy_profile} />
          ) : (
            <EmptyChart />
          )}
        </ChartCard>
      </section>

      <ChartCard
        title="Consumption vs renewable generation"
        description="Total consumption against on-site renewable production"
      >
        {breakdown?.renewable_timeseries?.length ? (
          <RenewableChart data={breakdown.renewable_timeseries} />
        ) : (
          <EmptyChart />
        )}
      </ChartCard>
    </div>
  )
}

function ChartCard({
  title,
  description,
  children,
}: {
  title: string
  description?: string
  children: React.ReactNode
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        {description && <p className="text-sm text-muted-foreground">{description}</p>}
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  )
}

function EmptyChart() {
  return (
    <p className="py-12 text-center text-sm text-muted-foreground">No data in this period.</p>
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
        <div className="text-2xl font-bold capitalize">{value}</div>
        {sub && <p className="mt-1 text-xs text-muted-foreground">{sub}</p>}
      </CardContent>
    </Card>
  )
}
