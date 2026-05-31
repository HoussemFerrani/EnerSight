"use client"

import { useRouter } from "next/navigation"
import { useTransition } from "react"

import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

const PERIODS = ["hour", "day", "week", "month"] as const

export function PeriodSelector({ period, rate }: { period: string; rate: number }) {
  const router = useRouter()
  const [isPending, startTransition] = useTransition()

  function setParam(key: string, value: string) {
    const params = new URLSearchParams({
      period: key === "period" ? value : period,
      rate: key === "rate" ? value : String(rate),
    })
    startTransition(() => router.replace(`/analytics?${params.toString()}`))
  }

  return (
    <div className="flex flex-wrap items-end gap-3">
      <div className="space-y-1">
        <Label className="text-xs text-muted-foreground">Bucket</Label>
        <Select value={period} onValueChange={(v) => v && setParam("period", v)} disabled={isPending}>
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
      <div className="space-y-1">
        <Label className="text-xs text-muted-foreground">Cost rate ($/kWh)</Label>
        <Input
          type="number"
          step="0.01"
          min="0"
          defaultValue={rate}
          onBlur={(e) => setParam("rate", e.target.value)}
          className="w-28"
          disabled={isPending}
        />
      </div>
    </div>
  )
}
