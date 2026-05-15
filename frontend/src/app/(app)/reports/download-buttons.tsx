"use client"

import { FileDown, FileSpreadsheet, Loader2 } from "lucide-react"
import { useState } from "react"

import { Button } from "@/components/ui/button"
import { createClient } from "@/lib/supabase/client"

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1"

type Format = "pdf" | "csv"

export function DownloadButtons({ days }: { days: number }) {
  const [busy, setBusy] = useState<Format | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function download(format: Format) {
    setBusy(format)
    setError(null)
    try {
      const supabase = createClient()
      const {
        data: { session },
      } = await supabase.auth.getSession()
      if (!session?.access_token) {
        setError("Not signed in.")
        return
      }

      const path = format === "pdf" ? "/reports/period.pdf" : "/reports/period.csv"
      const res = await fetch(`${API_URL}${path}?days=${days}`, {
        headers: { Authorization: `Bearer ${session.access_token}` },
      })
      if (!res.ok) {
        setError(`Server returned ${res.status}: ${res.statusText}`)
        return
      }

      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      const cd = res.headers.get("Content-Disposition") || ""
      const match = /filename="?([^"]+)"?/.exec(cd)
      a.download = match?.[1] ?? `enersight-report.${format}`
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Download failed")
    } finally {
      setBusy(null)
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-3">
        <Button onClick={() => download("pdf")} disabled={busy !== null} className="gap-2">
          {busy === "pdf" ? (
            <Loader2 className="size-4 animate-spin" />
          ) : (
            <FileDown className="size-4" />
          )}
          Download PDF report
        </Button>
        <Button
          variant="outline"
          onClick={() => download("csv")}
          disabled={busy !== null}
          className="gap-2"
        >
          {busy === "csv" ? (
            <Loader2 className="size-4 animate-spin" />
          ) : (
            <FileSpreadsheet className="size-4" />
          )}
          Export CSV
        </Button>
      </div>
      {error && <p className="text-sm text-destructive">{error}</p>}
    </div>
  )
}
