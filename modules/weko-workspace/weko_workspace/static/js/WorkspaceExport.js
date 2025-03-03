document.addEventListener('DOMContentLoaded', function () {
  // 🔹 アイテム出力ボタンを取得
  const exportButton = document.getElementById('btn_todo1');

  // 🔹 ボタンが存在する場合、クリックイベントを設定
  if (exportButton) {
    exportButton.addEventListener('click', function () {
      showExportModal(); // モーダル表示
    });
  } else {
    console.error('アイテム出力ボタン (btn_todo1) が見つかりません。');
  }
});

// エラーメッセージを画面に表示する関数
function showErrorMessage(message) {
  console.error(message);

  // 既存のエラーメッセージを削除
  const existingError = document.getElementById("exportErrorMessage");
  if (existingError) existingError.remove();

  // エラーメッセージを作成
  const errorBox = document.createElement("div");
  errorBox.id = "exportErrorMessage";
  errorBox.innerHTML = `
      <div style="
          background: #f8d7da;
          color: #721c24;
          padding: 10px;
          border: 1px solid #f5c6cb;
          border-radius: 5px;
          margin-top: 10px;
          text-align: center;
          width: 100%;
      ">
          ${message}
      </div>
  `;

  // モーダル内に追加
  const modal = document.getElementById("exportModal");
  if (modal) {
    modal.appendChild(errorBox);
  } else {
    document.body.appendChild(errorBox);
  }
}

// モーダル (ダイアログ) を表示する関数
function showExportModal() {
  // 🔹 モーダルのHTMLを作成
  const modalHTML = `
    <div id="exportModal" class="modal" style="
        display: flex;
        flex-direction: column;
        align-items: center;
        position: fixed;
        top: 20%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: white;
        width: 400px;
        height: 300px;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0px 4px 8px rgba(0,0,0,0.15);
        z-index: 1000;
        text-align: center;
    ">
        <h2 style="font-size: 14px; margin-bottom: 10px;">以下のオプションを選択してください:</h2>
        <div style="
                width: 100%;
                background: #f8f9fa;
                padding: 15px;
                border-radius: 6px;
                border: 1px solid #ddd;
                display: flex;
                justify-content: center;
                gap: 10px;
            ">
            <button id="export_selected" class="btn btn-primary">選択アイテム出力</button>
            <button id="export_all" class="btn btn-danger">全て出力</button>
            <button id="export_cancel" class="btn btn-secondary">キャンセル</button>
        </div>
        <button id="close_modal" style="
            position: absolute;
            top: 10px;
            right: 15px;
            background: none;
            border: none;
            font-size: 18px;
            cursor: pointer;
        ">&times;</button>
    </div>
    <div id="modalBackdrop" style="
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.3);
        z-index: 999;
    "></div>
  `;

  // モーダルを `body` に追加
  document.body.insertAdjacentHTML('beforeend', modalHTML);

  // ボタンのイベントリスナーを設定
  document.getElementById('export_selected').addEventListener('click', () => handleExportButtonClick(true));
  document.getElementById('export_all').addEventListener('click', () => handleExportButtonClick(false));
  document.getElementById('export_cancel').addEventListener('click', closeModal);
  document.getElementById('close_modal').addEventListener('click', closeModal);
  document.getElementById('modalBackdrop').addEventListener('click', closeModal);
}

// モーダルを閉じる関数
function closeModal() {
  document.getElementById('exportModal')?.remove();
  document.getElementById('modalBackdrop')?.remove();
}

// TSV 出力処理
function handleExportButtonClick(selectedOnly = false) {
  console.log("handleExportButtonClick が呼ばれました。");

  const items = getItemsFromWorkspace(); // workspaceItemList からデータ取得
  let selectedIds = [];

  // 選択アイテムのみを出力する場合、チェックされたアイテムの ID を取得
  if (selectedOnly) {
    selectedIds = Array.from(document.querySelectorAll('tbody input[type="checkbox"]:checked'))
      .map(cb => cb.closest('tr').querySelector('td:nth-child(2) strong a')?.href.split('/').pop());

    // チェックボックスが1つも選択されていない場合、エラーメッセージを表示
    if (selectedIds.length === 0) {
      showErrorMessage("エラー: 選択されたアイテムがありません。チェックボックスを選択してください。");
      return;
    }
  }

  console.log("出力対象のアイテム:", items.length, "選択アイテム:", selectedIds.length);

  // アイテムが取得できなかった場合
  if (!items.length) {
    showErrorMessage("出力に失敗しました");
    return;
  }

  exportItemListToTSV(items, selectedOnly, selectedIds);
}

// アイテムデータを取得
function getItemsFromWorkspace() {
  return window.workspaceItemList || [];
}

// TSV を作成してダウンロード
function exportItemListToTSV(items, selectedOnly) {
  const timestamp = new Date().toISOString().replace(/[-T:.Z]/g, "").slice(0, 14);
  const filename = `itemlist_workspace_export_${timestamp}.tsv`;
  const headers = ["No", "title", "authorName", "doi", "publicationDate", "downloadCnt", "accessCnt"];
  const tsvRows = [headers.join('\t')];

  items.forEach((item, index) => {
    const row = headers.map(header => (item[header] !== undefined ? item[header] : "")).join('\t');
    tsvRows.push(`${index + 1}\t${row}`);
  });

  const blob = new Blob(["\ufeff" + tsvRows.join('\n')], { type: "text/tab-separated-values;charset=utf-8;" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}
