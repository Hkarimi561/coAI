// Hand-off of the first message from /chat (no conversation yet) to /chat/[id] after the conversation was created.
export interface PendingMessage {
  content: string;
  imageIds: string[];
  /** local previews of the uploaded images, shown while the answer streams */
  previews: string[];
}

let pending: (PendingMessage & { id: string }) | null = null;

export const setPendingMessage = (id: string, content: string, imageIds: string[] = [], previews: string[] = []): void => {
  pending = { id, content, imageIds, previews };
};

export const takePendingMessage = (id: string): PendingMessage | null => {
  if (pending && pending.id === id) {
    const { content, imageIds, previews } = pending;
    pending = null;
    return { content, imageIds, previews };
  }
  return null;
};
