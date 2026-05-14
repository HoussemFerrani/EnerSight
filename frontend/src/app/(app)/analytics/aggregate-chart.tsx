"use client"

import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts"

import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart"

type Aggregated = {
  period_start: string
  total: number
  average: number
  min: number
  max: number
  count: number
}

const config: ChartConfig = {
  total: {
    label: "Total kWh",
    color: "var(--chart-1)",
  },
}

export function AggregateChart({ data }: { data: Aggregated[] }) {
  const points = data.map((d) => ({
    label: new Date(d.period_start).toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "numeric",
    }),
    total: Math.round(d.total * 100) / 100,
  }))

  return (
    <ChartContainer config={config} className="h-72 w-full">
      <BarChart data={points}>
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
        <ChartTooltip cursor={false} content={<ChartTooltipContent />} />
        <Bar dataKey="total" fill="var(--color-total)" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ChartContainer>
  )
}
