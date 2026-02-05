import { useState, useCallback, type KeyboardEvent } from 'react';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Loader2, Send } from 'lucide-react';

interface ChatInputProps {
  onSend: (message: string) => void
  isPending: boolean
}

export function ChatInput({ onSend, isPending }: ChatInputProps) {
  const [message, setMessage] = useState('');

  const handleSend = useCallback(() => {
    const trimmed = message.trim();
    if (!trimmed || isPending) return;
    onSend(trimmed);
    setMessage('');
  }, [message, isPending, onSend]);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend]
  );

  return (
    <div className="flex gap-2 items-end">
      <Textarea
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="メッセージを入力..."
        disabled={isPending}
        className="min-h-[44px] max-h-[200px] resize-none"
        rows={1}
      />
      <Button
        onClick={handleSend}
        disabled={isPending || !message.trim()}
        aria-label="送信"
        size="icon"
        className="shrink-0"
      >
        {isPending ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin" />
            <span className="sr-only">送信中...</span>
          </>
        ) : (
          <Send className="h-4 w-4" />
        )}
      </Button>
    </div>
  )
}
