document.addEventListener('DOMContentLoaded', () => {
    let hot; // hotという変数の定義

    // 表を描画する
    function initializeHandsontable(data, columns) {  //関数定義。pythonでいうdef関数
        const container = document.getElementById('spreadsheet');  //今開いているhtmlから'spreadsheet'を探し、その画面に表示させる
        hot = new Handsontable(container, {  //下記条件で表を生成して画面に描画
            data: data || [],  //dataが渡されていればその値を使用、空や未定義の場合は空セルにする
            colHeaders: columns || [],  //ヘッダーの設定で上記と同様
            rowHeaders: true,  //行番号表示
            minSpareRows: 1,  //表の下に常に1行の空行を表示
            contextMenu: true,  //セルを右クリックした際に表示されるコンテキストメニュー（コピー、ペースト、削除など）を有効化
            licenseKey: 'non-commercial-and-evaluation'  //Handsontableを動作させるための無償ライセンスキーを設定
        });
    }

    // サーバーからデータを取得して表示
    function loadExcelData() {  //関数定義
        fetch('/admin/load_excel')  //サーバー上の/admin/load_excelエンドポイントにHTTPリクエストを送信
            .then(response => {  //python側からreturnで帰ってきたjsonデータを確認し、次の.thenに渡す
                if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
                return response.json();
            })
            //python側からreturnで帰ってきたjsonデータがdataに入る。
            //initializeHandsontable関数を呼び出し、jsonデータを渡した実行結果をdataに入れる
            .then(data => initializeHandsontable(data.data, data.columns))
            .catch(error => console.error('Error loading data:', error));  //エラーハンドリング
    }

    // 変更した表を保存する
    function saveExcelData() {  //関数定義
        const updatedData = {  //updatedDataという変数に下記データを格納
            data: hot.getData(),  //現在表示されている表データを取得
            columns: hot.getColHeader()  //現在表示されているヘッダーを取得
        };

        fetch('/admin/save_excel', {  //サーバーの/admin/save_excelエンドポイントにデータを送信
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updatedData)  //現在の表データが格納されたupdatedDataをjson形式にする
        })
        .then(response => {  //上記jsonデータを確認し、バックエンドに渡す
            if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
            return response.json();
        })
        .then(result => alert(result.message))
        .catch(error => {
            console.error('Error saving data:', error);
            alert('データの保存に失敗しました。');
        });
    }

    // 最初に実行される
    loadExcelData();

    // id="saveButton"を持つボタンをクリックしたときに、saveExcelDataという関数を実行する
    document.getElementById('saveButton').addEventListener('click', saveExcelData);
});
