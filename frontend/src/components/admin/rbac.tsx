"use client";

import { useQuery } from "@tanstack/react-query";
import { Check, ChevronDown, Plus, Trash2 } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input, Select } from "@/components/ui/input";
import { api } from "@/lib/api";
import type { ContainerGrant, ContainerLevel, PermissionInfo, Role } from "@/lib/types";
import { cn } from "@/lib/utils";
import { useT } from "@/lib/i18n";

export function useRoles() {
  return useQuery({ queryKey: ["admin-roles"], queryFn: () => api.get<Role[]>("/admin/roles") });
}

export function usePermissionCatalog() {
  return useQuery({ queryKey: ["admin-permissions"], queryFn: () => api.get<PermissionInfo[]>("/admin/permissions"), staleTime: Infinity });
}

/** Multi-select dropdown of roles. Roles the signed-in admin may not grant (`canGrant`) are shown disabled. */
export function RolePicker({
  roles,
  value,
  onChange,
  canGrant,
}: {
  roles: Role[];
  value: string[];
  onChange: (ids: string[]) => void;
  canGrant?: (role: Role) => boolean;
}) {
  const t = useT();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const selected = roles.filter((r) => value.includes(r.id));

  useEffect(() => {
    if (!open) return;
    const close = (e: MouseEvent) => {
      if (!ref.current?.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, [open]);

  return (
    <div
      ref={ref}
      className="relative"
      onKeyDown={(e) => {
        if (e.key === "Escape" && open) {
          e.stopPropagation();
          setOpen(false);
        }
      }}
    >
      <button
        type="button"
        aria-haspopup="listbox"
        aria-expanded={open}
        onClick={() => setOpen((o) => !o)}
        className="flex min-h-10 w-full items-center justify-between gap-2 rounded-md border border-border bg-card px-3 py-1.5 text-start text-sm"
      >
        <span className="flex flex-wrap gap-1">
          {selected.length === 0 ? <span className="text-muted-foreground">{t("انتخاب نقش‌ها…")}</span> : null}
          {selected.map((r) => (
            <span key={r.id} className="rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary" dir="auto">
              {r.name}
            </span>
          ))}
        </span>
        <ChevronDown className={cn("h-4 w-4 shrink-0 text-muted-foreground transition-transform", open && "rotate-180")} />
      </button>
      {open ? (
        <ul role="listbox" aria-multiselectable="true" className="mt-1 max-h-60 overflow-y-auto rounded-md border border-border bg-card p-1 shadow-sm">
          {roles.map((r) => {
            const checked = value.includes(r.id);
            const locked = !checked && canGrant ? !canGrant(r) : false;
            return (
              <li key={r.id} role="option" aria-selected={checked} aria-disabled={locked}>
                <button
                  type="button"
                  disabled={locked}
                  title={locked ? t("شما همه‌ی دسترسی‌های این نقش را ندارید") : undefined}
                  onClick={() => onChange(checked ? value.filter((id) => id !== r.id) : [...value, r.id])}
                  className="flex w-full items-start gap-2 rounded px-2 py-1.5 text-start text-sm hover:bg-muted disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <span className={cn("mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded border border-border", checked && "border-primary bg-primary text-primary-foreground")}>
                    {checked ? <Check className="h-3 w-3" /> : null}
                  </span>
                  <span className="min-w-0">
                    <span className="font-medium" dir="auto">{r.name}</span>
                    {r.description ? <span className="block text-xs text-muted-foreground" dir="auto">{r.description}</span> : null}
                  </span>
                </button>
              </li>
            );
          })}
        </ul>
      ) : null}
    </div>
  );
}

/** Permissions grouped by area, each with a checkbox. */
export function PermissionGrid({
  catalog,
  value,
  onChange,
  disabled,
  canGrant,
}: {
  catalog: PermissionInfo[];
  value: string[];
  onChange: (keys: string[]) => void;
  disabled?: boolean;
  canGrant?: (key: string) => boolean; // permissions the editor does not hold themselves cannot be added
}) {
  const groups = [...new Set(catalog.map((p) => p.group))];
  return (
    <div className="space-y-4">
      {groups.map((g) => (
        <fieldset key={g} className="space-y-1.5">
          <legend className="mb-1 text-xs font-semibold text-muted-foreground">{g}</legend>
          {catalog
            .filter((p) => p.group === g)
            .map((p) => {
              const checked = value.includes(p.key);
              const off = disabled || (!checked && canGrant ? !canGrant(p.key) : false);
              return (
                <label key={p.key} className={cn("flex items-start gap-2 text-sm", off ? "cursor-not-allowed opacity-60" : "cursor-pointer")}>
                  <input
                    type="checkbox"
                    className="mt-1"
                    checked={checked}
                    disabled={off}
                    onChange={() => onChange(checked ? value.filter((k) => k !== p.key) : [...value, p.key])}
                  />
                  <span>
                    {p.label}
                    <code className="ms-2 text-[11px] text-muted-foreground" dir="ltr">{p.key}</code>
                  </span>
                </label>
              );
            })}
        </fieldset>
      ))}
    </div>
  );
}

/**
 * Per-container access for a role: one dropdown per known container (none / logs / logs + actions), plus free rows for
 * patterns such as `api-*` or containers that are not running right now.
 */
export function ContainerGrantEditor({
  known,
  value,
  onChange,
  disabled,
}: {
  known: string[];
  value: ContainerGrant[];
  onChange: (grants: ContainerGrant[]) => void;
  disabled?: boolean;
}) {
  const t = useT();
  const levelOf = (name: string): ContainerLevel | "" => value.find((g) => g.container === name)?.level ?? "";
  const setKnown = (name: string, level: ContainerLevel | "") =>
    onChange(level ? [...value.filter((g) => g.container !== name), { container: name, level }] : value.filter((g) => g.container !== name));
  const extra = value.filter((g) => !known.includes(g.container));
  const setExtra = (i: number, patch: Partial<ContainerGrant>) => {
    const target = extra[i]!;
    onChange(value.map((g) => (g === target ? { ...g, ...patch } : g)));
  };

  return (
    <div className="space-y-2">
      {known.map((name) => (
        <div key={name} className="flex items-center justify-between gap-2">
          <code className="min-w-0 truncate text-sm" dir="ltr">{name}</code>
          <Select value={levelOf(name)} disabled={disabled} aria-label={`${t("دسترسی به")} ${name}`} className="w-40" onChange={(e) => setKnown(name, e.target.value as ContainerLevel | "")}>
            <option value="">{t("بدون دسترسی")}</option>
            <option value="logs">{t("فقط لاگ")}</option>
            <option value="actions">{t("لاگ و عملیات")}</option>
          </Select>
        </div>
      ))}
      {extra.map((g, i) => (
        <div key={i} className="flex items-center gap-2">
          <Input dir="ltr" value={g.container} disabled={disabled} placeholder={t("الگو، مثلاً api-*")} aria-label={t("الگوی کانتینر")} onChange={(e) => setExtra(i, { container: e.target.value })} />
          <Select value={g.level} disabled={disabled} aria-label={t("سطح دسترسی")} className="w-40" onChange={(e) => setExtra(i, { level: e.target.value as ContainerLevel })}>
            <option value="logs">{t("فقط لاگ")}</option>
            <option value="actions">{t("لاگ و عملیات")}</option>
          </Select>
          <Button type="button" size="icon" variant="ghost" aria-label={t("حذف")} disabled={disabled} onClick={() => onChange(value.filter((x) => x !== g))}>
            <Trash2 className="h-4 w-4 text-danger" />
          </Button>
        </div>
      ))}
      {!disabled ? (
        <Button type="button" size="sm" variant="outline" onClick={() => onChange([...value, { container: "", level: "logs" }])}>
          <Plus className="h-4 w-4" /> {t("افزودن الگو / کانتینر")}
        </Button>
      ) : null}
    </div>
  );
}
