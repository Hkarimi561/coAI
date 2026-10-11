import { ChatView } from "@/components/chat/chat-view";

export default function ChatPage({ params }: { params: { id: string } }) {
  return <ChatView key={params.id} conversationId={params.id} />;
}
