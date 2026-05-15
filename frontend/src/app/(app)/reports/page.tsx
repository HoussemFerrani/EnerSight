import { FileText, Info } from "lucide-react"

import { Alert, AlertDescription } from "@/components/ui/alert"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

import { DownloadButtons } from "./download-buttons"
import { PeriodSelector } from "./period-selector"

type SearchParams = Promise<{ days?: string }>

export default async function ReportsPage({
  searchParams,
}: {
  searchParams: SearchParams
}) {
  const { days: daysParam } = await searchParams
  const days = Math.max(1, Math.min(parseInt(daysParam ?? "30", 10) || 30, 365))

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Reports</h1>
          <p className="text-sm text-muted-foreground">
            Download a shareable PDF summary or raw CSV export for any period.
          </p>
        </div>
        <PeriodSelector days={days} />
      </header>

      <Alert>
        <Info className="size-4" />
        <AlertDescription>
          The PDF report bundles an executive summary, period comparison, consumption trend,
          hourly profile, statistical outliers, and optimization recommendations into a single
          document. The CSV export is the raw reading-level dataset, suitable for spreadsheets
          and external analysis.
        </AlertDescription>
      </Alert>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="size-5 text-primary" />
            Period report — last {days} days
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <ul className="ml-5 list-disc space-y-1 text-sm text-muted-foreground">
            <li>Executive summary (total kWh, estimated cost, average daily, peak)</li>
            <li>Comparison vs the previous period of the same length</li>
            <li>Consumption trend (daily for windows ≥ 2 days, hourly otherwise)</li>
            <li>Hourly profile — average consumption by hour of day</li>
            <li>Statistical outliers (|z-score| &gt; 2)</li>
            <li>Optimization recommendations with projected monthly savings</li>
          </ul>
          <DownloadButtons days={days} />
        </CardContent>
      </Card>
    </div>
  )
}
