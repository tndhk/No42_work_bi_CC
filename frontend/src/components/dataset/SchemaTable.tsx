import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import type { Dataset } from '@/types';

interface SchemaTableProps {
  columns: Dataset['columns'];
}

export function SchemaTable({ columns }: SchemaTableProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>スキーマ</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>カラム名</TableHead>
              <TableHead>型</TableHead>
              <TableHead>NULL許容</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {columns.map((col) => (
              <TableRow key={col.name}>
                <TableCell className="font-mono">{col.name}</TableCell>
                <TableCell>
                  <Badge variant="secondary">{col.data_type}</Badge>
                </TableCell>
                <TableCell>{col.nullable ? 'Yes' : 'No'}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
