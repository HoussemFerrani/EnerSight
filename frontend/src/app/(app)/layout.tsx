import { redirect } from "next/navigation"

import { Sidebar } from "@/components/sidebar"
import { createClient } from "@/lib/supabase/server"

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const supabase = await createClient()
  const {
    data: { user },
  } = await supabase.auth.getUser()

  if (!user) {
    redirect("/login")
  }

  const { data: profile } = await supabase
    .from("profiles")
    .select("username, full_name, role")
    .eq("id", user.id)
    .single()

  return (
    <div className="flex min-h-screen bg-muted/30">
      <Sidebar
        user={{
          email: user.email ?? "",
          username: profile?.username ?? user.email?.split("@")[0] ?? "user",
          full_name: profile?.full_name ?? null,
          role: profile?.role ?? "user",
        }}
      />
      <main className="flex-1 overflow-auto">
        <div className="mx-auto max-w-7xl p-6 lg:p-8">{children}</div>
      </main>
    </div>
  )
}
