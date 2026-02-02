import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import type { S3ImportRequest } from '@/types';

const s3ImportSchema = z.object({
  name: z.string().min(1, 'データセット名は必須です'),
  s3_bucket: z.string().min(1, 'S3バケット名は必須です'),
  s3_key: z.string().min(1, 'S3キーは必須です'),
  delimiter: z.string().optional(),
  encoding: z.string().optional(),
  has_header: z.boolean().optional(),
  partition_column: z.string().optional(),
});

type S3ImportFormData = z.infer<typeof s3ImportSchema>;

interface S3ImportFormProps {
  onSubmit: (data: S3ImportRequest) => void | Promise<void>;
  isLoading?: boolean;
}

export function S3ImportForm({ onSubmit, isLoading = false }: S3ImportFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<S3ImportFormData>({
    resolver: zodResolver(s3ImportSchema),
    defaultValues: {
      delimiter: ',',
      encoding: '',
      has_header: true,
    },
  });

  const onFormSubmit = (data: S3ImportFormData) => {
    const request: S3ImportRequest = {
      name: data.name,
      s3_bucket: data.s3_bucket,
      s3_key: data.s3_key,
    };

    if (data.delimiter && data.delimiter !== ',') {
      request.delimiter = data.delimiter;
    }
    if (data.encoding) {
      request.encoding = data.encoding;
    }
    if (data.has_header !== undefined) {
      request.has_header = data.has_header;
    }
    if (data.partition_column) {
      request.partition_column = data.partition_column;
    }

    onSubmit(request);
  };

  return (
    <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="name">データセット名</Label>
        <Input
          id="name"
          {...register('name')}
          placeholder="データセット名を入力"
        />
        {errors.name && (
          <p className="text-sm text-destructive">{errors.name.message}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="s3_bucket">S3バケット</Label>
        <Input
          id="s3_bucket"
          {...register('s3_bucket')}
          placeholder="バケット名を入力"
        />
        {errors.s3_bucket && (
          <p className="text-sm text-destructive">{errors.s3_bucket.message}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="s3_key">S3キー</Label>
        <Input
          id="s3_key"
          {...register('s3_key')}
          placeholder="パス/ファイル名.csv"
        />
        {errors.s3_key && (
          <p className="text-sm text-destructive">{errors.s3_key.message}</p>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="delimiter">区切り文字</Label>
          <Input
            id="delimiter"
            {...register('delimiter')}
            placeholder=","
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="encoding">エンコーディング</Label>
          <Input
            id="encoding"
            {...register('encoding')}
            placeholder="utf-8"
          />
        </div>
      </div>

      <Button type="submit" disabled={isLoading}>
        {isLoading ? 'インポート中...' : 'インポート'}
      </Button>
    </form>
  );
}
