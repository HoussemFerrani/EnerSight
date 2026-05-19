import { Activity, ArrowDown, ArrowUp, Bolt, Calendar, FlaskConical, Gauge, ShieldAlert, Target, Zap } from "lucide-react"

import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { backendFetch } from "@/lib/api/backend"

import { AccuracyChart } from "./accuracy-chart"
import { ConsumptionChart } from "./consumption-chart"
import { DriftChart } from "./drift-chart"

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

type ModelEntry = {
  task: string
  algorithm: string
  variant?: string
  uses_lag_features?: boolean
  rmse?: number | null
  mae?: number | null
  r2?: number | null
  mape?: number | null
  accuracy_pct?: number | null
  contamination?: number
  flagged_count?: number
  total_records?: number
  flag_rate?: number | null
  note?: string
  sequence_length?: number
  epochs_trained?: number
}

type MetricsResponse = {
  generated_at: string
  dataset: { records: number; date_range: { start: string; end: string } }
  models: Record<string, ModelEntry>
}

type FoldSummary = {
  mean: number
  std: number
  min: number
  max: number
  folds: number[]
}

type EvaluationResponse = {
  generated_at: string
  dataset_records: number
  regression_cv: Record<
    string,
    {
      n_splits: number
      shuffle: boolean
      rmse: FoldSummary
      mae: FoldSummary
      mape: FoldSummary
      r2: FoldSummary
      accuracy_pct: FoldSummary
    }
  >
  anomaly: {
    ground_truth_positive?: number
    if_only?: AnomalyPRBlock
    hybrid?: AnomalyPRBlock
    novel_findings?: { count: number; percentage_of_dataset: number; note?: string }
    trained_contamination?: number
    note?: string
    caveat?: string
  }
}

type AnomalyPRBlock = {
  detected_positive: number
  true_positives: number
  false_positives: number
  false_negatives: number
  precision: number
  recall: number
  f1: number
}

type PredictionPoint = { timestamp: string; actual: number; predicted: number }
type PredictionsResponse = {
  generated_at: string
  models: Record<string, PredictionPoint[]>
}

type DriftSummary = {
  total_predictions: number
  backfilled: number
  pending_backfill: number
  live_mape: number | null
  live_accuracy_pct: number | null
}

type DriftPoint = { bucket_at: string; n: number; mape: number | null; mean_error: number | null }
type DriftResponse = { hours: number; bucket: string; series: DriftPoint[] }

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

  const [
    statsRes,
    chartRes,
    healthRes,
    metricsRes,
    evaluationRes,
    predictionsRes,
    driftSummaryRes,
    driftRes,
  ] = await Promise.all([
    backendFetch<WeekStats>("/energy/statistics?period=week"),
    backendFetch<ReadingsResponse>(`/energy/readings?${params}`),
    fetch(`${backendBase}/health`, { cache: "no-store" })
      .then((r) => (r.ok ? (r.json() as Promise<HealthResponse>) : null))
      .catch(() => null),
    backendFetch<MetricsResponse>("/ml/metrics"),
    backendFetch<EvaluationResponse>("/ml/evaluation"),
    backendFetch<PredictionsResponse>("/ml/predictions"),
    backendFetch<DriftSummary>("/ml/drift/summary"),
    backendFetch<DriftResponse>("/ml/drift?hours=168&bucket=hour"),
  ])

  const stats = statsRes.data
  const chartData = chartRes.data?.data ?? []
  const metrics = metricsRes.data
  const evaluation = evaluationRes.data
  const predictions = predictionsRes.data
  const driftSummary = driftSummaryRes.data
  const drift = driftRes.data
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

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="size-4 text-primary" />
            Model accuracy
          </CardTitle>
        </CardHeader>
        <CardContent>
          {!metrics ? (
            <p className="py-6 text-sm text-muted-foreground">
              No metrics yet. Run{" "}
              <code className="rounded bg-muted px-1 py-0.5 text-xs">
                python -m ml.training.train_models
              </code>{" "}
              to generate them.
            </p>
          ) : (
            <ModelMetricsTable metrics={metrics} />
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FlaskConical className="size-4 text-primary" />
            Cross-validation stability
          </CardTitle>
        </CardHeader>
        <CardContent>
          {!evaluation ? (
            <p className="py-6 text-sm text-muted-foreground">
              No CV results yet. Run{" "}
              <code className="rounded bg-muted px-1 py-0.5 text-xs">
                python -m ml.evaluation.evaluate
              </code>{" "}
              to generate them.
            </p>
          ) : (
            <CrossValidationTable evaluation={evaluation} />
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="size-4 text-primary" />
            Predicted vs actual — Random Forest baseline
          </CardTitle>
        </CardHeader>
        <CardContent>
          {!predictions?.models.regression_random_forest_baseline?.length ? (
            <p className="py-6 text-sm text-muted-foreground">
              No prediction samples yet. Run{" "}
              <code className="rounded bg-muted px-1 py-0.5 text-xs">
                python -m ml.evaluation.evaluate
              </code>
              .
            </p>
          ) : (
            <>
              <AccuracyChart points={predictions.models.regression_random_forest_baseline} />
              <p className="mt-3 text-xs text-muted-foreground">
                Solid = actual, dashed = predicted. Vertical gaps are model errors —
                look for systematic over/under-prediction at peaks.
              </p>
            </>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ShieldAlert className="size-4 text-primary" />
            Anomaly detector quality
          </CardTitle>
        </CardHeader>
        <CardContent>
          {!evaluation?.anomaly ? (
            <p className="py-6 text-sm text-muted-foreground">No anomaly evaluation yet.</p>
          ) : (
            <AnomalyEvalCard anomaly={evaluation.anomaly} />
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="size-4 text-primary" />
            Live drift monitoring
          </CardTitle>
        </CardHeader>
        <CardContent>
          <LiveDriftCard summary={driftSummary} series={drift?.series ?? []} />
        </CardContent>
      </Card>
    </div>
  )
}

function ModelMetricsTable({ metrics }: { metrics: MetricsResponse }) {
  const entries = Object.entries(metrics.models)
  const generated = new Date(metrics.generated_at).toLocaleString()

  return (
    <div className="space-y-3">
      <p className="text-xs text-muted-foreground">
        Last trained: {generated} · {metrics.dataset.records.toLocaleString()} records
      </p>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-left text-xs uppercase text-muted-foreground">
              <th className="py-2 pr-4">Model</th>
              <th className="py-2 pr-4">Accuracy</th>
              <th className="py-2 pr-4">MAPE</th>
              <th className="py-2 pr-4">RMSE</th>
              <th className="py-2 pr-4">MAE</th>
              <th className="py-2 pr-4">R²</th>
              <th className="py-2">Notes</th>
            </tr>
          </thead>
          <tbody>
            {entries.map(([key, m]) => (
              <tr key={key} className="border-b last:border-0">
                <td className="py-2 pr-4 font-medium">{key}</td>
                <td className={`py-2 pr-4 font-semibold ${accuracyColor(m.accuracy_pct)}`}>
                  {m.accuracy_pct != null ? `${m.accuracy_pct.toFixed(1)}%` : "—"}
                </td>
                <td className="py-2 pr-4">{m.mape != null ? `${m.mape.toFixed(2)}%` : "—"}</td>
                <td className="py-2 pr-4">{fmt(m.rmse)}</td>
                <td className="py-2 pr-4">{fmt(m.mae)}</td>
                <td className="py-2 pr-4">{m.r2 != null ? m.r2.toFixed(4) : "—"}</td>
                <td className="py-2 text-xs text-muted-foreground">{describe(m)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-muted-foreground">
        <strong>Accuracy</strong> = 100% − MAPE (mean absolute percentage error). 90%+ is good,
        70–90% is usable, &lt;70% needs work. RMSE/MAE are in kWh — lower is better. R² closer to
        1.0 is better. Lagged variants are benchmark-only; the{" "}
        <code className="rounded bg-muted px-1">/predict</code> endpoint uses the baseline model.
      </p>
    </div>
  )
}

function fmt(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—"
  return value.toFixed(2)
}

function accuracyColor(pct: number | null | undefined): string {
  if (pct == null || Number.isNaN(pct)) return ""
  if (pct >= 90) return "text-emerald-600"
  if (pct >= 70) return "text-amber-600"
  return "text-red-600"
}

function CrossValidationTable({ evaluation }: { evaluation: EvaluationResponse }) {
  const entries = Object.entries(evaluation.regression_cv)
  const generated = new Date(evaluation.generated_at).toLocaleString()

  return (
    <div className="space-y-3">
      <p className="text-xs text-muted-foreground">
        Last evaluated: {generated} · 5-fold cross-validation over{" "}
        {evaluation.dataset_records.toLocaleString()} rows
      </p>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-left text-xs uppercase text-muted-foreground">
              <th className="py-2 pr-4">Model</th>
              <th className="py-2 pr-4">Mean accuracy</th>
              <th className="py-2 pr-4">Std dev</th>
              <th className="py-2 pr-4">Worst fold</th>
              <th className="py-2 pr-4">Best fold</th>
              <th className="py-2">Stability</th>
            </tr>
          </thead>
          <tbody>
            {entries.map(([key, cv]) => {
              const acc = cv.accuracy_pct
              const stable = acc.std < 1.0
              return (
                <tr key={key} className="border-b last:border-0">
                  <td className="py-2 pr-4 font-medium">{key}</td>
                  <td className={`py-2 pr-4 font-semibold ${accuracyColor(acc.mean)}`}>
                    {acc.mean.toFixed(2)}%
                  </td>
                  <td className="py-2 pr-4">±{acc.std.toFixed(2)}%</td>
                  <td className="py-2 pr-4">{acc.min.toFixed(2)}%</td>
                  <td className="py-2 pr-4">{acc.max.toFixed(2)}%</td>
                  <td className="py-2">
                    <Badge variant={stable ? "default" : "secondary"}>
                      {stable ? "Stable" : "Variable"}
                    </Badge>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-muted-foreground">
        Std dev under 1% means the model's accuracy is consistent across data splits — you can
        trust the headline number. High std dev means accuracy depends on which slice of data you
        evaluate on.
      </p>
    </div>
  )
}

function AnomalyEvalCard({ anomaly }: { anomaly: EvaluationResponse["anomaly"] }) {
  if (!anomaly.hybrid) {
    return (
      <p className="text-sm text-muted-foreground">
        {anomaly.note ?? "Insufficient data for anomaly evaluation."}
      </p>
    )
  }

  const score = (v: number) => `${(v * 100).toFixed(1)}%`
  const badge = (v: number): "default" | "secondary" | "destructive" =>
    v >= 0.7 ? "default" : v >= 0.4 ? "secondary" : "destructive"

  return (
    <div className="space-y-4">
      <p className="text-xs text-muted-foreground">
        Production output is the <strong>hybrid</strong> (business rules OR IsolationForest). Recall vs
        rules is 1.0 by construction; what matters is precision and how many novel anomalies the IF
        catches that the rules miss.
      </p>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-left text-xs uppercase text-muted-foreground">
              <th className="py-2 pr-4">Strategy</th>
              <th className="py-2 pr-4">Precision</th>
              <th className="py-2 pr-4">Recall</th>
              <th className="py-2 pr-4">F1</th>
              <th className="py-2">Flagged</th>
            </tr>
          </thead>
          <tbody>
            {anomaly.if_only && (
              <tr className="border-b">
                <td className="py-2 pr-4 text-muted-foreground">IsolationForest only</td>
                <td className="py-2 pr-4">{score(anomaly.if_only.precision)}</td>
                <td className="py-2 pr-4">{score(anomaly.if_only.recall)}</td>
                <td className="py-2 pr-4">
                  <Badge variant={badge(anomaly.if_only.f1)}>{score(anomaly.if_only.f1)}</Badge>
                </td>
                <td className="py-2 text-xs text-muted-foreground">{anomaly.if_only.detected_positive}</td>
              </tr>
            )}
            <tr>
              <td className="py-2 pr-4 font-semibold">Hybrid (rules + IF) ★</td>
              <td className="py-2 pr-4">{score(anomaly.hybrid.precision)}</td>
              <td className="py-2 pr-4">{score(anomaly.hybrid.recall)}</td>
              <td className="py-2 pr-4">
                <Badge variant={badge(anomaly.hybrid.f1)}>{score(anomaly.hybrid.f1)}</Badge>
              </td>
              <td className="py-2 text-xs text-muted-foreground">{anomaly.hybrid.detected_positive}</td>
            </tr>
          </tbody>
        </table>
      </div>

      {anomaly.novel_findings && (
        <div className="rounded-md border border-dashed p-3">
          <p className="text-sm">
            <strong>{anomaly.novel_findings.count}</strong> novel findings
            <span className="text-muted-foreground">
              {" "}
              ({anomaly.novel_findings.percentage_of_dataset.toFixed(1)}% of dataset)
            </span>
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            Flagged by IsolationForest but matched no rule — these are the "unknown unknowns" the
            ML adds on top of the business rules. Worth manual triage.
          </p>
        </div>
      )}

      <div className="grid grid-cols-2 gap-2 text-xs text-muted-foreground sm:grid-cols-4">
        <span>Rule-matches: {anomaly.ground_truth_positive}</span>
        {anomaly.trained_contamination != null && (
          <span>IF contamination: {anomaly.trained_contamination.toFixed(2)}</span>
        )}
        {anomaly.hybrid && <span>Hybrid TP: {anomaly.hybrid.true_positives}</span>}
        {anomaly.hybrid && <span>Hybrid FP: {anomaly.hybrid.false_positives}</span>}
      </div>

      {anomaly.caveat && (
        <p className="text-xs italic text-muted-foreground">⚠ {anomaly.caveat}</p>
      )}
    </div>
  )
}

function Metric({
  label,
  value,
  variant,
}: {
  label: string
  value: string
  variant: "default" | "secondary" | "destructive"
}) {
  return (
    <div className="flex items-center justify-between rounded-md border p-3">
      <span className="text-sm text-muted-foreground">{label}</span>
      <Badge variant={variant}>{value}</Badge>
    </div>
  )
}

function LiveDriftCard({
  summary,
  series,
}: {
  summary: DriftSummary | null
  series: DriftPoint[]
}) {
  // No predictions have been logged yet — give the user actionable next steps
  // rather than an empty card.
  if (!summary || summary.total_predictions === 0) {
    return (
      <div className="space-y-3 py-4 text-sm text-muted-foreground">
        <p>
          No live predictions logged yet. Once you start calling{" "}
          <code className="rounded bg-muted px-1">/api/v1/predictions/predict</code> or{" "}
          <code className="rounded bg-muted px-1">/api/v1/predictions/forecast</code>, each call
          is logged automatically.
        </p>
        <p>
          To compute live accuracy, after some time call{" "}
          <code className="rounded bg-muted px-1">POST /api/v1/ml/backfill</code> — that joins
          predictions against{" "}
          <code className="rounded bg-muted px-1">energy_readings</code> to fill in actuals.
        </p>
      </div>
    )
  }

  const backfillable = summary.backfilled > 0
  const accColor = accuracyColor(summary.live_accuracy_pct)

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <KeyValue label="Logged predictions" value={summary.total_predictions.toLocaleString()} />
        <KeyValue label="With ground truth" value={summary.backfilled.toLocaleString()} />
        <KeyValue label="Pending backfill" value={summary.pending_backfill.toLocaleString()} />
        <KeyValue
          label="Live accuracy"
          value={summary.live_accuracy_pct != null ? `${summary.live_accuracy_pct.toFixed(1)}%` : "—"}
          accent={accColor}
        />
      </div>

      {backfillable && series.length > 0 ? (
        <>
          <DriftChart points={series} />
          <p className="text-xs text-muted-foreground">
            Solid line = bucketed MAPE per hour. Dashed grey = training-time MAPE (~5.8%). When
            the line stays above the dashed reference, your live data has drifted from what the
            model saw during training — time to retrain.
          </p>
        </>
      ) : (
        <p className="text-sm text-muted-foreground">
          {summary.backfilled === 0
            ? "Predictions logged but no actual values matched yet. Run POST /api/v1/ml/backfill once readings catch up."
            : "Not enough backfilled buckets to chart yet — keep predicting."}
        </p>
      )}
    </div>
  )
}

function KeyValue({
  label,
  value,
  accent,
}: {
  label: string
  value: string
  accent?: string
}) {
  return (
    <div className="rounded-md border p-3">
      <p className="text-xs uppercase text-muted-foreground">{label}</p>
      <p className={`text-lg font-semibold ${accent ?? ""}`}>{value}</p>
    </div>
  )
}

function describe(m: ModelEntry): string {
  if (m.task === "anomaly_detection") {
    const rate = m.flag_rate != null ? `${(m.flag_rate * 100).toFixed(1)}%` : "—"
    return `${m.flagged_count ?? 0} flagged (${rate}). Unsupervised — needs labels for precision/recall.`
  }
  if (m.task === "forecast") {
    return `LSTM seq=${m.sequence_length}, ${m.epochs_trained ?? "?"} epochs`
  }
  if (m.task === "regression") {
    return m.uses_lag_features ? "Uses lag features (1h, 24h, 168h, 24h rolling mean)" : "Baseline features only"
  }
  return ""
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
