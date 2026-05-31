"use server"

import { backendFetch } from "@/lib/api/backend"

export type PredictionInput = {
  temperature: number
  humidity: number
  occupancy: number
  hvac_usage: number
  lighting_usage: number
  equipment_usage: number
  renewable_energy: number
}

export type PredictionResult = {
  predicted_consumption: number
  model: string
  confidence: number
  features: Record<string, unknown>
}

export type PredictionModel = "rf" | "lstm"

export async function predict(
  input: PredictionInput,
  model: PredictionModel = "rf",
): Promise<{ ok: true; result: PredictionResult } | { ok: false; error: string }> {
  const { data, error } = await backendFetch<PredictionResult>(
    `/predictions/predict?model=${model}`,
    {
      method: "POST",
      body: JSON.stringify(input),
    },
  )
  if (error || !data) return { ok: false, error: error ?? "Unknown error" }
  return { ok: true, result: data }
}
