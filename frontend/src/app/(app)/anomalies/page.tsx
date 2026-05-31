import { AlertTriangle, Brain, Sparkles } from "lucide-react"

import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { backendFetch } from "@/lib/api/backend"

import { RefreshButton } from "./refresh-button"

type Anomaly = {
  timestamp: string
  device_id: string
  consumption: number
  expected_consumption: number
  anomaly_score: number
  severity: "low" | "medium" | "high"
}

type Response = {
  anomalies_detected: number
  period_analyzed: string
  anomalies: Anomaly[]
}

type SearchParams = Promise<{ hours?: string }>

export default async function AnomaliesPage({ searchParams }: { searchParams: SearchParams }) {
  const { hours: hoursParam } = await searchParams
  const hours = Math.max(1, Math.min(parseInt(hoursParam ?? "24", 10) || 24, 720))

  const { data, error } = await backendFetch<Response>(`/anomalies/detect?hours=${hours}`)
  const anomalies = data?.anomalies ?? []
  const high = anomalies.filter((a) => a.severity === "high").length
  const medium = anomalies.filter((a) => a.severity === "medium").length

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Anomalies</h1>
          <p className="text-sm text-muted-foreground">
            Unusual energy consumption identified by the Isolation Forest model.
          </p>
        </div>
        <RefreshButton hours={hours} />
      </header>

      <Alert>
        <Brain className="size-4" />
        <AlertDescription>
          <strong>About anomaly detection:</strong> Isolation Forest flags readings that deviate from typical
          patterns. Anomalies often indicate equipment malfunction, inefficient device behavior, or unusual usage.
        </AlertDescription>
      </Alert>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>Failed to load anomalies: {error}</AlertDescription>
        </Alert>
      )}

      <section className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Detected</CardTitle>
            <Sparkles className="size-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{anomalies.length}</div>
            <p className="mt-1 text-xs text-muted-foreground">in {hours}h window</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">High</CardTitle>
            <AlertTriangle className="size-4 text-destructive" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-destructive">{high}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Medium</CardTitle>
            <AlertTriangle className="size-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-500">{medium}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Low</CardTitle>
            <AlertTriangle className="size-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{anomalies.length - high - medium}</div>
          </CardContent>
        </Card>
      </section>

      <Card>
        <CardHeader>
          <CardTitle>Detected anomalies</CardTitle>
        </CardHeader>
        <CardContent>
          {anomalies.length === 0 ? (
            <p className="py-12 text-center text-sm text-muted-foreground">
              No anomalies in the last {hours} hours. Healthy consumption pattern.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>When</TableHead>
                  <TableHead>Device</TableHead>
                  <TableHead className="text-right">Actual</TableHead>
                  <TableHead className="text-right">Expected</TableHead>
                  <TableHead className="text-right">Deviation</TableHead>
                  <TableHead>Severity</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {anomalies.slice(0, 50).map((a, i) => {
                  const delta = a.consumption - a.expected_consumption
                  const pct = (delta / a.expected_consumption) * 100
                  return (
                    <TableRow key={`${a.timestamp}-${i}`}>
                      <TableCell className="text-sm text-muted-foreground">
                        {new Date(a.timestamp).toLocaleString()}
                      </TableCell>
                      <TableCell className="font-mono text-xs">{a.device_id}</TableCell>
                      <TableCell className="text-right">{a.consumption.toFixed(1)} kWh</TableCell>
                      <TableCell className="text-right text-muted-foreground">
                        {a.expected_consumption.toFixed(1)} kWh
                      </TableCell>
                      <TableCell
                        className={`text-right font-medium ${delta > 0 ? "text-orange-600" : "text-blue-600"}`}
                      >
                        {delta > 0 ? "+" : ""}
                        {pct.toFixed(1)}%
                      </TableCell>
                      <TableCell>
                        <Badge variant={severityVariant(a.severity)}>{a.severity}</Badge>
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

function severityVariant(s: "low" | "medium" | "high") {
  if (s === "high") return "destructive" as const
  if (s === "medium") return "default" as const
  return "secondary" as const
}
