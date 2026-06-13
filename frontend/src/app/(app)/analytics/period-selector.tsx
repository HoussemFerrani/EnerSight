"use client"

import { useRouter } from "next/navigation"
import { useTransition } from "react"

import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

const PERIODS = ["hour", "day", "week", "month"] as const

export function PeriodSelector({ period }: { period: string }) {
  const router = useRouter()
  const [isPending, startTransition] = useTransition()

  function setPeriod(value: string) {
    const params = new URLSearchParams({ period: value })
    startTransition(() => router.replace(`/analytics?${params.toString()}`))
  }

  return (
    <div className="flex flex-wrap items-end gap-3">
      <div className="space-y-1">
        <Label className="text-xs text-muted-foreground">Bucket</Label>
        <Select value={period} onValueChange={(v) => v && setPeriod(v)} disabled={isPending}>
          <SelectTrigger className="w-32">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {PERIODS.map((p) => (
              <SelectItem key={p} value={p}>
                {p.charAt(0).toUpperCase() + p.slice(1)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </div>
  )
}
