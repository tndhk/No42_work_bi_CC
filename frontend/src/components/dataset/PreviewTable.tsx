import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';

interface PreviewTableProps {
  preview: {
    columns: string[];
    rows: unknown[][];
    total_rows: number;
    preview_rows: number;
  } | null;
  isLoading: boolean;
  maxRows?: number;
}

export function PreviewTable({ preview, isLoading, maxRows = 20 }: PreviewTableProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>プレビュー</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex justify-center py-4"><LoadingSpinner /></div>
        ) : preview ? (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  {preview.columns.map((col) => (
                    <TableHead key={col}>{col}</TableHead>
                  ))}
                </TableHeader>
              </TableHeader>
              <TableBody>
                {preview.rows.slice(0, maxRows).map((row, i) => (
                  <TableRow key={i}>
                    {row.map((cell, j) => (
                      <TableCell key={j} className="font-mono text-sm">
                        {cell === null ? (
                          <span className="text-muted-foreground">NULL</span>
                        ) : (
                          String(cell)
                        )}
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            <p className="text-sm text-muted-foreground mt-2">
              {preview.total_rows.toLocaleString()}件中 {Math.min(maxRows, preview.preview_rows)}件を表示
            </p>
          </div>
        ) : (
          <p className="text-muted-foreground">プレビューデータがありません</p>
        )}
      </CardContent>
    </Card>
  );
}
