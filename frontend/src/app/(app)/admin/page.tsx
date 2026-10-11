"use client";

import { useQuery } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select } from "@/components/ui/input";
import { Empty, ErrorBanner, Spinner } from "@/components/ui/misc";
import { api } from "@/lib/api";
import { SOURCE_COLOR, SOURCE_LABEL, STATUS_LABEL } from "@/lib/labels";
import type { Analytics } from "@/lib/types";
import { formatDate, formatDateTime, formatNumber, formatPercent } from "@/lib/utils";

const TOOLTIP = { background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: 8, fontSize: 12 };
const STATUS_COLOR = { unresolved: "#94a3b8", pending_review: "#d97706", resolved: "#16a34a" } as const;

function Kpi({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <Card>
      <CardContent className="p-4">
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className="mt-1 text-3xl font-bold">{value}</p>
        {hint ? <p className="mt-1 text-xs text-muted-foreground">{hint}</p> : null}
      </CardContent>
    </Card>
  );
}

function ChartCard({ title, children }: { title: string; children: ReactNode }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      {/* charts keep LTR geometry; labels are Persian */}
      <CardContent className="h-72" dir="ltr">
        {children}
      </CardContent>
    </Card>
  );
}

export default function AnalyticsPage() {
  const [days, setDays] = useState(30);
  const { data, isLoading, error } = useQuery({ queryKey: ["analytics", days], queryFn: () => api.get<Analytics>(`/admin/analytics?days=${days}`) });

  if (isLoading) return <Spinner className="mx-auto mt-10 h-6 w-6" />;
  if (error || !data) return <ErrorBanner error={error} />;

  const sources = data.sources.map((s) => ({ ...s, label: SOURCE_LABEL[s.source] ?? s.source }));
  const statusData = (Object.keys(data.by_status) as (keyof typeof STATUS_COLOR)[]).map((k) => ({ name: STATUS_LABEL[k], value: data.by_status[k], key: k }));
  const webData = [
    { name: "جستجوی وب انجام‌شده", value: data.web.searches_performed, color: "#ea580c" },
    { name: "جستجوی وب صرفه‌جویی‌شده", value: data.web.searches_avoided, color: "#0891b2" },
  ];
  const noSources = sources.every((s) => s.count === 0);

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-bold">آمار و تحلیل</h1>
        <Select value={days} onChange={(e) => setDays(Number(e.target.value))} className="w-40" aria-label="بازه‌ی زمانی">
          <option value={7}>۷ روز گذشته</option>
          <option value={30}>۳۰ روز گذشته</option>
          <option value={90}>۹۰ روز گذشته</option>
        </Select>
      </div>

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Kpi label="کل گفتگوها" value={formatNumber(data.totals.conversations)} hint={`${formatNumber(data.totals.turns)} پاسخ در این بازه`} />
        <Kpi
          label="نرخ حل مسئله"
          value={formatPercent(data.totals.resolution_rate)}
          hint={`${formatNumber(data.feedback.confirmed)} تأیید · ${formatNumber(data.feedback.rejected)} رد`}
        />
        <Kpi label="نرخ بهره‌گیری از کش وب" value={formatPercent(data.web.cache_hit_rate)} hint={`${formatNumber(data.web.cache_entries)} ورودی فعال در کش`} />
        <Kpi label="جستجوی وب صرفه‌جویی‌شده" value={formatNumber(data.web.searches_avoided)} hint={`${formatNumber(data.web.searches_performed)} جستجوی واقعی · ${formatNumber(data.web.answer_cache_hits)} پاسخ از کش گفتگو`} />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <ChartCard title="گفتگوهای روزانه">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data.conversations_per_day} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis dataKey="date" tickFormatter={(d: string) => formatDate(d)} tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} minTickGap={24} />
              <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} />
              <Tooltip contentStyle={TOOLTIP} itemStyle={{ color: "hsl(var(--foreground))" }} labelStyle={{ color: "hsl(var(--foreground))" }} labelFormatter={(d) => formatDate(String(d))} formatter={(v) => [formatNumber(Number(v)), "گفتگو"]} />
              <Area type="monotone" dataKey="conversations" stroke="#2563eb" fill="#2563eb33" />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="توزیع منابع پاسخ">
          {noSources ? (
            <Empty>هنوز داده‌ای ثبت نشده است.</Empty>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={sources} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="label" tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} interval={0} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} />
                <Tooltip contentStyle={TOOLTIP} itemStyle={{ color: "hsl(var(--foreground))" }} labelStyle={{ color: "hsl(var(--foreground))" }} formatter={(v) => [formatNumber(Number(v)), "پاسخ"]} />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {sources.map((s) => (
                    <Cell key={s.source} fill={SOURCE_COLOR[s.source] ?? "#64748b"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        <ChartCard title="وضعیت گفتگوها">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={statusData} dataKey="value" nameKey="name" innerRadius={55} outerRadius={90} paddingAngle={2}>
                {statusData.map((s) => (
                  <Cell key={s.key} fill={STATUS_COLOR[s.key]} />
                ))}
              </Pie>
              <Tooltip contentStyle={TOOLTIP} itemStyle={{ color: "hsl(var(--foreground))" }} labelStyle={{ color: "hsl(var(--foreground))" }} formatter={(v) => formatNumber(Number(v))} />
              <Legend wrapperStyle={{ color: "hsl(var(--foreground))" }} />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="کش وب: جستجوی انجام‌شده در برابر صرفه‌جویی‌شده">
          {data.web.searches_performed + data.web.searches_avoided === 0 ? (
            <Empty>هنوز جستجوی وبی لازم نشده است.</Empty>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={webData} dataKey="value" nameKey="name" innerRadius={55} outerRadius={90} paddingAngle={2}>
                  {webData.map((s) => (
                    <Cell key={s.name} fill={s.color} />
                  ))}
                </Pie>
                <Tooltip contentStyle={TOOLTIP} itemStyle={{ color: "hsl(var(--foreground))" }} labelStyle={{ color: "hsl(var(--foreground))" }} formatter={(v) => formatNumber(Number(v))} />
                <Legend wrapperStyle={{ color: "hsl(var(--foreground))" }} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>خطاهای تکراری پرتکرار</CardTitle>
        </CardHeader>
        <CardContent>
          {data.top_signatures.length === 0 ? (
            <Empty>هنوز خطایی ثبت نشده است.</Empty>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="text-start text-xs text-muted-foreground">
                  <tr>
                    <th className="p-2 text-start">امضای خطا (نرمال‌سازی‌شده)</th>
                    <th className="p-2 text-start">دفعات</th>
                    <th className="p-2 text-start">گفتگوها</th>
                    <th className="p-2 text-start">آخرین مشاهده</th>
                  </tr>
                </thead>
                <tbody>
                  {data.top_signatures.map((s) => (
                    <tr key={s.signature} className="border-t border-border">
                      <td className="max-w-xl p-2">
                        <code className="ltr block truncate text-xs" title={s.text}>
                          {s.text}
                        </code>
                      </td>
                      <td className="p-2 font-semibold">{formatNumber(s.occurrences)}</td>
                      <td className="p-2">{formatNumber(s.conversations)}</td>
                      <td className="p-2 text-muted-foreground">{formatDateTime(s.last_seen)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
