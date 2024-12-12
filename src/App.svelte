<script>
  import axios from "axios";
  import { onMount } from "svelte";
  let file;
  let title = "";
  let tags = [];
  let summary = "";
  let extractedText = "";
  let filename = "";
  let errorMessage = "";
  let notification = "";
  let isSummarizing = false;

  const API_BASE_URL = "http://localhost:9012";

  import Sidebar from "./components/Sidebar.svelte";
  let papers = [];

  const getPapers = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/get-papers/`);
      papers = response.data.papers || [];
      console.log(papers); // デバッグ用: 論文タイトルをコンソールに表示
    } catch (error) {
      console.error("Error fetching papers:", error);
    }
  };

  // ページタイトルを変更
  document.title = "論文PDF要約ツール";

  // PDFアップロード時にテキスト抽出を行う
  const extractTextFromPdf = async () => {
    if (!file) {
      errorMessage = "ファイルを選択してください。";
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await axios.post(
        `${API_BASE_URL}/upload-pdf/`,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        },
      );
      extractedText = response.data.extracted_text;
      filename = response.data.filename;
      summary = ""; // 新しいPDFがアップロードされたら要約ボックスを空にする
    } catch (error) {
      errorMessage = "テキストの抽出に失敗しました。";
    }
  };

  const summarizeText = async () => {
    if (!extractedText || isSummarizing) {
      return;
    }

    isSummarizing = true;
    summary = "要約を生成中です...";

    try {
      const response = await axios.post(`${API_BASE_URL}/summarize-text/`, {
        text: extractedText,
        filename: filename,
      });
      const paper = response.data.paper;
      papers.push(paper);

      handleSelect({ detail: { paper } }); // サイドバーに追加された論文を選択
    } catch (error) {
      errorMessage = `要約の生成に失敗しました: ${error.message}`;
    } finally {
      isSummarizing = false;
    }
  };


  const handleDrop = (event) => {
    event.preventDefault();
    const files = event.dataTransfer.files;
    if (files.length > 0) {
      file = files[0];
      errorMessage = "";
      extractTextFromPdf(); // ドロップした瞬間にテキストを抽出
    }
  };

  const handleDragOver = (event) => {
    event.preventDefault();
  };

  const handleFileChange = (e) => {
    file = e.target.files[0];
    errorMessage = "";
    extractTextFromPdf(); // ファイル選択時にテキストを抽出
  };

  const copyToClipboard = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      showNotification("クリップボードにコピーしました");
    } catch (err) {
      showNotification("コピーに失敗しました");
    }
  };

  const showNotification = (message) => {
    notification = message;
    setTimeout(() => {
      notification = "";
    }, 3000); // 通知を3秒後に自動で消す
  };

  const getPdf = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/pdf/${selectedPaper.filename}.pdf`, {
      responseType: "blob", // バイナリデータを取得
    });

    // PDFデータをBlobオブジェクトとして扱う
    const pdfBlob = new Blob([response.data], { type: "application/pdf" });

    // Blob URLを生成
    const pdfUrl = URL.createObjectURL(pdfBlob);

    // 新しいタブでPDFを開く
    window.open(pdfUrl, "_blank");
  } catch (error) {
    console.error("Error fetching PDF:", error);
  }
};

  // 選択された論文を保持
  let selectedPaper = null;

  // サイドバーからの選択イベントを処理
  const handleSelect = (event) => {
    selectedPaper = event.detail.paper; // `dispatch` で渡されたデータを取得
    console.log("Selected paper:", selectedPaper);
    extractedText = selectedPaper.text;
    summary = selectedPaper.summary;
    title = selectedPaper.title;
    tags = selectedPaper.tags;
    console.log(tags);
    console.log(extractedText);
  };

  onMount(() => {
    getPapers();
  });
</script>

<main class="app">
  <Sidebar {papers} on:select={handleSelect} />
  <div class="content">
    {#if title}
      <div style="display: flex; align-items: center;">
        <h2 style="margin-right: 10px;">{title}</h2>
        {#if selectedPaper}
        <button on:click={() => getPdf()}>PDF</button>
        {/if}
      </div>
    {/if}
    {#if Array.isArray(tags) && tags.length > 0}
      <p>Tags: {tags.join(", ")}</p>
    {/if}
    <div
      on:drop={handleDrop}
      on:dragover={handleDragOver}
      style="width: 100%; height: 150px; border: 2px dashed #ccc; display: flex; align-items: center; justify-content: center; margin-bottom: 1rem;"
    >
      <p>ここにPDFをドラッグ＆ドロップしてください。</p>
    </div>
    <input type="file" on:change={handleFileChange} />
    {#if extractedText}
      <div style="display: flex; gap: 2rem;">
        <div style="flex: 1;">
          <h2>抽出されたテキスト:</h2>
          <textarea readonly rows="10" style="width: 100%;"
            >{extractedText}</textarea
          >
          <button on:click={() => copyToClipboard(extractedText)}>コピー</button
          >
          <button
            on:click={summarizeText}
            style="margin-top: 1rem;"
            disabled={isSummarizing}>要約を生成する</button
          >
        </div>
        <div style="flex: 1;">
          <h2>要約結果:</h2>
          <textarea readonly rows="10" style="width: 100%;">{summary}</textarea>
          <button on:click={() => copyToClipboard(summary)}>コピー</button>
        </div>
      </div>
    {/if}
    {#if errorMessage}
      <p style="color: red;">{errorMessage}</p>
    {/if}
    {#if notification}
      <div
        style="position: fixed; bottom: 1rem; right: 1rem; background: #333; color: #fff; padding: 1rem; border-radius: 5px;"
      >
        {notification}
      </div>
    {/if}        
  </div>
</main>

<style>
  .app {
    display: flex;
  }
  .content {
    flex: 1;
    padding: 16px;
  }
</style>
