"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import {
  Activity,
  AlertTriangle,
  BarChart3,
  Bell,
  Bolt,
  Brain,
  FileText,
  LayoutDashboard,
  LogOut,
  Sparkles,
} from "lucide-react"

import { signOut } from "@/app/login/actions"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { cn } from "@/lib/utils"

const NAV = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/realtime", label: "Real-time", icon: Activity },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/predictions", label: "Predictions", icon: Brain },
  { href: "/anomalies", label: "Anomalies", icon: AlertTriangle },
  { href: "/optimizations", label: "Optimizations", icon: Sparkles },
  { href: "/reports", label: "Reports", icon: FileText },
  { href: "/alerts", label: "Alerts", icon: Bell },
]

type Props = {
  user: { email: string; username: string; full_name: string | null; role: string }
}

export function Sidebar({ user }: Props) {
  const pathname = usePathname()
  const initials = (user.full_name || user.username || user.email)
    .split(" ")
    .map((s) => s[0])
    .slice(0, 2)
    .join("")
    .toUpperCase()

  return (
    <aside className="sticky top-0 hidden h-screen w-64 shrink-0 flex-col border-r bg-card md:flex">
      <div className="flex items-center gap-2 px-6 py-5">
        <Bolt className="size-6 text-primary" />
        <span className="text-lg font-semibold tracking-tight">EnerSight</span>
      </div>
      <Separator />
      <nav className="flex-1 space-y-1 p-3">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = href === "/" ? pathname === "/" : pathname.startsWith(href)
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                active
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
              )}
            >
              <Icon className="size-4" />
              {label}
            </Link>
          )
        })}
      </nav>
      <Separator />
      <div className="p-3">
        <div className="flex items-center gap-3 rounded-md p-2">
          <Avatar className="size-9">
            <AvatarFallback>{initials}</AvatarFallback>
          </Avatar>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium">{user.full_name || user.username}</p>
            <p className="truncate text-xs text-muted-foreground">{user.email}</p>
          </div>
        </div>
        <form action={signOut}>
          <Button variant="ghost" size="sm" type="submit" className="mt-1 w-full justify-start gap-2">
            <LogOut className="size-4" />
            Sign out
          </Button>
        </form>
      </div>
    </aside>
  )
}
