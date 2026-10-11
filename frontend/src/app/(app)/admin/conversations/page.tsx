"use client";

import { useQuery } from "@tanstack/react-query";
import { Search } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Input, Select } from "@/components/ui/input";
import { Empty, ErrorBanner, Pager, Spinner } from "@/components/ui/misc";
import { api, qs } from "@/lib/api";
import { STATUS_LABEL, STATUS_TONE } from "@/lib/labels";
import type { AdminConversationRow, ConversationStatus, Paged } from "@/lib/types";
import { formatDateTime, formatNumber } from "@/lib/utils";

export default function ConversationsPage() {
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState<ConversationStatus | "">("");
  const [q, setQ] = useState("");
  const [debounced, setDebounced] = useState("");

  useEffect(() => {
    const t = setTimeout(() => {
      setDebounced(q);
      setPage(1);
    }, 350);
    return () => clearTimeout(t);
  }, [q]);

  const { data, isLoading, error } = useQuery({
    queryKey: ["admin-conversations", page, status, debounced],
    queryFn: () => api.get<Paged<AdminConversationRow>>(`/admin/conversations${qs({ page, page_size: 20, status, q: debounced })}`),
    placeholderData: (prev) => prev,
  });

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="me-auto text-lg font-bold">گفتگوها</h1>
        <div className="relative">
          <Search className="pointer-events-none absolute start-3 top-3 h-4 w-4 text-muted-foreground" />
          <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="جستجو در عنوان، متن پیام‌ها یا ایمیل…" className="w-72 ps-9" aria-label="جستجو" />
        </div>
        <Select
          value={status}
          onChange={(e) => {
            setStatus(e.target.value as ConversationStatus | "");
            setPage(1);
          }}
          className="w-48"
          aria-label="فیلتر وضعیت"
        >
          <option value="">همه‌ی وضعیت‌ها</option>
          {(Object.keys(STATUS_LABEL) as ConversationStatus[]).map((s) => (
            <option key={s} value={s}>
              {STATUS_LABEL[s]}
            </option>
          ))}
        </Select>
      </div>

      <ErrorBanner error={error} />
      {isLoading ? <Spinner className="mx-auto mt-6" /> : null}
      {data && data.items.length === 0 ? <Empty>گفتگویی با این فیلتر پیدا نشد.</Empty> : null}
      {data && data.items.length > 0 ? (
        <Card className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-muted text-xs text-muted-foreground">
              <tr>
                <th className="p-3 text-start">عنوان</th>
                <th className="p-3 text-start">کاربر</th>
                <th className="p-3 text-start">وضعیت</th>
                <th className="p-3 text-start">پیام‌ها</th>
                <th className="p-3 text-start">آخرین فعالیت</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((c) => (
                <tr key={c.id} className="border-t border-border hover:bg-muted/40">
                  <td className="max-w-md p-3">
                    <Link href={`/admin/conversations/${c.id}`} className="font-medium text-primary hover:underline" dir="auto">
                      {c.title || "(بدون عنوان)"}
                    </Link>
                  </td>
                  <td className="p-3" dir="ltr">
                    {c.user.email}
                  </td>
                  <td className="p-3">
                    <Badge tone={STATUS_TONE[c.status]}>{STATUS_LABEL[c.status]}</Badge>
                  </td>
                  <td className="p-3">{formatNumber(c.message_count)}</td>
                  <td className="p-3 text-muted-foreground">{formatDateTime(c.updated_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      ) : null}
      {data ? <Pager page={data.page} pageSize={data.page_size} total={data.total} onPage={setPage} /> : null}
    </div>
  );
}
