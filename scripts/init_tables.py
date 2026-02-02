#!/usr/bin/env python3
"""DynamoDB テーブル初期化スクリプト (MVP版)"""
import boto3
import os
import time

DYNAMODB_ENDPOINT = os.environ.get('DYNAMODB_ENDPOINT', 'http://localhost:8000')
AWS_REGION = os.environ.get('AWS_REGION', 'ap-northeast-1')

dynamodb = boto3.resource(
    'dynamodb',
    endpoint_url=DYNAMODB_ENDPOINT,
    region_name=AWS_REGION,
    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID', 'dummy'),
    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY', 'dummy'),
)

# MVP用テーブル定義 (4テーブルのみ)
TABLES = [
    {
        'TableName': 'bi_users',
        'KeySchema': [{'AttributeName': 'userId', 'KeyType': 'HASH'}],
        'AttributeDefinitions': [
            {'AttributeName': 'userId', 'AttributeType': 'S'},
            {'AttributeName': 'email', 'AttributeType': 'S'},
        ],
        'GlobalSecondaryIndexes': [
            {
                'IndexName': 'UsersByEmail',
                'KeySchema': [{'AttributeName': 'email', 'KeyType': 'HASH'}],
                'Projection': {'ProjectionType': 'ALL'},
            },
        ],
    },
    {
        'TableName': 'bi_datasets',
        'KeySchema': [{'AttributeName': 'datasetId', 'KeyType': 'HASH'}],
        'AttributeDefinitions': [
            {'AttributeName': 'datasetId', 'AttributeType': 'S'},
            {'AttributeName': 'ownerId', 'AttributeType': 'S'},
            {'AttributeName': 'createdAt', 'AttributeType': 'N'},
        ],
        'GlobalSecondaryIndexes': [
            {
                'IndexName': 'DatasetsByOwner',
                'KeySchema': [
                    {'AttributeName': 'ownerId', 'KeyType': 'HASH'},
                    {'AttributeName': 'createdAt', 'KeyType': 'RANGE'},
                ],
                'Projection': {'ProjectionType': 'ALL'},
            },
        ],
    },
    {
        'TableName': 'bi_cards',
        'KeySchema': [{'AttributeName': 'cardId', 'KeyType': 'HASH'}],
        'AttributeDefinitions': [
            {'AttributeName': 'cardId', 'AttributeType': 'S'},
            {'AttributeName': 'ownerId', 'AttributeType': 'S'},
            {'AttributeName': 'createdAt', 'AttributeType': 'N'},
        ],
        'GlobalSecondaryIndexes': [
            {
                'IndexName': 'CardsByOwner',
                'KeySchema': [
                    {'AttributeName': 'ownerId', 'KeyType': 'HASH'},
                    {'AttributeName': 'createdAt', 'KeyType': 'RANGE'},
                ],
                'Projection': {'ProjectionType': 'ALL'},
            },
        ],
    },
    {
        'TableName': 'bi_dashboards',
        'KeySchema': [{'AttributeName': 'dashboardId', 'KeyType': 'HASH'}],
        'AttributeDefinitions': [
            {'AttributeName': 'dashboardId', 'AttributeType': 'S'},
            {'AttributeName': 'ownerId', 'AttributeType': 'S'},
            {'AttributeName': 'createdAt', 'AttributeType': 'N'},
        ],
        'GlobalSecondaryIndexes': [
            {
                'IndexName': 'DashboardsByOwner',
                'KeySchema': [
                    {'AttributeName': 'ownerId', 'KeyType': 'HASH'},
                    {'AttributeName': 'createdAt', 'KeyType': 'RANGE'},
                ],
                'Projection': {'ProjectionType': 'ALL'},
            },
        ],
    },
    {
        'TableName': 'bi_filter_views',
        'KeySchema': [{'AttributeName': 'filterViewId', 'KeyType': 'HASH'}],
        'AttributeDefinitions': [
            {'AttributeName': 'filterViewId', 'AttributeType': 'S'},
            {'AttributeName': 'dashboardId', 'AttributeType': 'S'},
            {'AttributeName': 'createdAt', 'AttributeType': 'N'},
        ],
        'GlobalSecondaryIndexes': [
            {
                'IndexName': 'FilterViewsByDashboard',
                'KeySchema': [
                    {'AttributeName': 'dashboardId', 'KeyType': 'HASH'},
                    {'AttributeName': 'createdAt', 'KeyType': 'RANGE'},
                ],
                'Projection': {'ProjectionType': 'ALL'},
            },
        ],
    },
]

def create_tables():
    """テーブルを作成"""
    # DynamoDBが起動するまで待機
    max_retries = 30
    for i in range(max_retries):
        try:
            list(dynamodb.tables.all())
            print("DynamoDB接続成功")
            break
        except Exception as e:
            if i == max_retries - 1:
                raise
            print(f"DynamoDB接続待機中... ({i+1}/{max_retries})")
            time.sleep(2)

    existing_tables = [t.name for t in dynamodb.tables.all()]

    for table_def in TABLES:
        table_name = table_def['TableName']

        if table_name in existing_tables:
            print(f"テーブル {table_name} は既に存在します。スキップします。")
            continue

        # BillingMode を追加
        create_params = {
            **table_def,
            'BillingMode': 'PAY_PER_REQUEST',
        }

        print(f"テーブル {table_name} を作成中...")
        dynamodb.create_table(**create_params)
        print(f"テーブル {table_name} を作成しました。")

if __name__ == '__main__':
    try:
        create_tables()
        print("\n全てのテーブル作成が完了しました。")
    except Exception as e:
        print(f"\nエラー: {e}")
        exit(1)
