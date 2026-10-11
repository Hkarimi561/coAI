export interface User {
  id: string;
  email: string;
  name: string;
  role: "admin" | "user";
  is_active: boolean;
  created_at?: string;
}

export type ConversationStatus = "unresolved" | "pending_review" | "resolved";
export type Phase = "idle" | "awaiting_feedback" | "awaiting_error";

export interface Conversation {
  id: string;
  title: string;
  status: ConversationStatus;
  phase: Phase;
  created_at: string;
  updated_at: string;
}

export type CitationKind = "doc" | "solution" | "web" | "docker" | "ci";

export interface Citation {
  n: number;
  kind: CitationKind;
  title: string;
  location: string | null;
  url: string | null;
  path: string | null;
  snippet: string;
  score: number | null;
  origin: "cache" | "fresh" | null;
  cited: boolean;
}

export interface MessageMeta {
  awaiting_feedback?: boolean;
  feedback?: "confirmed" | "rejected";
  primary_source?: string;
  web_event?: string;
  kind?: string;
  notes?: string[];
  thinking?: string;
  answer_cache?: "hit";
  refreshed?: boolean;
  llm_error?: string;
  [key: string]: unknown;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations: Citation[];
  meta: MessageMeta;
  created_at: string;
}

export interface MemoryTurn {
  n: number;
  user: string;
  assistant: string;
  source: string;
  outcome: "pending" | "confirmed" | "rejected" | "info";
}

export interface Memory {
  problem: string;
  summary?: string;
  next_step: string;
  timeline: MemoryTurn[];
  updating?: boolean;
}

export interface ConversationDetail {
  conversation: Conversation;
  messages: Message[];
  memory?: Memory | null;
}

export interface AdminConversationRow extends Conversation {
  user: { id: string; email: string; name: string };
  message_count: number;
}

export interface Paged<T> {
  total: number;
  page: number;
  page_size: number;
  items: T[];
}

export interface ToolCallRow {
  id: string;
  message_id: string | null;
  tool: string;
  input: Record<string, unknown>;
  output: Record<string, unknown>;
  status: "ok" | "error" | "skipped";
  duration_ms: number;
  created_at: string;
}

export interface FeedbackRow {
  id: string;
  message_id: string;
  solution_id: string | null;
  outcome: "confirmed" | "rejected";
  note: string;
  created_at: string;
}

export interface SolutionRow {
  id: string;
  title: string;
  status: "candidate" | "promoted" | "rejected";
  problem: string;
  content: string;
  document_id: string | null;
  created_at: string;
}

export interface TurnRow {
  message_id: string | null;
  primary_source: string;
  sources: string[];
  web_event: string;
  error_signature: string | null;
  signature_text: string | null;
  created_at: string;
}

export interface ConversationInspection {
  conversation: Conversation;
  user: { id: string; email: string; name: string };
  messages: Message[];
  tool_calls: ToolCallRow[];
  feedback: FeedbackRow[];
  solutions: SolutionRow[];
  turns: TurnRow[];
}

export interface DraftResponse {
  title: string;
  markdown: string;
  suggested_path: string;
  solution_id: string | null;
  generated_by_llm: boolean;
}

export interface DocumentRow {
  id: string;
  path: string;
  title: string;
  source: string;
  chunk_count: number;
  size_bytes: number;
  status: "indexed" | "error";
  error: string | null;
  indexed_at: string | null;
  updated_at: string;
}

export interface DocumentFull extends DocumentRow {
  content: string;
}

export interface ReindexReport {
  indexed: string[];
  skipped: number;
  removed: string[];
  errors: { path: string; error: string }[];
}

export interface CacheRow {
  id: string;
  cache_key: string;
  query_text: string;
  error_signature: string;
  provider: string;
  result_count: number;
  hit_count: number;
  has_answer: boolean;
  created_at: string;
  expires_at: string;
  invalidated_at: string | null;
}

export interface CacheDetail extends Omit<CacheRow, "result_count" | "has_answer"> {
  results: { title: string; url: string; snippet: string }[];
  answer: string | null;
}

export type ComponentKey = "llm" | "embeddings" | "qdrant" | "postgres" | "redis" | "web_search" | "docker" | "ci";

export interface SystemStatus {
  /** ok: true = healthy, false = failing, null = loading / disabled / not configured */
  components: Record<ComponentKey, { ok: boolean | null; detail: string }>;
  assistant_ready: boolean;
  documents?: Record<string, number>;
}

export interface Analytics {
  days: number;
  totals: { conversations: number; answered_conversations: number; resolved: number; resolution_rate: number; turns: number };
  by_status: Record<ConversationStatus, number>;
  feedback: { confirmed: number; rejected: number };
  sources: { source: string; count: number }[];
  web: {
    searches_performed: number;
    searches_avoided: number;
    cache_hit_rate: number;
    failed: number;
    cache_entries: number;
    cache_hits_total: number;
    answer_cache_hits: number;
  };
  conversations_per_day: { date: string; conversations: number }[];
  top_signatures: { signature: string; text: string; occurrences: number; conversations: number; last_seen: string }[];
}
