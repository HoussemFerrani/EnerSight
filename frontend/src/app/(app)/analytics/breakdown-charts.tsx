"use client"

import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Scatter,
  ScatterChart,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts"

import {
  ChartContainer,
  ChartLegend,
  ChartLegendContent,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart"

const WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

// ---------- Hourly profile ----------

type HourlyPoint = { hour: number; average: number; max: number; count: number }

const hourlyConfig: ChartConfig = {
  average: { label: "Avg kWh", color: "var(--chart-1)" },
  max: { label: "Max kWh", color: "var(--chart-2)" },
}

export function HourlyProfileChart({ data }: { data: HourlyPoint[] }) {
  const points = data.map((d) => ({ ...d, label: `${d.hour}:00` }))
  return (
    <ChartContainer config={hourlyConfig} className="h-64 w-full">
      <AreaChart data={points}>
        <CartesianGrid vertical={false} strokeDasharray="3 3" />
        <XAxis dataKey="label" tickLine={false} axisLine={false} tickMargin={8} minTickGap={24} />
        <YAxis tickLine={false} axisLine={false} tickMargin={8} width={40} />
        <ChartTooltip cursor={false} content={<ChartTooltipContent />} />
        <Area
          dataKey="max"
          type="monotone"
          stroke="var(--color-max)"
          fill="var(--color-max)"
          fillOpacity={0.08}
          strokeWidth={1.5}
        />
        <Area
          dataKey="average"
          type="monotone"
          stroke="var(--color-average)"
          fill="var(--color-average)"
          fillOpacity={0.25}
          strokeWidth={2}
        />
        <ChartLegend content={<ChartLegendContent />} />
      </AreaChart>
    </ChartContainer>
  )
}

// ---------- Weekday profile ----------

type WeekdayPoint = { weekday: number; average: number; count: number }

const weekdayConfig: ChartConfig = {
  average: { label: "Avg kWh", color: "var(--chart-3)" },
}

export function WeekdayChart({ data }: { data: WeekdayPoint[] }) {
  const points = data.map((d) => ({
    ...d,
    label: WEEKDAYS[d.weekday - 1] ?? String(d.weekday),
  }))
  return (
    <ChartContainer config={weekdayConfig} className="h-64 w-full">
      <BarChart data={points}>
        <CartesianGrid vertical={false} strokeDasharray="3 3" />
        <XAxis dataKey="label" tickLine={false} axisLine={false} tickMargin={8} />
        <YAxis tickLine={false} axisLine={false} tickMargin={8} width={40} />
        <ChartTooltip cursor={false} content={<ChartTooltipContent />} />
        <Bar dataKey="average" fill="var(--color-average)" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ChartContainer>
  )
}

// ---------- Temperature vs consumption scatter ----------

type ScatterPoint = { temperature: number; consumption: number; hvac: boolean }

const scatterConfig: ChartConfig = {
  hvacOn: { label: "HVAC on", color: "var(--chart-1)" },
  hvacOff: { label: "HVAC off", color: "var(--chart-4)" },
}

export function TempScatterChart({ data }: { data: ScatterPoint[] }) {
  const on = data.filter((d) => d.hvac)
  const off = data.filter((d) => !d.hvac)
  return (
    <ChartContainer config={scatterConfig} className="h-64 w-full">
      <ScatterChart margin={{ top: 8, right: 8 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis
          dataKey="temperature"
          type="number"
          name="Temperature"
          unit="°C"
          domain={["dataMin", "dataMax"]}
          tickLine={false}
          axisLine={false}
          tickMargin={8}
        />
        <YAxis
          dataKey="consumption"
          type="number"
          name="Consumption"
          unit=" kWh"
          domain={["auto", "auto"]}
          tickLine={false}
          axisLine={false}
          tickMargin={8}
          width={48}
        />
        <ZAxis range={[28, 28]} />
        <ChartTooltip cursor={{ strokeDasharray: "3 3" }} content={<ChartTooltipContent />} />
        <Scatter name="HVAC on" data={on} fill="var(--color-hvacOn)" fillOpacity={0.65} />
        <Scatter name="HVAC off" data={off} fill="var(--color-hvacOff)" fillOpacity={0.65} />
        <ChartLegend content={<ChartLegendContent />} />
      </ScatterChart>
    </ChartContainer>
  )
}

// ---------- Equipment / context impact ----------

type Factors = {
  hvac: { on: number | null; off: number | null }
  lighting: { on: number | null; off: number | null }
  holiday: { on: number | null; off: number | null }
}

const factorsConfig: ChartConfig = {
  on: { label: "On / Yes", color: "var(--chart-1)" },
  off: { label: "Off / No", color: "var(--chart-5)" },
}

export function FactorsChart({ data }: { data: Factors }) {
  const points = [
    { label: "HVAC", on: data.hvac.on ?? 0, off: data.hvac.off ?? 0 },
    { label: "Lighting", on: data.lighting.on ?? 0, off: data.lighting.off ?? 0 },
    { label: "Holiday", on: data.holiday.on ?? 0, off: data.holiday.off ?? 0 },
  ]
  return (
    <ChartContainer config={factorsConfig} className="h-64 w-full">
      <BarChart data={points}>
        <CartesianGrid vertical={false} strokeDasharray="3 3" />
        <XAxis dataKey="label" tickLine={false} axisLine={false} tickMargin={8} />
        <YAxis tickLine={false} axisLine={false} tickMargin={8} width={40} />
        <ChartTooltip cursor={false} content={<ChartTooltipContent />} />
        <Bar dataKey="on" fill="var(--color-on)" radius={[4, 4, 0, 0]} />
        <Bar dataKey="off" fill="var(--color-off)" radius={[4, 4, 0, 0]} />
        <ChartLegend content={<ChartLegendContent />} />
      </BarChart>
    </ChartContainer>
  )
}

// ---------- Occupancy impact ----------

type OccupancyPoint = { occupancy: number; average: number; count: number }

const occupancyConfig: ChartConfig = {
  average: { label: "Avg kWh", color: "var(--chart-2)" },
}

export function OccupancyChart({ data }: { data: OccupancyPoint[] }) {
  const points = data.map((d) => ({ ...d, label: `${d.occupancy}` }))
  return (
    <ChartContainer config={occupancyConfig} className="h-64 w-full">
      <BarChart data={points}>
        <CartesianGrid vertical={false} strokeDasharray="3 3" />
        <XAxis
          dataKey="label"
          tickLine={false}
          axisLine={false}
          tickMargin={8}
          label={{ value: "People present", position: "insideBottom", offset: -2, fontSize: 11 }}
          height={40}
        />
        <YAxis tickLine={false} axisLine={false} tickMargin={8} width={40} />
        <ChartTooltip cursor={false} content={<ChartTooltipContent />} />
        <Bar dataKey="average" fill="var(--color-average)" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ChartContainer>
  )
}

// ---------- Consumption vs renewable generation ----------

type RenewablePoint = { timestamp: string; consumption: number; renewable: number }

const renewableConfig: ChartConfig = {
  consumption: { label: "Consumption kWh", color: "var(--chart-1)" },
  renewable: { label: "Renewable kWh", color: "var(--chart-2)" },
}

export function RenewableChart({ data }: { data: RenewablePoint[] }) {
  const points = data.map((d) => ({
    ...d,
    label: new Date(d.timestamp).toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "numeric",
    }),
  }))
  return (
    <ChartContainer config={renewableConfig} className="h-72 w-full">
      <AreaChart data={points}>
        <CartesianGrid vertical={false} strokeDasharray="3 3" />
        <XAxis
          dataKey="label"
          tickLine={false}
          axisLine={false}
          tickMargin={8}
          interval="preserveStartEnd"
          minTickGap={48}
        />
        <YAxis tickLine={false} axisLine={false} tickMargin={8} width={48} />
        <ChartTooltip cursor={false} content={<ChartTooltipContent />} />
        <Area
          dataKey="consumption"
          type="monotone"
          stroke="var(--color-consumption)"
          fill="var(--color-consumption)"
          fillOpacity={0.2}
          strokeWidth={2}
        />
        <Area
          dataKey="renewable"
          type="monotone"
          stroke="var(--color-renewable)"
          fill="var(--color-renewable)"
          fillOpacity={0.3}
          strokeWidth={2}
        />
        <ChartLegend content={<ChartLegendContent />} />
      </AreaChart>
    </ChartContainer>
  )
}

// ---------- Consumption distribution histogram ----------

type DistributionBin = { range_start: number; range_end: number; count: number }

const distributionConfig: ChartConfig = {
  count: { label: "Readings", color: "var(--chart-4)" },
}

export function DistributionChart({ data }: { data: DistributionBin[] }) {
  const points = data.map((d) => ({
    ...d,
    label: `${d.range_start}–${d.range_end}`,
  }))
  return (
    <ChartContainer config={distributionConfig} className="h-64 w-full">
      <BarChart data={points}>
        <CartesianGrid vertical={false} strokeDasharray="3 3" />
        <XAxis
          dataKey="label"
          tickLine={false}
          axisLine={false}
          tickMargin={8}
          minTickGap={16}
          fontSize={10}
        />
        <YAxis tickLine={false} axisLine={false} tickMargin={8} width={40} allowDecimals={false} />
        <ChartTooltip cursor={false} content={<ChartTooltipContent />} />
        <Bar dataKey="count" fill="var(--color-count)" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ChartContainer>
  )
}
