"use client"

import { useTransition } from "react"
import { Check, CheckCheck, MoreHorizontal, Trash2 } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

import { acknowledgeAlert, deleteAlert, resolveAlert } from "./actions"

type Props = {
  id: number
  status: "pending" | "sent" | "acknowledged" | "resolved"
}

export function AlertRowActions({ id, status }: Props) {
  const [isPending, startTransition] = useTransition()

  function run(action: () => Promise<{ ok: boolean; error?: string }>, label: string) {
    startTransition(async () => {
      const res = await action()
      if (res.ok) toast.success(`${label} succeeded`)
      else toast.error(`${label} failed: ${res.error ?? "unknown"}`)
    })
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" disabled={isPending}>
          <MoreHorizontal className="size-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        {status !== "acknowledged" && status !== "resolved" && (
          <DropdownMenuItem onClick={() => run(() => acknowledgeAlert(id), "Acknowledge")}>
            <Check className="mr-2 size-4" /> Acknowledge
          </DropdownMenuItem>
        )}
        {status !== "resolved" && (
          <DropdownMenuItem onClick={() => run(() => resolveAlert(id), "Resolve")}>
            <CheckCheck className="mr-2 size-4" /> Resolve
          </DropdownMenuItem>
        )}
        <DropdownMenuItem
          variant="destructive"
          onClick={() => run(() => deleteAlert(id), "Delete")}
        >
          <Trash2 className="mr-2 size-4" /> Delete
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
