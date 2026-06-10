"use client"

import { useState, useTransition } from "react"
import { Bolt, Zap } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Separator } from "@/components/ui/separator"

import { predict, type PredictionResult } from "./actions"

type FormState = {
  temperature: string
  humidity: string
  occupancy: string
  hvac_usage: string
  lighting_usage: string
  equipment_usage: string
  renewable_energy: string
}

const DEFAULTS: FormState = {
  temperature: "22.5",
  humidity: "45",
  occupancy: "15",
  hvac_usage: "12.5",
  lighting_usage: "3.2",
  equipment_usage: "8.7",
  renewable_energy: "5",
}

const FIELDS: Array<{ key: keyof FormState; label: string; unit: string; step?: string }> = [
  { key: "temperature", label: "Temperature", unit: "°C", step: "0.1" },
  { key: "humidity", label: "Humidity", unit: "%", step: "0.1" },
  { key: "occupancy", label: "Occupancy", unit: "people" },
  { key: "hvac_usage", label: "HVAC usage", unit: "kWh", step: "0.1" },
  { key: "lighting_usage", label: "Lighting usage", unit: "kWh", step: "0.1" },
  { key: "equipment_usage", label: "Equipment usage", unit: "kWh", step: "0.1" },
  { key: "renewable_energy", label: "Renewable", unit: "kWh", step: "0.1" },
]

export function PredictionForm() {
  const [form, setForm] = useState<FormState>(DEFAULTS)
  const [result, setResult] = useState<PredictionResult | null>(null)
  const [isPending, startTransition] = useTransition()

  function update(key: keyof FormState, value: string) {
    setForm({ ...form, [key]: value })
  }

  function submit() {
    const input = {
      temperature: parseFloat(form.temperature),
      humidity: parseFloat(form.humidity),
      occupancy: parseInt(form.occupancy, 10),
      hvac_usage: parseFloat(form.hvac_usage),
      lighting_usage: parseFloat(form.lighting_usage),
      equipment_usage: parseFloat(form.equipment_usage),
      renewable_energy: parseFloat(form.renewable_energy),
    }
    if (Object.values(input).some((v) => Number.isNaN(v))) {
      toast.error("Please fill in all fields with valid numbers")
      return
    }
    startTransition(async () => {
      const res = await predict(input)
      if (res.ok) {
        setResult(res.result)
        toast.success("Prediction complete")
      } else {
        toast.error(`Prediction failed: ${res.error}`)
      }
    })
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {FIELDS.map(({ key, label, unit, step }) => (
          <div key={key} className="space-y-2">
            <Label htmlFor={key}>
              {label} <span className="text-muted-foreground">({unit})</span>
            </Label>
            <Input
              id={key}
              type="number"
              step={step ?? "1"}
              value={form[key]}
              onChange={(e) => update(key, e.target.value)}
            />
          </div>
        ))}
        <div className="col-span-full mt-2">
          <Button onClick={submit} disabled={isPending} size="lg" className="w-full sm:w-auto">
            <Zap className="mr-2 size-4" />
            {isPending ? "Predicting..." : "Predict"}
          </Button>
        </div>
      </div>

      <Card className="self-start">
        <CardContent className="space-y-4 p-6">
          <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
            <Bolt className="size-4 text-primary" />
            Predicted consumption
          </div>
          {result ? (
            <>
              <div>
                <div className="text-4xl font-bold tracking-tight">
                  {result.predicted_consumption.toFixed(2)}
                  <span className="ml-1 text-base font-normal text-muted-foreground">kWh</span>
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  via {result.model} ({Math.round(result.confidence * 100)}% confidence)
                </p>
              </div>
              <Separator />
              <div className="space-y-1 text-xs">
                <p className="font-medium text-muted-foreground">Input features</p>
                {Object.entries(result.features).map(([k, v]) => (
                  <div key={k} className="flex justify-between">
                    <span className="text-muted-foreground">{k}</span>
                    <span className="font-mono">{String(v)}</span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <p className="text-sm text-muted-foreground">
              Fill in the fields and click <strong>Predict</strong> to see the model output.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
