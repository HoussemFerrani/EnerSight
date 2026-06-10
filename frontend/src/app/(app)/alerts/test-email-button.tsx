"use client"

import { useTransition } from "react"
import { Mail } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"

import { sendTestEmail } from "./actions"

export function TestEmailButton() {
  const [isPending, startTransition] = useTransition()

  function handleClick() {
    startTransition(async () => {
      const res = await sendTestEmail()
      if (res.ok) toast.success(`Test email sent to ${res.to ?? "your address"}`)
      else toast.error(`Test email failed: ${res.error ?? "unknown"}`)
    })
  }

  return (
    <Button variant="outline" onClick={handleClick} disabled={isPending}>
      <Mail className="mr-2 size-4" />
      {isPending ? "Sending..." : "Send test email"}
    </Button>
  )
}
