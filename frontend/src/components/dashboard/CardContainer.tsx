import { Badge } from '@/components/ui/badge';

interface CardContainerProps {
  cardId: string;
  html: string;
  filterApplied?: boolean;
}

function getCSP(): string {
  return [
    "default-src 'none'",
    "script-src 'unsafe-inline'",
    "style-src 'unsafe-inline'",
    "img-src data: blob:",
  ].join('; ');
}

export function CardContainer({ cardId, html, filterApplied }: CardContainerProps) {
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
    <div className="relative h-full">
      {filterApplied && (
        <Badge
          variant="secondary"
          className="absolute top-1 left-1 z-10 text-[10px] px-1.5 py-0"
        >
          filtered
        </Badge>
      )}
      <iframe
        title={`card-${cardId}`}
        sandbox="allow-scripts"
        srcDoc={srcDoc}
        style={{
          width: '100%',
          height: '100%',
          border: 'none',
        }}
      />
    </div>
  );
}
