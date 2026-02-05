import { useRef, useEffect } from 'react';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from '@/components/ui/sheet';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ChatMessageBubble } from '@/components/chat/ChatMessageBubble';
import { ChatInput } from '@/components/chat/ChatInput';
import { useChatbot } from '@/hooks/use-chatbot';
import { Loader2 } from 'lucide-react';

interface ChatbotPanelProps {
  dashboardId: string;
  isOpen: boolean;
  onClose: () => void;
}

export function ChatbotPanel({ dashboardId, isOpen, onClose }: ChatbotPanelProps) {
  const { messages, isPending, error, sendMessage } = useChatbot(dashboardId);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (messagesEndRef.current && typeof messagesEndRef.current.scrollIntoView === 'function') {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  return (
    <Sheet
      open={isOpen}
      onOpenChange={(open) => {
        if (!open) onClose();
      }}
    >
      <SheetContent
        side="right"
        className="w-full md:max-w-md flex flex-col p-0"
        data-testid="chatbot-panel"
      >
        <SheetHeader className="px-6 pt-6 pb-2">
          <SheetTitle>AI アシスタント</SheetTitle>
          <SheetDescription className="sr-only">
            ダッシュボードのデータについてAIに質問できます
          </SheetDescription>
        </SheetHeader>

        {/* Error display */}
        {error && (
          <div className="px-6 py-2">
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          </div>
        )}

        {/* Message list */}
        <div
          data-testid="message-list"
          className="flex-1 overflow-y-auto px-6 py-4 space-y-4"
        >
          {messages.map((message, index) => (
            <ChatMessageBubble key={index} message={message} />
          ))}

          {/* Loading indicator */}
          {isPending && (
            <div data-testid="loading-indicator" className="flex justify-start">
              <div className="flex items-center gap-2 rounded-lg bg-muted px-4 py-2 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                応答を生成中...
              </div>
            </div>
          )}

          {/* Scroll anchor */}
          <div ref={messagesEndRef} data-testid="scroll-anchor" />
        </div>

        {/* Chat input */}
        <div className="border-t px-6 py-4">
          <ChatInput onSend={sendMessage} isPending={isPending} />
        </div>
      </SheetContent>
    </Sheet>
  );
}
