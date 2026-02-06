import { Badge } from '@/components/ui/badge';
import { MoreVertical } from 'lucide-react';
import DOMPurify from 'dompurify';

interface CardContainerProps {
  cardId: string;
  html: string;
  filterApplied?: boolean;
  cardName?: string;
  cardType?: 'code' | 'text';
  params?: Record<string, unknown>;
}

function getCSP(): string {
  return [
    "default-src 'none'",
    "script-src 'unsafe-inline'",
    "style-src 'unsafe-inline'",
    "img-src data: blob:",
  ].join('; ');
}

export function CardContainer({ 
  cardId, 
  html, 
  filterApplied, 
  cardName,
  cardType = 'code',
  params 
}: CardContainerProps) {
  const isTextCard = cardType === 'text';
  
  // For text cards, sanitize HTML and render directly
  const sanitizedHtml = isTextCard ? DOMPurify.sanitize(html) : html;
  
  // Get background color from params for text cards
  const backgroundColor = isTextCard && params?.background_color 
    ? String(params.background_color) 
    : undefined;

  const srcDoc = `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <meta http-equiv="Content-Security-Policy" content="${getCSP()}">
      <style>
        body { margin: 0; padding: 8px; font-family: sans-serif; overflow: auto; }
      </style>
    </head>
    <body>
      ${html}
    </body>
    </html>
  `;

  return (
    <div className="flex flex-col h-full">
      {!isTextCard && (
        <div className="flex items-center justify-between px-4 py-2 border-b bg-muted/30">
          <h3 className="text-sm font-medium text-foreground truncate">
            {cardName || `Card ${cardId.slice(0, 8)}`}
          </h3>
          <div className="flex items-center gap-2">
            {filterApplied && (
              <Badge
                variant="secondary"
                className="text-[10px] px-1.5 py-0"
              >
                filtered
              </Badge>
            )}
            <button
              className="p-1 rounded hover:bg-background transition-colors"
              title="オプション"
              aria-label="カードオプション"
            >
              <MoreVertical className="h-4 w-4 text-muted-foreground" />
            </button>
          </div>
        </div>
      )}
      <div 
        className={isTextCard ? "flex-1 relative overflow-auto p-6" : "flex-1 relative overflow-hidden"}
        style={backgroundColor ? { backgroundColor } : undefined}
      >
        {isTextCard ? (
          <div 
            className="h-full text-white prose prose-invert max-w-none"
            dangerouslySetInnerHTML={{ __html: sanitizedHtml }}
          />
        ) : (
          <iframe
            title={`card-${cardId}`}
            sandbox="allow-scripts"
            srcDoc={srcDoc}
            className="w-full h-full border-none"
          />
        )}
      </div>
    </div>
  );
}
