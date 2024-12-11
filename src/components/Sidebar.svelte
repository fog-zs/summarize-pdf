<script>
    import { createEventDispatcher } from 'svelte';
    export let papers = []; // 論文リストを受け取る

    const dispatch = createEventDispatcher(); // カスタムイベントを作成

    let sidebarWidth = 250; // 初期幅（ピクセル）
    let selectedPaper = null; // 選択されている論文を管理

    // ドラッグ操作中かどうかを管理
    let isResizing = false;

    // ドラッグ開始時の処理
    function startResizing(event) {
        isResizing = true;
        const initialX = event.clientX;
        const initialWidth = sidebarWidth;

        function resize(event) {
            if (isResizing) {
                const deltaX = event.clientX - initialX;
                sidebarWidth = Math.max(150, initialWidth + deltaX); // 最小幅150pxに制限
            }
        }

        function stopResizing() {
            isResizing = false;
            window.removeEventListener('mousemove', resize);
            window.removeEventListener('mouseup', stopResizing);
        }

        window.addEventListener('mousemove', resize);
        window.addEventListener('mouseup', stopResizing);
    }

    const selectPaper = (paper) => {
        selectedPaper = paper; // 選択状態を更新
        dispatch('select', { paper });
    }
</script>

<style>
    .sidebar {
        height: 100vh;
        background-color: #f4f4f4;
        border-right: 1px solid #ccc;
        padding: 16px;
        overflow-y: auto;
        display: flex;
        flex-direction: column;
    }

    .title {
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 16px;
    }

    .list {
        list-style: none;
        padding: 0;
    }

    .list-item {
        margin: 8px 0;
        padding: 8px;
        border-radius: 4px;
        background: #eaeaea;
        cursor: pointer;
    }

    .list-item:hover {
        background: #ddd;
    }

    .list-item.selected {
        background: #007BFF; /* 選択状態の背景色 */
        color: white;       /* 選択状態の文字色 */
        font-weight: bold;  /* 選択状態の強調 */
    }

    .resizer {
        width: 8px;
        height: 100%;
        position: absolute;
        right: 0;
        top: 0;
        z-index: 10;
    }
</style>

<div class="sidebar" style="width: {sidebarWidth}px; position: relative;" on:mousedown={startResizing}>
    <ul class="list">
        {#each papers as paper, index}
            <li
                class="list-item {selectedPaper === paper ? 'selected' : ''}"
                on:click={() => selectPaper(paper)}
            >
                {paper.title}
            </li>
        {/each}
    </ul>
</div>
