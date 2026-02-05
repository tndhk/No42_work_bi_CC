import { cn } from '@/lib/utils';
import type { ChatMessage } from '@/types';

interface ChatMessageBubbleProps {
  message: ChatMessage;
}

export function ChatMessageBubble({ message }: ChatMessageBubbleProps) {
  const isUser = message.role === 'user';

  return (
    <div
      data-testid="chat-message-bubble"
      className={cn('flex w-full', isUser ? 'justify-end' : 'justify-start')}
    >
      <div
        data-testid="chat-bubble"
        role="log"
        className={cn(
          'rounded-lg px-4 py-2 max-w-[80%] whitespace-pre-wrap break-words',
          isUser
            ? 'bg-primary text-primary-foreground'
            : 'bg-muted text-foreground'
        )}
      >
        {message.content}
      </div>
    </div>
  );
}
