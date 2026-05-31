import { Brain } from "lucide-react"

import { Alert, AlertDescription } from "@/components/ui/alert"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

import { PredictionForm } from "./prediction-form"

export default function PredictionsPage() {
  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-bold tracking-tight">Predictions</h1>
        <p className="text-sm text-muted-foreground">
          ML-based forecasts of energy consumption from environmental + usage inputs.
        </p>
      </header>

      <Alert>
        <Brain className="size-4" />
        <AlertDescription>
          Estimate consumption from current conditions using either the Random Forest (default) or the multivariate
          LSTM — both are trained on the loaded sample dataset and reach a similar R² (~0.55–0.59). Enter realistic
          values and pick a model to compare their outputs.
        </AlertDescription>
      </Alert>

      <Card>
        <CardHeader>
          <CardTitle>Predict consumption</CardTitle>
        </CardHeader>
        <CardContent>
          <PredictionForm />
        </CardContent>
      </Card>
    </div>
  )
}
