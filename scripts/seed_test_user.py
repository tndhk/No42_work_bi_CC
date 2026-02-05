#!/usr/bin/env python3
"""E2Eテスト用ユーザをDynamoDB Localに挿入するスクリプト"""
import boto3
import bcrypt
import os
import time

# DynamoDB Local エンドポイント (docker-compose の 8001:8000 マッピングを使用)
DYNAMODB_ENDPOINT = os.environ.get('DYNAMODB_ENDPOINT', 'http://localhost:8001')
AWS_REGION = os.environ.get('AWS_REGION', 'ap-northeast-1')

# Bcrypt rounds (backend/app/core/security.py と同じ)
BCRYPT_ROUNDS = 12

# ユーザ設定リスト
# raise_on_error=True の場合、作成失敗時に例外を再送出する
# raise_on_error=False の場合、警告を出力して続行する
USER_CONFIGS = [
    {
        'userId': 'e2e-test-user-001',
        'email': 'e2e@example.com',
        'password': 'Test@1234',
        'label': 'テストユーザ',
        'raise_on_error': False,
    },
    {
        'userId': 'admin-test-user-001',
        'email': 'admin@example.com',
        'password': 'Admin@1234',
        'role': 'admin',
        'label': '管理者ユーザ',
        'raise_on_error': True,
    },
    {
        'userId': 'e2e-viewer-user-001',
        'email': 'e2e-viewer@example.com',
        'password': 'Test@1234',
        'role': 'member',
        'label': 'Viewerユーザ',
        'raise_on_error': False,
    },
    {
        'userId': 'e2e-editor-user-001',
        'email': 'e2e-editor@example.com',
        'password': 'Test@1234',
        'role': 'member',
        'label': 'Editorユーザ',
        'raise_on_error': False,
    },
    {
        'userId': 'e2e-member-user-001',
        'email': 'e2e-member@example.com',
        'password': 'Test@1234',
        'role': 'member',
        'label': 'Memberユーザ',
        'raise_on_error': False,
    },
]


def hash_password(password: str) -> str:
    """bcryptでパスワードをハッシュ化 (12 rounds)"""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    hashed_bytes = bcrypt.hashpw(password_bytes, salt)
    return hashed_bytes.decode('utf-8')


def _create_user_if_not_exists(table, user_config, current_timestamp):
    """単一ユーザの存在確認と作成を行う。

    user_config に raise_on_error=True が設定されている場合、
    作成失敗時に例外を再送出する。それ以外は警告を出力して続行する。
    """
    user_id = user_config['userId']
    email = user_config['email']
    password = user_config['password']
    label = user_config['label']
    role = user_config.get('role')
    raise_on_error = user_config.get('raise_on_error', False)

    try:
        response = table.get_item(Key={'userId': user_id})
        if 'Item' in response:
            print(f"{label} ({email}) は既に存在します。スキップします。")
        else:
            hashed_password = hash_password(password)
            user_item = {
                'userId': user_id,
                'email': email,
                'hashedPassword': hashed_password,
                'createdAt': current_timestamp,
                'updatedAt': current_timestamp,
            }
            if role:
                user_item['role'] = role
            table.put_item(Item=user_item)
            print(f"✅ {label}を作成しました:")
            print(f"   User ID: {user_id}")
            print(f"   Email: {email}")
            print(f"   Password: {password}")
            if role == 'admin':
                print(f"   Role: admin")
    except Exception as e:
        if raise_on_error:
            print(f"❌ エラー: {label}の作成に失敗しました: {e}")
            raise
        else:
            print(f"警告: {label}作成中にエラー: {e}")


def seed_test_user():
    """テストユーザと管理者ユーザをDynamoDB Localに挿入"""
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

    # 現在時刻 (UNIX timestamp)
    current_timestamp = int(time.time())

    # 全ユーザを作成
    for user_config in USER_CONFIGS:
        _create_user_if_not_exists(table, user_config, current_timestamp)


if __name__ == '__main__':
    try:
        seed_test_user()
        print("\nテストユーザのSeedが完了しました。")
        print("作成されたユーザ:")
        for user_config in USER_CONFIGS:
            label = user_config['label']
            email = user_config['email']
            print(f"  - {label}: {email}")
    except Exception as e:
        print(f"\nエラー: {e}")
        exit(1)
