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
  mode: "support" | "teach";
  phase: Phase;
  created_at: string;
  updated_at: string;
}

export type CitationKind = "doc" | "lesson" | "solution" | "github" | "web" | "docker" | "ci";

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
  timings?: {
    total_ms: number;
    search_ms: number;
    tools_ms?: number;
    docs_ms?: number;
    cache_ms?: number;
    web_ms?: number;
    generate_ms?: number;
    prefill_ms?: number;
    thinking_ms: number;
    response_ms: number;
  };
  skills?: string[];
  mcp_calls?: { server: string | null; tool: string; ok: boolean; ms: number; args?: Record<string, unknown>; result?: string }[];
  confidence?: "verified" | "live" | "external" | "model";
  risky_commands?: { command: string; reason: string; severity: "high" | "medium" }[];
  usage?: { prompt_tokens: number; completion_tokens: number; total_tokens: number; estimated: boolean };
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
  active?: boolean;
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
  /** true while documents are being indexed - chat is disabled meanwhile */
  indexing?: boolean;
  /** context length of the loaded model, tokens */
  context_window?: number;
  index_progress?: { running: boolean; total: number; done: number; current: string | null };
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

export type LessonStatus = "pending" | "approved" | "rejected";

export interface Lesson {
  id: string;
  conversation_id: string;
  title: string;
  applies_when: string;
  instruction: string;
  status: LessonStatus;
  review_note: string;
  created_at: string;
  reviewed_at: string | null;
  user?: { id: string; email: string; name: string } | null;
}

export type ContainerLevel = "logs" | "actions";
export type ContainerAction = "start" | "stop" | "restart";

export interface ContainerInfo {
  name: string;
  image: string | null;
  state: string | null;
  status: string | null;
  level: ContainerLevel;
}

export interface ContainerPermissions {
  enabled: boolean;
  error: string | null;
  containers: { name: string; image: string | null; state: string | null }[];
  users: { id: string; email: string; name: string; role: "admin" | "user"; is_active: boolean; grants: { container: string; level: ContainerLevel }[] }[];
}

export interface ContainerAuditRow {
  id: string;
  user: { email: string; name: string };
  container: string;
  action: string;
  result: string;
  created_at: string;
}

export interface McpServerRow {
  id: string;
  name: string;
  transport: "http" | "sse";
  url: string;
  header_names: string[];
  enabled: boolean;
  tools: { name: string; description: string }[];
  enabled_tools: string[];
  last_error: string | null;
  synced_at: string | null;
}

export interface SkillRow {
  id: string;
  name: string;
  description: string;
  instructions: string;
  enabled: boolean;
  updated_at: string | null;
}

export interface GapReport {
  days: number;
  from: string;
  to: string;
  turns: number;
  gap_turns: number;
  gap_rate: number;
  previous: { turns: number; gap_turns: number; gap_rate: number };
  kinds: { no_source: number; web_fallback: number; rejected: number };
  clusters: {
    title: string;
    count: number;
    score: number;
    kinds: { no_source: number; web_fallback: number; rejected: number };
    last_seen: string;
    examples: { query: string; conversation_id: string; at: string }[];
  }[];
}
