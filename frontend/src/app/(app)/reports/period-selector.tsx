"use client"

import { useRouter, useSearchParams } from "next/navigation"
import { useTransition } from "react"

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

const PRESETS = [
  { value: "7", label: "Last 7 days" },
  { value: "14", label: "Last 14 days" },
  { value: "30", label: "Last 30 days" },
  { value: "90", label: "Last 90 days" },
  { value: "180", label: "Last 6 months" },
  { value: "365", label: "Last year" },
]

export function PeriodSelector({ days }: { days: number }) {
  const router = useRouter()
  const params = useSearchParams()
  const [, startTransition] = useTransition()

  function onChange(value: string | null) {
    if (value === null) return
    const next = new URLSearchParams(params)
    next.set("days", value)
    startTransition(() => router.replace(`/reports?${next.toString()}`))
  }

  return (
    <Select value={String(days)} onValueChange={onChange}>
      <SelectTrigger className="w-48">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {PRESETS.map((p) => (
          <SelectItem key={p.value} value={p.value}>
            {p.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
