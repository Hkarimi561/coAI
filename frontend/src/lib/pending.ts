// Hand-off of the first message from /chat (no conversation yet) to /chat/[id] after the conversation was created.
let pending: { id: string; content: string } | null = null;

export const setPendingMessage = (id: string, content: string): void => {
  pending = { id, content };
};

export const takePendingMessage = (id: string): string | null => {
  if (pending && pending.id === id) {
    const { content } = pending;
    pending = null;
    return content;
  }
  return null;
};
