"use client"

import { useRouter, useSearchParams } from "next/navigation"
import { useTransition } from "react"
import { RefreshCw } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

const PRESETS = [
  { value: "6", label: "Last 6 hours" },
  { value: "24", label: "Last 24 hours" },
  { value: "72", label: "Last 3 days" },
  { value: "168", label: "Last 7 days" },
  { value: "720", label: "Last 30 days" },
]

export function RefreshButton({ hours }: { hours: number }) {
  const router = useRouter()
  const params = useSearchParams()
  const [isPending, startTransition] = useTransition()

  function onChange(value: string) {
    const next = new URLSearchParams(params)
    next.set("hours", value)
    startTransition(() => router.replace(`/anomalies?${next.toString()}`))
  }

  function refresh() {
    startTransition(() => router.refresh())
  }

  return (
    <div className="flex items-center gap-2">
      <Select value={String(hours)} onValueChange={onChange} disabled={isPending}>
        <SelectTrigger className="w-40">
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
      <Button variant="outline" size="icon" onClick={refresh} disabled={isPending} aria-label="Refresh">
        <RefreshCw className={`size-4 ${isPending ? "animate-spin" : ""}`} />
      </Button>
    </div>
  )
}
