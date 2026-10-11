"use client";

import { useQuery } from "@tanstack/react-query";
import { GraduationCap } from "lucide-react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Empty, ErrorBanner, Spinner } from "@/components/ui/misc";
import { api } from "@/lib/api";
import { LESSON_LABEL, LESSON_TONE } from "@/lib/labels";
import type { Lesson } from "@/lib/types";
import { formatDateTime } from "@/lib/utils";

export default function MyLessonsPage() {
  const { data, isLoading, error } = useQuery({ queryKey: ["lessons"], queryFn: () => api.get<Lesson[]>("/chat/lessons") });
  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto max-w-4xl space-y-4 p-4 md:p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-lg font-bold">آموزش‌های من</h1>
            <p className="mt-1 text-sm text-muted-foreground">آنچه به دستیار یاد داده‌اید. پس از تأیید ادمین فعال می‌شود و برای همه‌ی تیم قابل استفاده است.</p>
          </div>
          <Button asChild>
            <Link href="/chat?teach=1">
              <GraduationCap className="h-4 w-4" /> آموزش جدید
            </Link>
          </Button>
        </div>
        <ErrorBanner error={error} />
        {isLoading ? <Spinner className="mx-auto" /> : null}
        {data && data.length === 0 ? <Empty>هنوز چیزی به دستیار یاد نداده‌اید.</Empty> : null}
        {data?.map((l) => (
          <Card key={l.id} className="space-y-2 p-4">
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="font-semibold" dir="auto">{l.title}</h2>
              <Badge tone={LESSON_TONE[l.status]}>{LESSON_LABEL[l.status]}</Badge>
              <span className="text-xs text-muted-foreground">{formatDateTime(l.created_at)}</span>
            </div>
            {l.applies_when ? <p className="text-sm text-muted-foreground" dir="auto">زمان استفاده: {l.applies_when}</p> : null}
            <pre className="max-h-48 overflow-auto whitespace-pre-wrap rounded bg-muted p-2 text-sm" dir="auto">{l.instruction}</pre>
            {l.review_note ? <p className="text-sm" dir="auto">یادداشت ادمین: {l.review_note}</p> : null}
          </Card>
        ))}
      </div>
    </div>
  );
}
