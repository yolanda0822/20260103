from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import sqlite3


# Pydantic 
class PostCreate(BaseModel):    
    text: str = Field(..., min_length=1) # 名言內容，至少一個字
    author: str = Field(..., min_length=1) # 作者名稱，至少一個字
    tags: str | None = "" # 標籤，可選，預設空字串

class PostResponse(PostCreate):
    id: int             # 讀取資料時包含的id欄位，繼承 PostCreate


# 建立 FastAPI
app = FastAPI(title="Quotes API") # 建立 FastAPI 應用，設定標題

DB_NAME = "quotes.db"  # SQLite 資料庫檔名


def get_db_connection():
    """
    取得資料庫連線
    row_factory 設定為 sqlite3.Row , 方便把結果轉成 dict
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # 支援用 dict(row) 轉成 dict
    return conn

# GET 
@app.get("/quotes", response_model=list[PostResponse])
def get_quotes():
    conn = get_db_connection() # 連線資料庫
    rows = conn.execute("SELECT * FROM quotes").fetchall() # 執行 SELECT，讀取所有資料
    conn.close() # 關閉資料庫連線
    return [dict(row) for row in rows] # 將每筆資料轉成 dict 回傳



# POST
@app.post("/quotes", response_model=PostResponse)
def create_quote(quote: PostCreate):
    conn = get_db_connection()
    cursor = conn.cursor() # 建立游標

    #執行 INSERT SQL 新增名言資料
    # quote.text   -> 名言內容
    # quote.author -> 作者
    # quote.tags   -> 標籤
    cursor.execute(
        "INSERT INTO quotes (text, author, tags) VALUES (?, ?, ?)",
        (quote.text, quote.author, quote.tags)
    )
    conn.commit()  # 提交變更
    new_id = cursor.lastrowid  # 取得剛新增的id

    # 取出剛新增的完整資料
    row = conn.execute("SELECT * FROM quotes WHERE id = ?", (new_id,)).fetchone() 
    conn.close()
    return dict(row) # 回傳新增的資料


# PUT
@app.put("/quotes/{quote_id}", response_model=PostResponse)
def update_quote(quote_id: int, quote: PostCreate):
    conn = get_db_connection()  # 連線資料庫
    cursor = conn.cursor()
     # 更新指定 id 的名言資料
    # quote.text   -> 更新後的名言內容
    # quote.author -> 更新後的作者
    # quote.tags   -> 更新後的標籤
    # quote_id     -> 指定要更新的資料id
    cursor.execute(
        "UPDATE quotes SET text = ?, author = ?, tags = ? WHERE id = ?",
        (quote.text, quote.author, quote.tags, quote_id)
    )
    conn.commit()  # 提交變更

    # 取出更新後的資料
    row = conn.execute("SELECT * FROM quotes WHERE id = ?", (quote_id,)).fetchone()
    conn.close()

    if row is None:  # 如果資料不存在，回傳 404 錯誤
        raise HTTPException(status_code=404, detail="Quote not found")
    return dict(row)

# DELETE 
@app.delete("/quotes/{quote_id}")
def delete_quote(quote_id: int):
    conn = get_db_connection() # 連線資料庫
    cursor = conn.cursor()  # 建立游標

    #刪除指定 ID 的資料
    cursor.execute("DELETE FROM quotes WHERE id = ?", (quote_id,))
    conn.commit() # 提交變更
    conn.close() # 關閉資料庫連線

    # 如果沒有刪到資料，回傳 404
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Quote not found")
    return {"message": "Quote deleted successfully"}  # 回傳刪除成功訊息
