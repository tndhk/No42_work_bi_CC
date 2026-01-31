import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { CardContainer } from '@/components/dashboard/CardContainer';

interface CardPreviewProps {
  html: string;
  isLoading: boolean;
}

export function CardPreview({ html, isLoading }: CardPreviewProps) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center" style={{ height: 400 }}>
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (!html) {
    return (
      <div className="flex items-center justify-center text-muted-foreground" style={{ height: 400 }}>
        プレビューを実行してください
      </div>
    );
  }

  return (
    <div style={{ height: 400 }}>
      <CardContainer cardId="preview" html={html} />
    </div>
  );
}
