"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useSystemStatus } from "@/components/system-status";
import { Card } from "@/components/ui/card";
import { ErrorBanner, Spinner } from "@/components/ui/misc";
import { Switch } from "@/components/ui/switch";
import { api } from "@/lib/api";
import { useT } from "@/lib/i18n";

interface SettingRow {
  key: string;
  label: string;
  enabled: boolean;
}

const INFO: Record<string, { title: string; text: string }> = {
  web_search_enabled: {
    title: "جستجوی زنده در وب",
    text: "اگر خاموش باشد هیچ درخواستی به موتور جستجو (SearXNG / Tavily) ارسال نمی‌شود. نتایج قبلاً ذخیره‌شده در کش همچنان استفاده می‌شوند.",
  },
  github_docs_enabled: {
    title: "مستندات پروژه‌ها در GitHub",
    text: "پروژه‌ی مرتبط (مثلاً angular) را در GitHub پیدا می‌کند و llms.txt، README و فایل‌های docs/*.md آن را می‌خواند و با لینک منبع برمی‌گرداند.",
  },
  answer_cache_enabled: {
    title: "کش پاسخ گفتگوها",
    text: "سؤال تکراری بدون جستجو و بدون فراخوانی مدل، فوراً از پاسخ قبلی جواب داده می‌شود.",
  },
};

export default function SettingsPage() {
  const t = useT();
  const qc = useQueryClient();
  const status = useSystemStatus();
  const { data, isLoading, error } = useQuery({ queryKey: ["admin-settings"], queryFn: () => api.get<{ settings: SettingRow[] }>("/admin/settings") });
  const save = useMutation({
    mutationFn: (v: Record<string, boolean>) => api.put<{ settings: SettingRow[] }>("/admin/settings", v),
    onSuccess: (res) => {
      qc.setQueryData(["admin-settings"], res);
      void qc.invalidateQueries({ queryKey: ["system-status"] });
    },
  });

  if (isLoading) return <Spinner className="mx-auto mt-10 h-6 w-6" />;
  return (
    <div className="space-y-4">
      <h1 className="text-lg font-bold">{t("تنظیمات")}</h1>
      <ErrorBanner error={error ?? save.error} />
      <Card className="divide-y divide-border">
        {data?.settings.map((s) => {
          const info = INFO[s.key];
          return (
            <div key={s.key} className="flex items-start justify-between gap-4 p-4">
              <div className="space-y-1">
                <div className="font-medium">{info ? t(info.title) : s.label}</div>
                <p className="text-sm text-muted-foreground">{info ? t(info.text) : null}</p>
                {s.key === "web_search_enabled" && status.data ? (
                  <p className="ltr text-xs text-muted-foreground">{status.data.components.web_search.detail}</p>
                ) : null}
              </div>
              <Switch checked={s.enabled} label={info ? t(info.title) : s.label} disabled={save.isPending} onChange={(v) => save.mutate({ [s.key]: v })} />
            </div>
          );
        })}
      </Card>
      <p className="text-xs text-muted-foreground">{t("تغییرها بلافاصله اعمال می‌شوند و همه‌ی پاسخ‌های ذخیره‌شده در کش گفتگو معتبرسازی مجدد می‌شوند.")}</p>
    </div>
  );
}
