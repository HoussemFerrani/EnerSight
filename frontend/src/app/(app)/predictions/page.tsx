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
          Estimates consumption from current conditions using the Random Forest model (~94.2% accuracy
          on the held-out test set). Enter realistic values and click Predict.
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
