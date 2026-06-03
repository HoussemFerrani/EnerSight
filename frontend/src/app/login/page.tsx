import { Suspense } from "react"
import { Activity, BarChart3, Bolt, ShieldCheck } from "lucide-react"

import { Alert, AlertDescription } from "@/components/ui/alert"
import { LoginForm } from "./login-form"

type SearchParams = Promise<{ error?: string }>

const HIGHLIGHTS = [
  {
    icon: Activity,
    title: "Real-time monitoring",
    desc: "Live consumption streamed straight to your dashboard.",
  },
  {
    icon: BarChart3,
    title: "Predictive analytics",
    desc: "Forecasts and anomaly detection powered by ML.",
  },
  {
    icon: ShieldCheck,
    title: "Secure by design",
    desc: "Authentication and row-level security via Supabase.",
  },
]

export default async function LoginPage({ searchParams }: { searchParams: SearchParams }) {
  const { error } = await searchParams

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      {/* Brand panel — hidden on small screens */}
      <div className="relative hidden flex-col justify-between bg-primary p-12 text-primary-foreground lg:flex">
        <div className="flex items-center gap-2">
          <Bolt className="size-6" />
          <span className="text-lg font-semibold tracking-tight">EnerSight</span>
        </div>

        <div className="space-y-8">
          <div className="space-y-3">
            <h1 className="text-3xl font-semibold leading-tight tracking-tight">
              Energy management,
              <br />
              made intelligent.
            </h1>
            <p className="max-w-md text-sm text-primary-foreground/70">
              Monitor, forecast, and optimize consumption from a single analytics platform.
            </p>
          </div>

          <ul className="space-y-5">
            {HIGHLIGHTS.map(({ icon: Icon, title, desc }) => (
              <li key={title} className="flex gap-3">
                <span className="mt-0.5 flex size-9 shrink-0 items-center justify-center rounded-md bg-primary-foreground/10">
                  <Icon className="size-4" />
                </span>
                <div className="space-y-0.5">
                  <p className="text-sm font-medium">{title}</p>
                  <p className="text-sm text-primary-foreground/60">{desc}</p>
                </div>
              </li>
            ))}
          </ul>
        </div>

        <p className="text-xs text-primary-foreground/50">© 2026 EnerSight. All rights reserved.</p>
      </div>

      {/* Form panel */}
      <div className="flex items-center justify-center bg-background p-6 sm:p-12">
        <div className="w-full max-w-sm space-y-8">
          <div className="flex items-center gap-2 lg:hidden">
            <Bolt className="size-6 text-primary" />
            <span className="text-lg font-semibold tracking-tight">EnerSight</span>
          </div>

          <div className="space-y-2">
            <h2 className="text-2xl font-semibold tracking-tight">Welcome back</h2>
            <p className="text-sm text-muted-foreground">Sign in to your account to continue.</p>
          </div>

          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <Suspense>
            <LoginForm />
          </Suspense>

          <p className="text-xs text-muted-foreground">
            Use your EnerSight account email and password.
          </p>
        </div>
      </div>
    </div>
  )
}
