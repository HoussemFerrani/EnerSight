import { Suspense } from "react"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { LoginForm } from "./login-form"

type SearchParams = Promise<{ error?: string }>

export default async function LoginPage({ searchParams }: { searchParams: SearchParams }) {
  const { error } = await searchParams

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-indigo-500 to-purple-600 p-4">
      <Card className="w-full max-w-sm">
        <CardHeader className="space-y-1 text-center">
          <CardTitle className="text-3xl font-bold tracking-tight text-primary">EnerSight</CardTitle>
          <CardDescription>Energy Management & Analytics Platform</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <h2 className="text-xl font-semibold">Sign In</h2>
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          <Suspense>
            <LoginForm />
          </Suspense>
          <p className="text-center text-xs text-muted-foreground">
            Sign in with your Supabase account email and password.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
