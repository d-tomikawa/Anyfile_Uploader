from __future__ import annotations # eraff,lvaa

import logging
import io
import pandas as pd

from flask import Flask, request, abort, jsonify, render_template
from google.cloud import storage

app = Flask(__name__)

# 変数定義
FILE_DEFINITION = 'DXD001_file_definition.xlsx'  # ファイル名定義マスタ
BUCKET_NAME = 'ragapp_master'  # ファイル名定義マスタのバケット

# ファイル名の採番取得
def file_numbers(storage_client, file_def):
    # ファイル名の次の採番を取得
    for i in range(1, len(file_def)):  # ファイル名定義マスタの2行目以降
        bucket_name = file_def[i][2]  # ファイル名定義マスタ3列目のバケット名を取得
        bucket = storage_client.bucket(bucket_name)
        blobs = bucket.list_blobs()

        numbers = []
        for blob in blobs:
            if blob.name[3:6].isdigit():  # ファイル名の4〜6文字目が数字かどうかを確認
                numbers.append(int(blob.name[3:6]))  # 数字の場合はint型に変換してリストに追加

        # リストが空の場合、次の採番を1とする
        if numbers:
            next_number = max(numbers) + 1  # 次の採番を算出
        else:
            next_number = 1  # 初めてのファイルの場合は1から始める

        if len(file_def[i]) < 4:  # 次の採番が空欄の場合
            file_def[i].append("")  # 採番セルに空の要素を追加
        file_def[i][3] = str(next_number)  # 採番セルに次の採番を入力


# 次の採番を更新したファイル名定義マスタをGCSに戻す
def upload_xlsx(blob, file_def):
    output = io.BytesIO()       # バイナリデータとしてファイル定義書を処理するためのもの
    
    # file_defからデータフレームを再構築
    df = pd.DataFrame(file_def[1:], columns=file_def[0])  # 1行目を列名として扱い、2行目以降をdfに格納
    # Excelファイルに書き込めるようにするオブジェクト作成
    # engineを使ってxlsxを読み書きし。outputにそのファイルを出力させ
    with pd.ExcelWriter(output, engine='openpyxl') as writer:  
        df.to_excel(writer, index=False)
    blob.upload_from_string(output.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

# webページを読み込む
@app.route("/")
def index() -> str:
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(FILE_DEFINITION)

    # GCSからマスタをダウンロード
    content = blob.download_as_bytes()  # Excelファイルをバイナリデータとして取得
    file_def = pd.read_excel(io.BytesIO(content), header=None).values.tolist()  # データフレームとして読み込みリストに変換

    file_numbers(storage_client, file_def)

    upload_xlsx(blob, file_def)  

    # ファイル名定義マスタをアプリ画面で表として表示
    return render_template("index.html", headers=file_def[0], data=file_def[1:])


# ファイルアップロード処理
@app.route("/upload", methods=["POST"])
def upload() -> str:
    # 複数アップロードされたファイルを取得
    uploaded_files = request.files.getlist("files[]")

    # ファイルが選択されていない場合、エラーメッセージを返す
    if not uploaded_files or all(file.filename == "" for file in uploaded_files):
        abort(400, "No data")

    # GCSからファイル名定義書を取得
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(FILE_DEFINITION)
    content = blob.download_as_bytes()
    file_def = pd.read_excel(io.BytesIO(content)).values.tolist()

    # GCSにアップロード
    for file in uploaded_files:
        matched = False  # ファイル名が定義書にない場合のフラグ

        for row in file_def:
            if row[0] in file.filename:  # ファイル名が定義書に含まれているか
                cloud_storage_bucket = row[2]  # ファイル定義のバケット名を取得

                # GCSバケットにファイルをアップロード
                bucket = storage_client.bucket(cloud_storage_bucket)
                blob_list = bucket.list_blobs()
                for j in blob_list:
                    if file.filename[0:6] == j.name[0:6]:
                        print(file.filename[0:6])
                        return f"""ファイル名の先頭6桁が重複しています。<br>ファイル名：{file.filename}
                        <br>
                        <button onclick="window.history.back();">戻る</button>
                        """

                blob = bucket.blob(file.filename)
                file.stream.seek(0)  # ストリームの先頭に戻す
                blob.upload_from_file(file)

                matched = True  # ファイル名が一致したフラグをセット
                break

        # ファイル名が定義書に一致しなかった場合のエラーメッセージ
        if not matched:
            return f"""
            <h3>ファイル名がファイル定義と一致しません。ファイル名: {file.filename}</h3>
            <button onclick="window.history.back();">戻る</button>
            """

    # アップロード完了メッセージ
    return """
    <h2>Successfully Uploaded</h2>
    <button onclick="window.history.back();">戻る</button>
    """


@app.route('/admin')
def admin_page():
    return render_template('管理者ページ.html')

# GCSからExcelファイルを読み込んでフロントエンドに送信
@app.route('/admin/load_excel', methods=['GET'])
def load_excel():
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(FILE_DEFINITION)
    
    content = blob.download_as_bytes()  # GCSからExcelファイルをダウンロード
    df = pd.read_excel(io.BytesIO(content))  # PandasでExcelファイルを読み込む

    # DataFrameをJSON形式に変換してフロントエンドに送信
    return jsonify({
        'data': df.values.tolist(),
        'columns': df.columns.tolist()
    })

# 管理者ページのマスタ編集
@app.route('/admin/save_excel', methods=['POST'])
def save_excel():
    data = request.json
    df = pd.DataFrame(data['data'], columns=data['columns'])  # JSONからPandas DataFrameを作成

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)  # DataFrameをExcelファイルに書き込み

    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(FILE_DEFINITION)
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
