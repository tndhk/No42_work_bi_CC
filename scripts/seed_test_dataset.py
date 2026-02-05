#!/usr/bin/env python3
"""サンプルデータセットをDynamoDB LocalとMinIOに挿入するスクリプト"""
import boto3
import os
import time
import io

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# DynamoDB Local エンドポイント
DYNAMODB_ENDPOINT = os.environ.get('DYNAMODB_ENDPOINT', 'http://localhost:8001')
AWS_REGION = os.environ.get('AWS_REGION', 'ap-northeast-1')

# MinIO (S3互換) エンドポイント
S3_ENDPOINT = os.environ.get('S3_ENDPOINT', 'http://localhost:9000')
S3_ACCESS_KEY = os.environ.get('S3_ACCESS_KEY', 'minioadmin')
S3_SECRET_KEY = os.environ.get('S3_SECRET_KEY', 'minioadmin')
S3_BUCKET = os.environ.get('S3_BUCKET_DATASETS', 'bi-datasets')

# データセット情報
DATASET_ID = 'ds_seed_sales_001'
DATASET_NAME = 'Sample Sales Data'
DATASET_DESCRIPTION = 'Seeded sample dataset for development'
OWNER_ID = 'e2e-test-user-001'
S3_PATH = f'datasets/{DATASET_ID}/data.parquet'

# サンプルCSVデータ
SAMPLE_CSV_DATA = """date,product,amount,quantity
2024-01-01,Widget A,1000,10
2024-01-02,Widget B,1500,15
2024-01-03,Widget A,2000,20
2024-01-04,Widget C,2500,25
2024-01-05,Widget B,3000,30"""


def wait_for_dynamodb(dynamodb, max_retries: int = 30):
    """DynamoDBが起動するまで待機"""
    print("DynamoDB Local への接続を確認中...")
    for i in range(max_retries):
        try:
            list(dynamodb.tables.all())
            print("DynamoDB接続成功")
            return True
        except Exception as e:
            if i == max_retries - 1:
                print(f"エラー: DynamoDB Localに接続できませんでした。")
                raise
            print(f"DynamoDB接続待機中... ({i+1}/{max_retries})")
            time.sleep(2)
    return False


def wait_for_minio(s3_client, bucket: str, max_retries: int = 30):
    """MinIOが起動し、バケットが存在するまで待機"""
    print("MinIO への接続を確認中...")
    for i in range(max_retries):
        try:
            s3_client.head_bucket(Bucket=bucket)
            print(f"MinIO接続成功（バケット: {bucket}）")
            return True
        except Exception as e:
            if i == max_retries - 1:
                print(f"エラー: MinIOに接続できませんでした。バケット: {bucket}")
                raise
            print(f"MinIO接続待機中... ({i+1}/{max_retries})")
            time.sleep(2)
    return False


def check_dataset_exists(table, dataset_id: str) -> bool:
    """データセットが既に存在するか確認"""
    try:
        response = table.get_item(Key={'datasetId': dataset_id})
        return 'Item' in response
    except Exception as e:
        print(f"警告: データセット存在チェック中にエラー: {e}")
        return False


def check_s3_object_exists(s3_client, bucket: str, key: str) -> bool:
    """S3オブジェクトが既に存在するか確認"""
    try:
        s3_client.head_object(Bucket=bucket, Key=key)
        return True
    except Exception:
        return False


def create_parquet_from_csv(csv_data: str) -> bytes:
    """CSVデータからParquetバイト列を生成"""
    df = pd.read_csv(io.StringIO(csv_data))
    
    # 明示的な型変換
    df['date'] = df['date'].astype(str)
    df['product'] = df['product'].astype(str)
    df['amount'] = df['amount'].astype('int64')
    df['quantity'] = df['quantity'].astype('int64')
    
    # Parquetに変換
    table = pa.Table.from_pandas(df)
    buffer = io.BytesIO()
    pq.write_table(table, buffer)
    return buffer.getvalue()


def get_schema_info(csv_data: str) -> list:
    """CSVデータからスキーマ情報を取得（ColumnSchemaと互換形式）"""
    df = pd.read_csv(io.StringIO(csv_data))
    schema = []
    for col in df.columns:
        if col in ['date', 'product']:
            col_type = 'string'
        else:
            col_type = 'int64'
        schema.append({
            'name': col,
            'data_type': col_type,
            'nullable': False,
            'description': None,
        })
    return schema


def seed_test_dataset():
    """サンプルデータセットをMinIOとDynamoDB Localに挿入"""
    # DynamoDB リソース接続
    dynamodb = boto3.resource(
        'dynamodb',
        endpoint_url=DYNAMODB_ENDPOINT,
        region_name=AWS_REGION,
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID', 'dummy'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY', 'dummy'),
    )

    # S3 クライアント接続
    s3_client = boto3.client(
        's3',
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY,
        region_name=AWS_REGION,
    )

    # 接続待機
    wait_for_dynamodb(dynamodb)
    wait_for_minio(s3_client, S3_BUCKET)

    # テーブル取得
    table = dynamodb.Table('bi_datasets')

    # 冪等性チェック: データセットが既に存在する場合はスキップ
    if check_dataset_exists(table, DATASET_ID):
        print(f"データセット ({DATASET_ID}) は既に存在します。スキップします。")
        return

    # S3にParquetファイルが既に存在する場合もスキップ
    if check_s3_object_exists(s3_client, S3_BUCKET, S3_PATH):
        print(f"S3オブジェクト ({S3_PATH}) は既に存在します。メタデータのみ確認します。")
    else:
        # CSVをParquetに変換
        print("CSVデータをParquetに変換中...")
        parquet_data = create_parquet_from_csv(SAMPLE_CSV_DATA)

        # MinIOにアップロード
        print(f"MinIOにアップロード中... (s3://{S3_BUCKET}/{S3_PATH})")
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=S3_PATH,
            Body=parquet_data,
            ContentType='application/octet-stream'
        )
        print("アップロード完了")

    # スキーマ情報を取得
    schema = get_schema_info(SAMPLE_CSV_DATA)

    # 現在時刻 (UNIX timestamp)
    current_timestamp = int(time.time())

    # データセットメタデータを作成
    dataset_item = {
        'datasetId': DATASET_ID,
        'name': DATASET_NAME,
        'description': DATASET_DESCRIPTION,
        'ownerId': OWNER_ID,
        'sourceType': 'csv',
        'rowCount': 5,
        'columnCount': 4,
        's3Path': S3_PATH,
        'schema': schema,
        'createdAt': current_timestamp,
        'updatedAt': current_timestamp,
    }

    # DynamoDBに挿入
    try:
        table.put_item(Item=dataset_item)
        print(f"✅ サンプルデータセットを作成しました:")
        print(f"   Dataset ID: {DATASET_ID}")
        print(f"   Name: {DATASET_NAME}")
        print(f"   Owner: {OWNER_ID}")
        print(f"   S3 Path: s3://{S3_BUCKET}/{S3_PATH}")
        print(f"   Row Count: 5")
        print(f"   Column Count: 4")
    except Exception as e:
        print(f"❌ エラー: データセットメタデータの作成に失敗しました: {e}")
        raise


if __name__ == '__main__':
    try:
        seed_test_dataset()
        print("\nサンプルデータセットのSeedが完了しました。")
    except Exception as e:
        print(f"\nエラー: {e}")
        exit(1)
