<script>
  import axios from 'axios';
  let file;
  let summary = '';
  let extractedText = '';
  let errorMessage = '';
  let notification = '';
  let isSummarizing = false;

  // APIエンドポイントを設定する変数
  const API_BASE_URL = 'http://localhost:8000';

  // ページタイトルを変更
  document.title = '論文PDF要約ツール';

  // PDFアップロード時にテキスト抽出を行う
  const extractTextFromPdf = async () => {
    if (!file) {
      errorMessage = 'ファイルを選択してください。';
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API_BASE_URL}/upload-pdf/`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      extractedText = response.data.extracted_text;
      summary = ''; // 新しいPDFがアップロードされたら要約ボックスを空にする
    } catch (error) {
      errorMessage = 'テキストの抽出に失敗しました。';
    }
  };

  const summarizeText = async () => {
    if (!extractedText || isSummarizing) {
      return;
    }

    isSummarizing = true;
    summary = '要約を生成中です...';

    try {
      const response = await axios.post(`${API_BASE_URL}/summarize-text/`, {
        text: extractedText,
        filename: file.name,
      });
      summary = response.data.summary;
    } catch (error) {
      errorMessage = '要約の生成に失敗しました。';
    } finally {
      isSummarizing = false;
    }
  };

  const handleDrop = (event) => {
    event.preventDefault();
    const files = event.dataTransfer.files;
    if (files.length > 0) {
      file = files[0];
      errorMessage = '';
      extractTextFromPdf(); // ドロップした瞬間にテキストを抽出
    }
  };

  const handleDragOver = (event) => {
    event.preventDefault();
  };

  const handleFileChange = (e) => {
    file = e.target.files[0];
    errorMessage = '';
    extractTextFromPdf(); // ファイル選択時にテキストを抽出
  };

  const copyToClipboard = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      showNotification('クリップボードにコピーしました');
    } catch (err) {
      showNotification('コピーに失敗しました');
    }
  };

  const showNotification = (message) => {
    notification = message;
    setTimeout(() => {
      notification = '';
    }, 3000); // 通知を3秒後に自動で消す
  };
</script>

<main>
  <h1>論文PDF要約ツール</h1>
  <div 
    on:drop="{handleDrop}" 
    on:dragover="{handleDragOver}"
    style="width: 100%; height: 150px; border: 2px dashed #ccc; display: flex; align-items: center; justify-content: center; margin-bottom: 1rem;">
    <p>ここにPDFをドラッグ＆ドロップしてください。</p>
  </div>
  <input type="file" on:change="{handleFileChange}" />
  {#if extractedText}
    <div style="display: flex; gap: 2rem;">
      <div style="flex: 1;">
        <h2>抽出されたテキスト:</h2>
        <textarea readonly rows="10" style="width: 100%;">{extractedText}</textarea>
        <button on:click="{() => copyToClipboard(extractedText)}">コピー</button>
        <button on:click="{summarizeText}" style="margin-top: 1rem;" disabled={isSummarizing}>要約を生成する</button>
      </div>
      <div style="flex: 1;">
        <h2>要約結果:</h2>
        <textarea readonly rows="10" style="width: 100%;">{summary}</textarea>
        <button on:click="{() => copyToClipboard(summary)}">コピー</button>
      </div>
    </div>
  {/if}
  {#if errorMessage}
    <p style="color: red;">{errorMessage}</p>
  {/if}
  {#if notification}
    <div style="position: fixed; bottom: 1rem; right: 1rem; background: #333; color: #fff; padding: 1rem; border-radius: 5px;">
      {notification}
    </div>
  {/if}
</main>