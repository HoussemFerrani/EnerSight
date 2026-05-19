"use client"

import { CartesianGrid, Line, LineChart, ReferenceLine, XAxis, YAxis } from "recharts"

import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart"

type Point = { bucket_at: string; n: number; mape: number | null; mean_error: number | null }

const config: ChartConfig = {
  mape: { label: "MAPE (%)", color: "var(--chart-1)" },
}

export function DriftChart({ points }: { points: Point[] }) {
  const data = points
    .filter((p) => p.mape != null)
    .map((p) => ({
      label: new Date(p.bucket_at).toLocaleString(undefined, {
        month: "short",
        day: "numeric",
        hour: "numeric",
      }),
      mape: Math.round((p.mape ?? 0) * 100) / 100,
      n: p.n,
    }))

  return (
    <ChartContainer config={config} className="h-64 w-full">
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
        <YAxis
          tickLine={false}
          axisLine={false}
          tickMargin={8}
          tickFormatter={(v) => `${v}%`}
        />
        <ChartTooltip cursor={false} content={<ChartTooltipContent indicator="line" />} />
        {/* Training-time MAPE baseline (~5.8% from Level 1/2). Anything above
            this means the model is doing worse in production than offline eval. */}
        <ReferenceLine y={5.8} stroke="var(--muted-foreground)" strokeDasharray="3 3" />
        <Line
          type="monotone"
          dataKey="mape"
          stroke="var(--color-mape)"
          strokeWidth={2}
          dot={false}
        />
      </LineChart>
    </ChartContainer>
  )
}
