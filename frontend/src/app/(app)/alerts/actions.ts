"use server"

import { revalidatePath } from "next/cache"

import { backendFetch } from "@/lib/api/backend"

export async function acknowledgeAlert(id: number) {
  const res = await backendFetch(`/alerts/${id}/acknowledge`, { method: "POST", body: JSON.stringify({}) })
  if (res.error) return { ok: false, error: res.error }
  revalidatePath("/alerts")
  return { ok: true }
}

export async function resolveAlert(id: number) {
  const res = await backendFetch(`/alerts/${id}/resolve`, { method: "POST", body: JSON.stringify({}) })
  if (res.error) return { ok: false, error: res.error }
  revalidatePath("/alerts")
  return { ok: true }
}

export async function deleteAlert(id: number) {
  const res = await backendFetch(`/alerts/${id}`, { method: "DELETE" })
  if (res.error) return { ok: false, error: res.error }
  revalidatePath("/alerts")
  return { ok: true }
}

export async function sendTestEmail() {
  const res = await backendFetch<{ sent: boolean; to: string }>("/alerts/test-email", {
    method: "POST",
    body: JSON.stringify({}),
  })
  if (res.error) return { ok: false as const, error: res.error }
  return { ok: true as const, to: res.data?.to }
}
