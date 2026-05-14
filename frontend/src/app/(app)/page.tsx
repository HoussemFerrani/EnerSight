import { ArrowDown, ArrowUp, Bolt, Calendar, Gauge, Zap } from "lucide-react"

import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { backendFetch } from "@/lib/api/backend"

import { ConsumptionChart } from "./consumption-chart"

type WeekStats = {
  total_consumption: number
  average_daily: number
  peak_consumption: number
  minimum_consumption: number
  days: number
}

type ReadingsResponse = {
  data: Array<{ time: string; value: number; aggregation: string; window: string }>
}

type HealthResponse = {
  status: string
  components: Record<string, string>
}

export default async function DashboardPage() {
  const end = new Date()
  const start = new Date(end.getTime() - 7 * 24 * 60 * 60 * 1000)
  const params = new URLSearchParams({
    start_date: start.toISOString(),
    end_date: end.toISOString(),
    aggregation: "mean",
    window: "1h",
  })

  // /health is at the root, not under /api/v1
  const backendBase = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1").replace(/\/api\/v1\/?$/, "")

  const [statsRes, chartRes, healthRes] = await Promise.all([
    backendFetch<WeekStats>("/energy/statistics?period=week"),
    backendFetch<ReadingsResponse>(`/energy/readings?${params}`),
    fetch(`${backendBase}/health`, { cache: "no-store" })
      .then((r) => (r.ok ? (r.json() as Promise<HealthResponse>) : null))
      .catch(() => null),
  ])

  const stats = statsRes.data
  const chartData = chartRes.data?.data ?? []
  const apiError = statsRes.error || chartRes.error

  return (
    <div className="space-y-6">
      <header className="flex items-end justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-sm text-muted-foreground">
            Live overview of your energy consumption.
          </p>
        </div>
        {healthRes && (
          <Badge variant={healthRes.status === "healthy" ? "default" : "destructive"}>
            {healthRes.status}
          </Badge>
        )}
      </header>

      {apiError && (
        <Alert variant="destructive">
          <AlertDescription>Failed to load data: {apiError}</AlertDescription>
        </Alert>
      )}

      <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total this week"
          value={stats ? `${stats.total_consumption.toLocaleString()} kWh` : "—"}
          icon={Bolt}
        />
        <StatCard
          title="Daily average"
          value={stats ? `${Math.round(stats.average_daily).toLocaleString()} kWh` : "—"}
          icon={Calendar}
        />
        <StatCard
          title="Peak day"
          value={stats ? `${Math.round(stats.peak_consumption).toLocaleString()} kWh` : "—"}
          icon={ArrowUp}
          accent="text-orange-600"
        />
        <StatCard
          title="Quietest day"
          value={stats ? `${Math.round(stats.minimum_consumption).toLocaleString()} kWh` : "—"}
          icon={ArrowDown}
          accent="text-emerald-600"
        />
      </section>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="size-4 text-primary" />
            Hourly consumption — last 7 days
          </CardTitle>
        </CardHeader>
        <CardContent>
          {chartData.length > 0 ? (
            <ConsumptionChart points={chartData} />
          ) : (
            <p className="py-12 text-center text-sm text-muted-foreground">
              No data yet. Load readings into Supabase to see this chart.
            </p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Gauge className="size-4 text-primary" />
            System status
          </CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          {healthRes?.components &&
            Object.entries(healthRes.components).map(([name, status]) => (
              <div key={name} className="flex items-center justify-between rounded-md border p-3">
                <span className="text-sm capitalize text-muted-foreground">{name}</span>
                <Badge variant={status === "connected" || status === "operational" ? "default" : "secondary"}>
                  {status}
                </Badge>
              </div>
            ))}
        </CardContent>
      </Card>
    </div>
  )
}

function StatCard({
  title,
  value,
  icon: Icon,
  accent,
}: {
  title: string
  value: string
  icon: React.ComponentType<{ className?: string }>
  accent?: string
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
        <Icon className={`size-4 ${accent ?? "text-muted-foreground"}`} />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
      </CardContent>
    </Card>
  )
}
