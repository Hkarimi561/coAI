import { ChatView } from "@/components/chat/chat-view";

export default function NewChatPage({ searchParams }: { searchParams: { teach?: string } }) {
  const mode = searchParams.teach ? "teach" : "support";
  return <ChatView key={mode} conversationId={null} mode={mode} />;
}
