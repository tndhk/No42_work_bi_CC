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

# テーブル定義 (全11テーブル)
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
    {
        'TableName': 'bi_groups',
        'KeySchema': [{'AttributeName': 'groupId', 'KeyType': 'HASH'}],
        'AttributeDefinitions': [
            {'AttributeName': 'groupId', 'AttributeType': 'S'},
            {'AttributeName': 'name', 'AttributeType': 'S'},
        ],
        'GlobalSecondaryIndexes': [
            {
                'IndexName': 'GroupsByName',
                'KeySchema': [
                    {'AttributeName': 'name', 'KeyType': 'HASH'},
                ],
                'Projection': {'ProjectionType': 'ALL'},
            },
        ],
    },
    {
        'TableName': 'bi_group_members',
        'KeySchema': [
            {'AttributeName': 'groupId', 'KeyType': 'HASH'},
            {'AttributeName': 'userId', 'KeyType': 'RANGE'},
        ],
        'AttributeDefinitions': [
            {'AttributeName': 'groupId', 'AttributeType': 'S'},
            {'AttributeName': 'userId', 'AttributeType': 'S'},
        ],
        'GlobalSecondaryIndexes': [
            {
                'IndexName': 'MembersByUser',
                'KeySchema': [
                    {'AttributeName': 'userId', 'KeyType': 'HASH'},
                ],
                'Projection': {'ProjectionType': 'ALL'},
            },
        ],
    },
    {
        'TableName': 'bi_dashboard_shares',
        'KeySchema': [{'AttributeName': 'shareId', 'KeyType': 'HASH'}],
        'AttributeDefinitions': [
            {'AttributeName': 'shareId', 'AttributeType': 'S'},
            {'AttributeName': 'dashboardId', 'AttributeType': 'S'},
            {'AttributeName': 'sharedToId', 'AttributeType': 'S'},
        ],
        'GlobalSecondaryIndexes': [
            {
                'IndexName': 'SharesByDashboard',
                'KeySchema': [
                    {'AttributeName': 'dashboardId', 'KeyType': 'HASH'},
                ],
                'Projection': {'ProjectionType': 'ALL'},
            },
            {
                'IndexName': 'SharesByTarget',
                'KeySchema': [
                    {'AttributeName': 'sharedToId', 'KeyType': 'HASH'},
                ],
                'Projection': {'ProjectionType': 'ALL'},
            },
        ],
    },
    {
        'TableName': 'bi_transforms',
        'KeySchema': [{'AttributeName': 'transformId', 'KeyType': 'HASH'}],
        'AttributeDefinitions': [
            {'AttributeName': 'transformId', 'AttributeType': 'S'},
            {'AttributeName': 'ownerId', 'AttributeType': 'S'},
        ],
        'GlobalSecondaryIndexes': [
            {
                'IndexName': 'TransformsByOwner',
                'KeySchema': [
                    {'AttributeName': 'ownerId', 'KeyType': 'HASH'},
                ],
                'Projection': {'ProjectionType': 'ALL'},
            },
        ],
    },
    {
        'TableName': 'bi_transform_executions',
        'KeySchema': [
            {'AttributeName': 'transformId', 'KeyType': 'HASH'},
            {'AttributeName': 'startedAt', 'KeyType': 'RANGE'},
        ],
        'AttributeDefinitions': [
            {'AttributeName': 'transformId', 'AttributeType': 'S'},
            {'AttributeName': 'startedAt', 'AttributeType': 'N'},
        ],
    },
    {
        'TableName': 'bi_audit_logs',
        'KeySchema': [
            {'AttributeName': 'logId', 'KeyType': 'HASH'},
            {'AttributeName': 'timestamp', 'KeyType': 'RANGE'},
        ],
        'AttributeDefinitions': [
            {'AttributeName': 'logId', 'AttributeType': 'S'},
            {'AttributeName': 'timestamp', 'AttributeType': 'N'},
            {'AttributeName': 'userId', 'AttributeType': 'S'},
            {'AttributeName': 'targetId', 'AttributeType': 'S'},
        ],
        'GlobalSecondaryIndexes': [
            {
                'IndexName': 'LogsByUser',
                'KeySchema': [
                    {'AttributeName': 'userId', 'KeyType': 'HASH'},
                    {'AttributeName': 'timestamp', 'KeyType': 'RANGE'},
                ],
                'Projection': {'ProjectionType': 'ALL'},
            },
            {
                'IndexName': 'LogsByTarget',
                'KeySchema': [
                    {'AttributeName': 'targetId', 'KeyType': 'HASH'},
                    {'AttributeName': 'timestamp', 'KeyType': 'RANGE'},
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
