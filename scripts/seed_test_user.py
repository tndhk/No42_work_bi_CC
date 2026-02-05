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

# 管理者テストユーザ情報
ADMIN_USER_ID = 'admin-test-user-001'
ADMIN_USER_EMAIL = 'admin@example.com'
ADMIN_USER_PASSWORD = 'Admin@1234'

# 共有テスト用ユーザ情報
VIEWER_USER_ID = 'e2e-viewer-user-001'
VIEWER_USER_EMAIL = 'e2e-viewer@example.com'
VIEWER_USER_PASSWORD = 'Test@1234'

EDITOR_USER_ID = 'e2e-editor-user-001'
EDITOR_USER_EMAIL = 'e2e-editor@example.com'
EDITOR_USER_PASSWORD = 'Test@1234'

MEMBER_USER_ID = 'e2e-member-user-001'
MEMBER_USER_EMAIL = 'e2e-member@example.com'
MEMBER_USER_PASSWORD = 'Test@1234'

# Bcrypt rounds (backend/app/core/security.py と同じ)
BCRYPT_ROUNDS = 12


def hash_password(password: str) -> str:
    """bcryptでパスワードをハッシュ化 (12 rounds)"""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    hashed_bytes = bcrypt.hashpw(password_bytes, salt)
    return hashed_bytes.decode('utf-8')


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

    # 1. 通常のテストユーザを作成
    try:
        response = table.get_item(Key={'userId': TEST_USER_ID})
        if 'Item' in response:
            print(f"テストユーザ ({TEST_USER_EMAIL}) は既に存在します。スキップします。")
        else:
            hashed_password = hash_password(TEST_USER_PASSWORD)
            user_item = {
                'userId': TEST_USER_ID,
                'email': TEST_USER_EMAIL,
                'hashedPassword': hashed_password,
                'createdAt': current_timestamp,
                'updatedAt': current_timestamp,
            }
            table.put_item(Item=user_item)
            print(f"✅ テストユーザを作成しました:")
            print(f"   User ID: {TEST_USER_ID}")
            print(f"   Email: {TEST_USER_EMAIL}")
            print(f"   Password: {TEST_USER_PASSWORD}")
    except Exception as e:
        print(f"警告: テストユーザ作成中にエラー: {e}")
        # 続行してみる

    # 2. 管理者ユーザを作成
    try:
        response = table.get_item(Key={'userId': ADMIN_USER_ID})
        if 'Item' in response:
            print(f"管理者ユーザ ({ADMIN_USER_EMAIL}) は既に存在します。スキップします。")
        else:
            admin_hashed_password = hash_password(ADMIN_USER_PASSWORD)
            admin_user_item = {
                'userId': ADMIN_USER_ID,
                'email': ADMIN_USER_EMAIL,
                'hashedPassword': admin_hashed_password,
                'role': 'admin',  # 管理者ロールを設定
                'createdAt': current_timestamp,
                'updatedAt': current_timestamp,
            }
            table.put_item(Item=admin_user_item)
            print(f"✅ 管理者ユーザを作成しました:")
            print(f"   User ID: {ADMIN_USER_ID}")
            print(f"   Email: {ADMIN_USER_EMAIL}")
            print(f"   Password: {ADMIN_USER_PASSWORD}")
            print(f"   Role: admin")
    except Exception as e:
        print(f"❌ エラー: 管理者ユーザの作成に失敗しました: {e}")
        raise

    # 3. Viewerユーザを作成
    try:
        response = table.get_item(Key={'userId': VIEWER_USER_ID})
        if 'Item' in response:
            print(f"Viewerユーザ ({VIEWER_USER_EMAIL}) は既に存在します。スキップします。")
        else:
            viewer_hashed_password = hash_password(VIEWER_USER_PASSWORD)
            viewer_user_item = {
                'userId': VIEWER_USER_ID,
                'email': VIEWER_USER_EMAIL,
                'hashedPassword': viewer_hashed_password,
                'role': 'member',
                'createdAt': current_timestamp,
                'updatedAt': current_timestamp,
            }
            table.put_item(Item=viewer_user_item)
            print(f"✅ Viewerユーザを作成しました:")
            print(f"   User ID: {VIEWER_USER_ID}")
            print(f"   Email: {VIEWER_USER_EMAIL}")
            print(f"   Password: {VIEWER_USER_PASSWORD}")
    except Exception as e:
        print(f"警告: Viewerユーザ作成中にエラー: {e}")

    # 4. Editorユーザを作成
    try:
        response = table.get_item(Key={'userId': EDITOR_USER_ID})
        if 'Item' in response:
            print(f"Editorユーザ ({EDITOR_USER_EMAIL}) は既に存在します。スキップします。")
        else:
            editor_hashed_password = hash_password(EDITOR_USER_PASSWORD)
            editor_user_item = {
                'userId': EDITOR_USER_ID,
                'email': EDITOR_USER_EMAIL,
                'hashedPassword': editor_hashed_password,
                'role': 'member',
                'createdAt': current_timestamp,
                'updatedAt': current_timestamp,
            }
            table.put_item(Item=editor_user_item)
            print(f"✅ Editorユーザを作成しました:")
            print(f"   User ID: {EDITOR_USER_ID}")
            print(f"   Email: {EDITOR_USER_EMAIL}")
            print(f"   Password: {EDITOR_USER_PASSWORD}")
    except Exception as e:
        print(f"警告: Editorユーザ作成中にエラー: {e}")

    # 5. Memberユーザを作成
    try:
        response = table.get_item(Key={'userId': MEMBER_USER_ID})
        if 'Item' in response:
            print(f"Memberユーザ ({MEMBER_USER_EMAIL}) は既に存在します。スキップします。")
        else:
            member_hashed_password = hash_password(MEMBER_USER_PASSWORD)
            member_user_item = {
                'userId': MEMBER_USER_ID,
                'email': MEMBER_USER_EMAIL,
                'hashedPassword': member_hashed_password,
                'role': 'member',
                'createdAt': current_timestamp,
                'updatedAt': current_timestamp,
            }
            table.put_item(Item=member_user_item)
            print(f"✅ Memberユーザを作成しました:")
            print(f"   User ID: {MEMBER_USER_ID}")
            print(f"   Email: {MEMBER_USER_EMAIL}")
            print(f"   Password: {MEMBER_USER_PASSWORD}")
    except Exception as e:
        print(f"警告: Memberユーザ作成中にエラー: {e}")


if __name__ == '__main__':
    try:
        seed_test_user()
        print("\nテストユーザのSeedが完了しました。")
        print("作成されたユーザ:")
        print(f"  - E2Eテストユーザ: {TEST_USER_EMAIL}")
        print(f"  - 管理者ユーザ: {ADMIN_USER_EMAIL}")
        print(f"  - Viewerユーザ: {VIEWER_USER_EMAIL}")
        print(f"  - Editorユーザ: {EDITOR_USER_EMAIL}")
        print(f"  - Memberユーザ: {MEMBER_USER_EMAIL}")
    except Exception as e:
        print(f"\nエラー: {e}")
        exit(1)
