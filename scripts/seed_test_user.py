#!/usr/bin/env python3
"""E2Eテスト用ユーザをDynamoDB Localに挿入するスクリプト"""
import boto3
import bcrypt
import os
import time

# DynamoDB Local エンドポイント (docker-compose の 8001:8000 マッピングを使用)
DYNAMODB_ENDPOINT = os.environ.get('DYNAMODB_ENDPOINT', 'http://localhost:8001')
AWS_REGION = os.environ.get('AWS_REGION', 'ap-northeast-1')

# テストユーザ情報
TEST_USER_ID = 'e2e-test-user-001'
TEST_USER_EMAIL = 'e2e@example.com'
TEST_USER_PASSWORD = 'Test@1234'

# Bcrypt rounds (backend/app/core/security.py と同じ)
BCRYPT_ROUNDS = 12


def hash_password(password: str) -> str:
    """bcryptでパスワードをハッシュ化 (12 rounds)"""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    hashed_bytes = bcrypt.hashpw(password_bytes, salt)
    return hashed_bytes.decode('utf-8')


def seed_test_user():
    """テストユーザをDynamoDB Localに挿入"""
    # DynamoDB リソース接続
    dynamodb = boto3.resource(
        'dynamodb',
        endpoint_url=DYNAMODB_ENDPOINT,
        region_name=AWS_REGION,
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID', 'dummy'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY', 'dummy'),
    )

    # DynamoDBが起動するまで待機
    print("DynamoDB Local への接続を確認中...")
    max_retries = 30
    for i in range(max_retries):
        try:
            list(dynamodb.tables.all())
            print("DynamoDB接続成功")
            break
        except Exception as e:
            if i == max_retries - 1:
                print(f"エラー: DynamoDB Localに接続できませんでした。docker-compose upを実行してください。")
                raise
            print(f"DynamoDB接続待機中... ({i+1}/{max_retries})")
            time.sleep(2)

    # テーブル取得
    table = dynamodb.Table('bi_users')

    # ユーザが既に存在するか確認 (冪等性)
    try:
        response = table.get_item(Key={'userId': TEST_USER_ID})
        if 'Item' in response:
            print(f"テストユーザ ({TEST_USER_EMAIL}) は既に存在します。スキップします。")
            return
    except Exception as e:
        print(f"警告: ユーザ存在チェック中にエラー: {e}")
        # テーブルが存在しない場合など、続行してみる

    # パスワードをハッシュ化
    hashed_password = hash_password(TEST_USER_PASSWORD)

    # 現在時刻 (UNIX timestamp)
    current_timestamp = int(time.time())

    # ユーザアイテムを作成
    user_item = {
        'userId': TEST_USER_ID,
        'email': TEST_USER_EMAIL,
        'hashedPassword': hashed_password,
        'createdAt': current_timestamp,
        'updatedAt': current_timestamp,
    }

    # DynamoDBに挿入
    try:
        table.put_item(Item=user_item)
        print(f"✅ テストユーザを作成しました:")
        print(f"   User ID: {TEST_USER_ID}")
        print(f"   Email: {TEST_USER_EMAIL}")
        print(f"   Password: {TEST_USER_PASSWORD}")
        print(f"   Hashed Password: {hashed_password[:50]}...")
    except Exception as e:
        print(f"❌ エラー: テストユーザの作成に失敗しました: {e}")
        raise


if __name__ == '__main__':
    try:
        seed_test_user()
        print("\nテストユーザのSeedが完了しました。")
    except Exception as e:
        print(f"\nエラー: {e}")
        exit(1)
