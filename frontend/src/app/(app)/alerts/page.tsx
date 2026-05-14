import { AlertTriangle, Bell, CheckCircle2, Info } from "lucide-react"

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

import { AlertRowActions } from "./row-actions"

type AlertRecord = {
  id: number
  user_id: string
  alert_type: string
  severity: "info" | "warning" | "critical"
  status: "pending" | "sent" | "acknowledged" | "resolved"
  title: string
  message: string
  current_value: number | null
  threshold_value: number | null
  email_sent: boolean
  push_sent: boolean
  created_at: string
  acknowledged_at: string | null
  resolved_at: string | null
}

type Summary = {
  total_alerts: number
  pending_alerts: number
  critical_alerts: number
  unacknowledged_alerts: number
  alerts_today: number
}

export default async function AlertsPage() {
  const [alertsRes, summaryRes] = await Promise.all([
    backendFetch<AlertRecord[]>("/alerts/?limit=100"),
    backendFetch<Summary>("/alerts/summary"),
  ])

  const alerts = alertsRes.data ?? []
  const summary = summaryRes.data
  const err = alertsRes.error || summaryRes.error

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-bold tracking-tight">Alerts</h1>
        <p className="text-sm text-muted-foreground">
          Notifications when consumption breaks your thresholds.
        </p>
      </header>

      {err && (
        <Alert variant="destructive">
          <AlertDescription>Failed to load alerts: {err}</AlertDescription>
        </Alert>
      )}

      <section className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <SummaryCard icon={Bell} label="Total" value={summary?.total_alerts ?? 0} />
        <SummaryCard icon={Info} label="Pending" value={summary?.pending_alerts ?? 0} />
        <SummaryCard
          icon={AlertTriangle}
          label="Critical"
          value={summary?.critical_alerts ?? 0}
          accent="text-destructive"
        />
        <SummaryCard
          icon={CheckCircle2}
          label="Today"
          value={summary?.alerts_today ?? 0}
          accent="text-emerald-600"
        />
      </section>

      <Card>
        <CardHeader>
          <CardTitle>Recent alerts</CardTitle>
        </CardHeader>
        <CardContent>
          {alerts.length === 0 ? (
            <p className="py-12 text-center text-sm text-muted-foreground">
              No alerts yet. They appear here when your consumption exceeds your threshold.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Severity</TableHead>
                  <TableHead>Title</TableHead>
                  <TableHead className="hidden md:table-cell">Value</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="hidden md:table-cell">Created</TableHead>
                  <TableHead className="w-0" />
                </TableRow>
              </TableHeader>
              <TableBody>
                {alerts.map((a) => (
                  <TableRow key={a.id}>
                    <TableCell>
                      <Badge variant={severityVariant(a.severity)}>{a.severity}</Badge>
                    </TableCell>
                    <TableCell className="font-medium">
                      <div>{a.title}</div>
                      <div className="text-xs text-muted-foreground">{a.message}</div>
                    </TableCell>
                    <TableCell className="hidden md:table-cell">
                      {a.current_value != null && a.threshold_value != null
                        ? `${a.current_value.toFixed(1)} / ${a.threshold_value.toFixed(0)} kWh`
                        : "—"}
                    </TableCell>
                    <TableCell>
                      <Badge variant={statusVariant(a.status)}>{a.status}</Badge>
                    </TableCell>
                    <TableCell className="hidden text-sm text-muted-foreground md:table-cell">
                      {new Date(a.created_at).toLocaleString()}
                    </TableCell>
                    <TableCell className="text-right">
                      <AlertRowActions id={a.id} status={a.status} />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

function SummaryCard({
  icon: Icon,
  label,
  value,
  accent,
}: {
  icon: React.ComponentType<{ className?: string }>
  label: string
  value: number
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

function severityVariant(s: AlertRecord["severity"]) {
  if (s === "critical") return "destructive" as const
  if (s === "warning") return "default" as const
  return "secondary" as const
}

function statusVariant(s: AlertRecord["status"]) {
  if (s === "resolved") return "secondary" as const
  if (s === "acknowledged") return "outline" as const
  return "default" as const
}
