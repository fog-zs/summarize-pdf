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
    result_file_path = os.path.join(results_dir, f"{generate_string_hash(text)}_summary.json")
    if os.path.exists(result_file_path):
        with open(result_file_path, "r", encoding="utf-8") as f:
            existing_result = json.load(f)            
            existing_result = old_to_new(existing_result)
            return {"paper": existing_result}
         
    prompt = get_prompt("summary")
    summary = llm(prompt, text)
    
    prompt = get_prompt("title")
    title = llm(prompt, text[:300])
    
    prompt = get_prompt("tag")
    tags = llm(prompt, title)    
    tasg = tags.replace(", ", ",")
    
    # 結果を保存
    result = {
        "filename": filename,
        "title": title, 
        "text": text,
        "summary": summary,
        "tags": tags.split(",")
    }
    with open(result_file_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)
    
    return {"paper": result }

def llm(prompt_template, text):        
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt_template.format(text=text)}
        ],
        max_tokens=5000,
        temperature=0.7
    )
    return completion.choices[0].message.content    
        
def get_prompt(prompt):
    file_path = os.path.join(os.path.dirname(__file__), 'prompts', f'{prompt}.txt')    
    
    with open(file_path, 'r', encoding='utf-8') as f:      
        prompt_text = f.read()  
        
        return prompt_text

@app.get("/get-papers/")
async def get_papers():
    results_dir = "summary_results"
    
    # アップロードされたPDFを読み込み
    papers = []
    if not os.path.exists(results_dir): return {"papers": none}
    for file_name in os.listdir(results_dir):
        result_file_path = os.path.join(results_dir, file_name)        
        paper = get_paper(result_file_path, file_name)
        papers.append(paper)
    
    return {"papers": papers }

def get_paper(file_path, file_name):    
    if not file_path.endswith(".json"): return
    
    file_hash = file_name.split("_")[0]        
    
    if not os.path.exists(file_path): return
    
    with open(file_path, "r", encoding="utf-8") as f:
        existing_result = json.load(f)            
    
    existing_result = old_to_new(existing_result)
    
    return {
        "id": file_hash,
        "title": existing_result["title"],  # タイトルをファイル名から取得（拡張子除く）
        "text": existing_result["extracted_text"],
        "summary": existing_result["text"],
        "tags": existing_result["tag"]
    }
    
def old_to_new(existing_result):
    if "tag" not in existing_result:
        existing_result["tag"] = []
    
    if "text" not in existing_result:
        existing_result["text"] = existing_result["extracted_text"]
        
    return existing_result
    