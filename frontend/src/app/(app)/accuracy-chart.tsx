"use client"

import { CartesianGrid, Line, LineChart, XAxis, YAxis } from "recharts"

import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart"

type Point = { timestamp: string; actual: number; predicted: number }

const config: ChartConfig = {
  actual: { label: "Actual", color: "var(--chart-1)" },
  predicted: { label: "Predicted", color: "var(--chart-2)" },
}

export function AccuracyChart({ points }: { points: Point[] }) {
  // Two overlaid lines (actual vs predicted) on a shared time axis. Gap = error.
  const data = points.map((p) => ({
    label: new Date(p.timestamp).toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "numeric",
    }),
    actual: Math.round(p.actual * 100) / 100,
    predicted: Math.round(p.predicted * 100) / 100,
  }))

  return (
    <ChartContainer config={config} className="h-72 w-full">
      <LineChart data={data}>
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
          dataKey="actual"
          stroke="var(--color-actual)"
          strokeWidth={2}
          dot={false}
        />
        <Line
          type="monotone"
          dataKey="predicted"
          stroke="var(--color-predicted)"
          strokeWidth={2}
          strokeDasharray="4 4"
          dot={false}
        />
      </LineChart>
    </ChartContainer>
  )
}
