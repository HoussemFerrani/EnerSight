import { Construction } from "lucide-react"

import { Card, CardContent } from "@/components/ui/card"

export function ComingSoon({ title, description }: { title: string; description: string }) {
  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-bold tracking-tight">{title}</h1>
        <p className="text-sm text-muted-foreground">{description}</p>
      </header>
      <Card className="border-dashed">
        <CardContent className="flex flex-col items-center gap-3 py-16 text-center">
          <Construction className="size-10 text-muted-foreground" />
          <p className="text-sm font-medium">Page coming soon</p>
          <p className="max-w-md text-sm text-muted-foreground">
            This page is being rebuilt in the Next.js migration. The Dashboard is functional — check back here once the
            remaining pages land.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
