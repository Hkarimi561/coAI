"use client";

import { useQueryClient } from "@tanstack/react-query";
import { Terminal } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ErrorBanner, Spinner } from "@/components/ui/misc";
import { api } from "@/lib/api";
import type { User } from "@/lib/types";

export default function LoginPage() {
  const router = useRouter();
  const qc = useQueryClient();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const user = await api.post<User>("/auth/login", { email, password });
      qc.setQueryData(["me"], user);
      router.replace("/chat");
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center p-4">
      <Card className="w-full max-w-sm">
        <CardContent className="space-y-5 p-6">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-primary p-2 text-primary-foreground">
              <Terminal className="h-5 w-5" />
            </div>
            <div>
              <h1 className="text-lg font-bold">دستیار هوشمند DevOps</h1>
              <p className="text-xs text-muted-foreground">ورود به سامانه‌ی داخلی</p>
            </div>
          </div>
          <form onSubmit={submit} className="space-y-3">
            <label className="block space-y-1 text-sm">
              <span>ایمیل</span>
              <Input type="email" dir="ltr" autoComplete="username" required value={email} onChange={(e) => setEmail(e.target.value)} />
            </label>
            <label className="block space-y-1 text-sm">
              <span>رمز عبور</span>
              <Input type="password" dir="ltr" autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} />
            </label>
            <ErrorBanner error={error} />
            <Button type="submit" className="w-full" disabled={busy}>
              {busy ? <Spinner /> : null} ورود
            </Button>
          </form>
        </CardContent>
      </Card>
    </main>
  );
}
