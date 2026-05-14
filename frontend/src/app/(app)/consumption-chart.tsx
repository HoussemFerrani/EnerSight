"use client"

import { Area, AreaChart, CartesianGrid, XAxis, YAxis } from "recharts"

import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart"

type Point = { time: string; value: number }

const config: ChartConfig = {
  value: {
    label: "kWh",
    color: "var(--chart-1)",
  },
}

export function ConsumptionChart({ points }: { points: Point[] }) {
  const data = points.map((p) => ({
    time: p.time,
    value: Math.round(p.value * 100) / 100,
    label: new Date(p.time).toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "numeric",
    }),
  }))

  return (
    <ChartContainer config={config} className="h-72 w-full">
      <AreaChart data={data}>
        <defs>
          <linearGradient id="consumption" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="var(--color-value)" stopOpacity={0.4} />
            <stop offset="95%" stopColor="var(--color-value)" stopOpacity={0.05} />
          </linearGradient>
        </defs>
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
        <Area
          type="monotone"
          dataKey="value"
          stroke="var(--color-value)"
          strokeWidth={2}
          fill="url(#consumption)"
        />
      </AreaChart>
    </ChartContainer>
  )
}
