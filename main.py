from __future__ import annotations

import logging
import io
import pandas as pd

from flask import Flask, request, jsonify, render_template
from google.cloud import storage

app = Flask(__name__)

# 変数定義
FILE_NAME = 'Shipping_schedule_富川ver.xlsx'  # ファイル名
BUCKET_NAME = 'room_shipping_schedule'  # ファイルがあるバケット名


@app.route('/')
def main_page():
    return render_template('oil_table.html')

# シッピングスケジュール読み込み
@app.route('/admin/load_excel', methods=['GET'])
def load_excel():
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(FILE_NAME)
    
    content = blob.download_as_bytes()  # GCSからExcelファイルをダウンロード
    df = pd.read_excel(io.BytesIO(content))  # Excelファイルをデータフレームに格納（デフォルトで1行目がヘッダーとして読み込まれる）

    # データフレームにNaNがある場合、空の文字列を入力
    # NaNは数値型の空欄であり、エラーになりやすい。文字列型の空欄にすればエラーを回避しやすい。
    df = df.where(df.notnull(), "")  

    df.drop(df.index[[0, 1, 2, 3, 4]])

    # DataFrameをJSON形式に変換してフロントエンドに送信
    return jsonify({
        'data': df.values.tolist(),  # dfを配列として取得し、リストに変換する
        'columns': df.columns.tolist()  # dfのヘッダーをリストに変換する
    })



# 変更された表の保存
@app.route('/admin/save_excel', methods=['POST'])
def save_excel():
    data = request.json  # フロントエンドから渡された、現在の表データを変数dataに格納
    df = pd.DataFrame(data['data'], columns=data['columns'])  # フロントエンドから渡されたデータ部分と列名をdfに格納

    output = io.BytesIO() # 空の仮想ファイル作成
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)  # DataFrameをExcelファイルに書き込み
        df = df.where(df.notnull(), "")  # dfにNaNがあったら、空欄文字列に置換

    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(FILE_NAME)
    blob.upload_from_string(output.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')  # GCSにアップロード

    return jsonify({'message': 'ファイルが正常に保存されました'})



@app.errorhandler(500)
def server_error(e: Exception) -> str:
    logging.exception("An error occurred during a request.")
    return f"""
    An internal error occurred: <pre>{e}</pre>
    See logs for full stacktrace.
    """, 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
