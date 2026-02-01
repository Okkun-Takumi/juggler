import json
import sys
from pathlib import Path

# ファイルパス
json_file = Path(__file__).parent / "setting_data.json"

try:
    # JSONファイルを読み込み
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("✓ JSON読み込み成功\n")
    
    # トップレベルのキーを確認
    print(f"トップレベルキー: {list(data.keys())}")
    print(f"機種数: {len(data['machines'])}\n")
    
    # 各機種のデータを表示
    for i, machine in enumerate(data['machines'], start=1):
        print(f"[{i}] {machine['Name']}")
        print(f"    設定数: {len(machine['SettingData'])}")
        
        # 各設定の詳細を表示
        for setting in machine['SettingData']:
            setting_num = setting['setting']
            big = setting['BIG']
            reg = setting['REG']
            print(f"      設定{setting_num}: BIG={big}, REG={reg}")
        print()
    
    # 統計情報
    print("=" * 50)
    print("統計情報:")
    print(f"総機種数: {len(data['machines'])}")
    print(f"各機種の設定数: {[len(m['SettingData']) for m in data['machines']]}")
    
    # サンプル: 最初の機種の最初の設定にアクセス
    first_machine = data['machines'][0]
    first_setting = first_machine['SettingData'][0]
    print(f"\nサンプル（最初の機種の最初の設定）:")
    print(f"  機種名: {first_machine['Name']}")
    print(f"  設定: {first_setting['setting']}, BIG: {first_setting['BIG']}, REG: {first_setting['REG']}")
    
except FileNotFoundError:
    print(f"❌ エラー: ファイルが見つかりません: {json_file}")
    sys.exit(1)
except json.JSONDecodeError as e:
    print(f"❌ エラー: JSONの解析に失敗しました")
    print(f"詳細: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ エラー: 予期しないエラーが発生しました")
    print(f"詳細: {e}")
    sys.exit(1)
