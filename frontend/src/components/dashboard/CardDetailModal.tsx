import { useState } from 'react';
import { X } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { CardContainer } from './CardContainer';
import { useCardData } from '@/hooks/use-cards';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { cn } from '@/lib/utils';

interface CardDetailModalProps {
  cardId: string;
  cardName: string;
  html: string;
  cardType?: 'code' | 'text';
  params?: Record<string, unknown>;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

type TabType = 'chart' | 'data';

export function CardDetailModal({
  cardId,
  cardName,
  html,
  cardType,
  params,
  open,
  onOpenChange,
}: CardDetailModalProps) {
  const [activeTab, setActiveTab] = useState<TabType>('chart');
  const { data: cardData, isLoading: isLoadingData } = useCardData(cardId, 1000);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-[90vw] max-h-[90vh] w-full h-full flex flex-col p-0">
        <DialogHeader className="px-6 py-4 border-b">
          <div className="flex items-center justify-between">
            <DialogTitle className="text-xl">{cardName}</DialogTitle>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => onOpenChange(false)}
              className="h-8 w-8"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </DialogHeader>

        {/* Tabs */}
        <div className="flex border-b px-6">
          <button
            type="button"
            onClick={() => setActiveTab('chart')}
            className={cn(
              'px-4 py-3 text-sm font-medium border-b-2 transition-colors',
              activeTab === 'chart'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground',
            )}
          >
            チャート
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('data')}
            className={cn(
              'px-4 py-3 text-sm font-medium border-b-2 transition-colors',
              activeTab === 'data'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground',
            )}
          >
            データ
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-6">
          {activeTab === 'chart' ? (
            <div className="h-full min-h-[600px]">
              <CardContainer
                cardId={cardId}
                html={html}
                cardName={cardName}
                cardType={cardType}
                params={params}
              />
            </div>
          ) : (
            <div className="space-y-4">
              {isLoadingData ? (
                <div className="flex justify-center py-12">
                  <LoadingSpinner size="lg" />
                </div>
              ) : cardData ? (
                <>
                  <div className="text-sm text-muted-foreground">
                    {cardData.total_rows.toLocaleString()} 行中 {cardData.returned_rows.toLocaleString()} 行を表示
                    {cardData.truncated && ' (切り詰められています)'}
                  </div>
                  <div className="border rounded-lg overflow-auto">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          {cardData.columns.map((col) => (
                            <TableHead key={col}>{col}</TableHead>
                          ))}
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {cardData.rows.length === 0 ? (
                          <TableRow>
                            <TableCell colSpan={cardData.columns.length} className="text-center text-muted-foreground">
                              データがありません
                            </TableCell>
                          </TableRow>
                        ) : (
                          cardData.rows.map((row, idx) => (
                            <TableRow key={idx}>
                              {cardData.columns.map((col) => (
                                <TableCell key={col}>
                                  {row[col] != null ? String(row[col]) : '-'}
                                </TableCell>
                              ))}
                            </TableRow>
                          ))
                        )}
                      </TableBody>
                    </Table>
                  </div>
                </>
              ) : (
                <div className="text-center text-muted-foreground py-12">
                  データを読み込めませんでした
                </div>
              )}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
