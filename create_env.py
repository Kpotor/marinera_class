#!/usr/bin/env python
"""
環境設定ファイルを生成するスクリプト
"""
import os
import secrets
import getpass

def generate_env_file():
    """
    .env ファイルを生成する
    """
    # 既存のファイルをチェック
    if os.path.exists('.env'):
        overwrite = input('.env ファイルが既に存在します。上書きしますか？ (y/n): ')
        if overwrite.lower() != 'y':
            print('処理をキャンセルしました。')
            return

    # シークレットキーを生成
    secret_key = secrets.token_hex(32)
    
        # データベースパス
    db_path = input('データベースのパス (デフォルト: sqlite:///marinera.db): ') or 'sqlite:///marinera.db'
    
    # 環境変数を書き込む
    with open('.env', 'w') as f:
        f.write(f'FLASK_SECRET_KEY={secret_key}\n')
        f.write(f'DATABASE_URL={db_path}\n')
        # その他の環境変数も必要に応じて追加可能
    
    print('.env ファイルを生成しました。')
    print('重要: このファイルは公開リポジトリにコミットしないでください！')

if __name__ == '__main__':
    generate_env_file()
    print('\n環境変数の設定が完了しました。')
    print('次のコマンドで管理者アカウントを作成できます:')
    print('flask create-admin <ユーザー名> <メールアドレス>')