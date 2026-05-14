"use client"

import { useEffect, useRef, useState } from "react"
import { Activity, Bolt, DollarSign, Droplet, Thermometer, Wifi, WifiOff } from "lucide-react"
import { CartesianGrid, Line, LineChart, XAxis, YAxis } from "recharts"

import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart"

type Reading = {
  timestamp: string
  consumption: number
  voltage: number
  current: number
  power_factor: number
  temperature: number
  humidity: number
  cost: number
  location: string
  device_id: string
}

const chartConfig: ChartConfig = {
  consumption: {
    label: "kWh",
    color: "var(--chart-1)",
  },
}

const MAX_POINTS = 60

export function LiveStream() {
  const [readings, setReadings] = useState<Reading[]>([])
  const [latest, setLatest] = useState<Reading | null>(null)
  const [connected, setConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    const apiBase = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1"
    const wsUrl = apiBase.replace(/^http/, "ws") + "/ws/energy/live"
    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => setConnected(true)
    ws.onclose = () => setConnected(false)
    ws.onerror = () => setConnected(false)
    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        if (msg.type === "energy_reading" && msg.data) {
          setLatest(msg.data)
          setReadings((prev) => [...prev.slice(-(MAX_POINTS - 1)), msg.data])
        }
      } catch {
        /* ignore non-JSON */
      }
    }

    return () => ws.close()
  }, [])

  const chartData = readings.map((r) => ({
    label: new Date(r.timestamp).toLocaleTimeString(undefined, { hour12: false }),
    consumption: r.consumption,
  }))

  return (
    <div className="space-y-6">
      <section className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <MetricCard
          icon={Bolt}
          label="Consumption"
          value={latest ? `${latest.consumption.toFixed(2)} kWh` : "—"}
          accent="text-primary"
        />
        <MetricCard
          icon={Thermometer}
          label="Temperature"
          value={latest ? `${latest.temperature.toFixed(1)} °C` : "—"}
          accent="text-orange-500"
        />
        <MetricCard
          icon={Droplet}
          label="Humidity"
          value={latest ? `${latest.humidity.toFixed(1)} %` : "—"}
          accent="text-blue-500"
        />
        <MetricCard
          icon={DollarSign}
          label="Cost"
          value={latest ? `$${latest.cost.toFixed(2)}` : "—"}
          accent="text-emerald-600"
        />
      </section>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0">
          <CardTitle className="flex items-center gap-2">
            <Activity className="size-4" />
            Live consumption stream
          </CardTitle>
          <Badge variant={connected ? "default" : "secondary"} className="gap-1">
            {connected ? <Wifi className="size-3" /> : <WifiOff className="size-3" />}
            {connected ? "connected" : "disconnected"}
          </Badge>
        </CardHeader>
        <CardContent>
          {chartData.length === 0 ? (
            <p className="py-12 text-center text-sm text-muted-foreground">Waiting for first reading…</p>
          ) : (
            <ChartContainer config={chartConfig} className="h-72 w-full">
              <LineChart data={chartData}>
                <CartesianGrid vertical={false} strokeDasharray="3 3" />
                <XAxis
                  dataKey="label"
                  tickLine={false}
                  axisLine={false}
                  tickMargin={8}
                  interval="preserveStartEnd"
                  minTickGap={48}
                />
                <YAxis tickLine={false} axisLine={false} tickMargin={8} />
                <ChartTooltip cursor={false} content={<ChartTooltipContent indicator="line" />} />
                <Line
                  type="monotone"
                  dataKey="consumption"
                  stroke="var(--color-consumption)"
                  strokeWidth={2}
                  dot={false}
                  isAnimationActive={false}
                />
              </LineChart>
            </ChartContainer>
          )}
        </CardContent>
      </Card>

      {latest && (
        <Card>
          <CardHeader>
            <CardTitle>Latest reading</CardTitle>
          </CardHeader>
          <CardContent>
            <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm sm:grid-cols-3">
              {Object.entries(latest).map(([k, v]) => (
                <div key={k} className="flex flex-col">
                  <dt className="text-xs text-muted-foreground">{k}</dt>
                  <dd className="font-mono text-sm">{String(v)}</dd>
                </div>
              ))}
            </dl>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

function MetricCard({
  icon: Icon,
  label,
  value,
  accent,
}: {
  icon: React.ComponentType<{ className?: string }>
  label: string
  value: string
  accent?: string
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{label}</CardTitle>
        <Icon className={`size-4 ${accent ?? "text-muted-foreground"}`} />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
      </CardContent>
    </Card>
  )
}
