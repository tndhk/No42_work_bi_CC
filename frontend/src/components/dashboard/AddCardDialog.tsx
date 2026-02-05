import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { useCards } from '@/hooks';

interface AddCardDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSelect: (cardId: string) => void;
  existingCardIds: string[];
}

export function AddCardDialog({ open, onOpenChange, onSelect, existingCardIds }: AddCardDialogProps) {
  const { data, isLoading } = useCards({ limit: 100 });

  const availableCards = data?.data.filter(
    (card) => !existingCardIds.includes(card.card_id || card.id || '')
  ) || [];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>カードを追加</DialogTitle>
        </DialogHeader>
        {isLoading ? (
          <div className="flex justify-center py-4"><LoadingSpinner /></div>
        ) : availableCards.length === 0 ? (
          <p className="text-center text-muted-foreground py-4">
            追加可能なカードがありません
          </p>
        ) : (
          <div className="space-y-2 max-h-[400px] overflow-y-auto">
            {availableCards.map((card) => {
              const cardId = card.card_id || card.id || '';
              return (
                <Button
                  key={cardId}
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => onSelect(cardId)}
                >
                  <div className="text-left">
                    <div className="font-medium">{card.name}</div>
                    <div className="text-xs text-muted-foreground">
                      {card.dataset?.name || 'データセット未設定'}
                    </div>
                  </div>
                </Button>
              );
            })}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
