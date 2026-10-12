"use client";

import { ChevronDown, ChevronLeft, FileText, Folder, FolderOpen, Pencil, RefreshCw, Trash2 } from "lucide-react";
import { useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/misc";
import type { DocumentRow } from "@/lib/types";
import { formatDateTime, formatNumber } from "@/lib/utils";

interface FolderNode {
  name: string;
  path: string;
  folders: FolderNode[];
  files: DocumentRow[];
}

function buildTree(docs: DocumentRow[]): FolderNode {
  const root: FolderNode = { name: "", path: "", folders: [], files: [] };
  for (const d of docs) {
    const parts = d.path.split("/");
    let node = root;
    for (const name of parts.slice(0, -1)) {
      const path = node.path ? `${node.path}/${name}` : name;
      let next = node.folders.find((f) => f.name === name);
      if (!next) {
        next = { name, path, folders: [], files: [] };
        node.folders.push(next);
      }
      node = next;
    }
    node.files.push(d);
  }
  const sort = (n: FolderNode) => {
    n.folders.sort((a, b) => a.name.localeCompare(b.name));
    n.files.sort((a, b) => a.path.localeCompare(b.path));
    n.folders.forEach(sort);
  };
  sort(root);
  return root;
}

function countErrors(n: FolderNode): number {
  return n.files.filter((d) => d.status !== "indexed").length + n.folders.reduce((s, f) => s + countErrors(f), 0);
}

function countFiles(n: FolderNode): number {
  return n.files.length + n.folders.reduce((s, f) => s + countFiles(f), 0);
}

interface Props {
  docs: DocumentRow[];
  onEdit: (d: DocumentRow) => void;
  onDelete: (d: DocumentRow) => void;
  onReindex: (d: DocumentRow) => void;
  /** id of the document being re-indexed right now */
  reindexingId?: string | null;
  /** path of the document the indexer is working on right now */
  currentPath?: string | null;
}

export function DocTree({ docs, onEdit, onDelete, onReindex, reindexingId, currentPath }: Props) {
  const tree = useMemo(() => buildTree(docs), [docs]);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const toggle = (path: string) =>
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(path)) next.delete(path);
      else next.add(path);
      return next;
    });

  return (
    <div className="rounded-lg border border-border bg-card p-2 text-sm">
      <Folder_ node={tree} depth={0} expanded={expanded} toggle={toggle} onEdit={onEdit} onDelete={onDelete} onReindex={onReindex} reindexingId={reindexingId} currentPath={currentPath} />
    </div>
  );
}

interface NodeProps extends Pick<Props, "onEdit" | "onDelete" | "onReindex" | "reindexingId" | "currentPath"> {
  node: FolderNode;
  depth: number;
  expanded: Set<string>;
  toggle: (path: string) => void;
}

function Folder_({ node, depth, expanded, toggle, onEdit, onDelete, onReindex, reindexingId, currentPath }: NodeProps) {
  const isRoot = depth === 0;
  const isOpen = isRoot || expanded.has(node.path);
  const errors = countErrors(node);
  const hasCurrent = !!currentPath && currentPath.startsWith(`${node.path}/`);
  return (
    <div>
      {!isRoot ? (
        <button
          type="button"
          onClick={() => toggle(node.path)}
          className="flex w-full items-center gap-1.5 rounded-md px-2 py-1.5 text-start hover:bg-muted"
          style={{ paddingInlineStart: `${depth * 18 - 10}px` }}
          aria-expanded={isOpen}
        >
          {isOpen ? <ChevronDown className="h-4 w-4 shrink-0" /> : <ChevronLeft className="h-4 w-4 shrink-0" />}
          {isOpen ? <FolderOpen className="h-4 w-4 shrink-0 text-warning" /> : <Folder className="h-4 w-4 shrink-0 text-warning" />}
          <span className="ltr font-medium">{node.name}</span>
          <span className="text-xs text-muted-foreground">({formatNumber(countFiles(node))})</span>
          {hasCurrent ? <Spinner /> : null}
          {errors > 0 ? <Badge tone="danger">{formatNumber(errors)} خطا</Badge> : null}
        </button>
      ) : null}
      {isOpen ? (
        <div className={isRoot ? "" : "border-s border-border"} style={isRoot ? undefined : { marginInlineStart: `${depth * 18 - 2}px` }}>
          {node.folders.map((f) => (
            <Folder_ key={f.path} node={f} depth={depth + 1} expanded={expanded} toggle={toggle} onEdit={onEdit} onDelete={onDelete} onReindex={onReindex} reindexingId={reindexingId} currentPath={currentPath} />
          ))}
          {node.files.map((d) => (
            <FileRow key={d.id} d={d} depth={depth} onEdit={onEdit} onDelete={onDelete} onReindex={onReindex} busy={reindexingId === d.id} current={currentPath === d.path} />
          ))}
        </div>
      ) : null}
    </div>
  );
}

function FileRow({ d, depth, onEdit, onDelete, onReindex, busy, current }: { d: DocumentRow; depth: number; busy: boolean; current: boolean } & Pick<Props, "onEdit" | "onDelete" | "onReindex">) {
  const name = d.path.split("/").pop() ?? d.path;
  return (
    <div
      className="group flex flex-wrap items-center gap-x-3 gap-y-1 rounded-md px-2 py-1.5 hover:bg-muted"
      style={{ paddingInlineStart: depth === 0 ? undefined : "10px" }}
    >
      <FileText className="h-4 w-4 shrink-0 text-muted-foreground" />
      <div className="min-w-0 flex-1">
        <div className="truncate font-medium" dir="auto" title={d.title}>
          {d.title}
        </div>
        <code className="ltr text-xs text-muted-foreground">{name}</code>
      </div>
      <Badge tone={d.source === "promoted" ? "success" : "neutral"}>{d.source}</Badge>
      <span className="text-xs text-muted-foreground">{formatNumber(d.chunk_count)} chunk</span>
      {current ? (
        <Badge tone="info">
          <Spinner /> در حال ایندکس
        </Badge>
      ) : d.status === "indexed" ? (
        <Badge tone="success">ایندکس</Badge>
      ) : (
        <span className="group/err relative">
          <span tabIndex={0} className="cursor-help outline-none">
            <Badge tone="danger">خطا در ایندکس</Badge>
          </span>
          <span
            role="tooltip"
            className="ltr pointer-events-none invisible absolute end-0 top-full z-20 mt-1 w-80 max-w-[85vw] whitespace-pre-wrap break-words rounded-md border border-danger/40 bg-card p-2 text-left text-[11px] text-danger opacity-0 shadow-lg transition-opacity group-hover/err:visible group-hover/err:opacity-100 group-focus-within/err:visible group-focus-within/err:opacity-100"
          >
            {d.error || "Unknown indexing error"}
          </span>
        </span>
      )}
      <span className="hidden text-xs text-muted-foreground md:inline">{formatDateTime(d.indexed_at)}</span>
      <div className="flex gap-1">
        <Button size="icon" variant="ghost" aria-label="ایندکس مجدد" title="ایندکس مجدد این سند" disabled={busy} onClick={() => onReindex(d)}>
          {busy ? <Spinner /> : <RefreshCw className="h-4 w-4" />}
        </Button>
        <Button size="icon" variant="ghost" aria-label="ویرایش" onClick={() => onEdit(d)}>
          <Pencil className="h-4 w-4" />
        </Button>
        <Button size="icon" variant="ghost" aria-label="حذف" onClick={() => onDelete(d)}>
          <Trash2 className="h-4 w-4 text-danger" />
        </Button>
      </div>
    </div>
  );
}
