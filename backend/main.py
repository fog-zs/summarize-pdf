import hashlib
from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel
from openai import OpenAI
import PyPDF2
import io
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import shutil
import json

# .envファイルを読み込む
load_dotenv()

# OpenAI APIキーを読み込む
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# OpenAIクライアントの初期化
client = OpenAI(api_key=OPENAI_API_KEY)

# FastAPI アプリケーションのインスタンスを作成
app = FastAPI()

# CORS設定を追加
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 必要に応じて特定のオリジンを許可
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# PDFを読み込み、テキストを抽出する関数
def extract_text_from_pdf(file_path: str) -> str:
    with open(file_path, "rb") as f:
        pdf_reader = PyPDF2.PdfReader(f)
        text = ""
        for page_num in range(len(pdf_reader.pages)):
            text += pdf_reader.pages[page_num].extract_text()
    return text

# リクエストボディ用のPydanticモデル
class SummarizeRequest(BaseModel):
    text: str
    filename: str
  
# ファイル内容からハッシュを生成する関数
def generate_file_hash(file_path: str) -> str:
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

# 文字列からハッシュを生成する関数
def generate_string_hash(input_string: str) -> str:
    return hashlib.md5(input_string.encode()).hexdigest()

# APIエンドポイント: PDFファイルをアップロードしてテキストを抽出する
@app.post("/upload-pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    print("test")
    # アップロードされたファイルを保存するディレクトリ
    upload_dir = "uploaded_pdfs"
    os.makedirs(upload_dir, exist_ok=True)
    
    # 一時ファイルを保存
    temp_file_path = os.path.join(upload_dir, file.filename)
    with open(temp_file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    # ファイル内容からハッシュを生成してファイル名に利用
    file_hash = generate_file_hash(temp_file_path)
    hashed_file_path = os.path.join(upload_dir, f"{file_hash}.pdf")
    
    # ハッシュを用いたファイル名で保存（既に存在しない場合のみ）
    if not os.path.exists(hashed_file_path):
        shutil.move(temp_file_path, hashed_file_path)
    else:
        os.remove(temp_file_path)  # 一時ファイルを削除
    
    # テキストを抽出
    text = extract_text_from_pdf(hashed_file_path)
    if len(text) == 0:
        return {"error": "PDFからテキストを抽出できませんでした。"}
    return {"extracted_text": text, "filename": f"{file_hash}.pdf"}

# APIエンドポイント: 抽出されたテキストを要約する
@app.post("/summarize-text/")
async def summarize_text(request: SummarizeRequest):
    text = request.text
    filename = request.filename
    if len(text) == 0:
        return {"error": "要約するテキストがありません。"}
    
    # 既に同じファイルの要約結果が存在するか確認
    results_dir = "summary_results"
    os.makedirs(results_dir, exist_ok=True)
    result_file_path = os.path.join(results_dir, f"{generate_string_hash(filename)}_summary.json")
    if os.path.exists(result_file_path):
        with open(result_file_path, "r", encoding="utf-8") as f:
            existing_result = json.load(f)
        return {"summary": existing_result["summary"]}
    
    # プロンプトを外部ファイルから読み込む
    prompt_file_path = os.path.join(os.path.dirname(__file__), 'prompt.txt')
    with open(prompt_file_path, 'r', encoding='utf-8') as f:
        prompt_template = f.read()
    
    # GPT-4を使用して要約を生成
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt_template.format(text=text)}
        ],
        max_tokens=5000,
        temperature=0.7
    )
    summary = completion.choices[0].message.content
    
    # 結果を保存
    result = {
        "filename": filename,
        "title": filename.split('.')[0],  # タイトルをファイル名から取得（拡張子除く）
        "extracted_text": text,
        "summary": summary
    }
    with open(result_file_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)
    
    return {"summary": summary}