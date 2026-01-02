from selenium import webdriver  #自動操作瀏覽器
from selenium.webdriver.common.by import By #定義定位元素的方法
from selenium.webdriver.chrome.options import Options #設定 Chrome 瀏覽器啟動選項
from selenium.webdriver.support.ui import WebDriverWait# 顯式等待物件，用於等待元素出現
from selenium.webdriver.support import expected_conditions as EC # 用於條件判斷，例如元素可見
from bs4 import BeautifulSoup
import sqlite3
import time

def scrape_quotes():
    options = Options() # 建立 Chrome 選項物件
    options.add_argument("--headless") # 無頭模式
    options.add_argument("--disable-gpu") # 停用 GPU 加速
    options.add_argument("--no-sandbox")
    options.add_argument("--start-maximized") # 啟動時最大化視窗

    driver = webdriver.Chrome(options=options)# 建立 Chrome 瀏覽器物件
    wait = WebDriverWait(driver, 10) #最多等 10 秒

    driver.get("http://quotes.toscrape.com/js/")

    quotes_list = [] # 用來存放所有抓到的名言
    current_page = 1 # 記錄目前頁數

    while current_page <= 5:
        print(f"正在爬取第 {current_page} 頁...")
        time.sleep(1)

         # 取得當前頁面的 HTML
        soup = BeautifulSoup(driver.page_source, "html.parser")

        quote_blocks = soup.select("div.quote")# 選取所有名言區塊 

        for q in quote_blocks:
            text = q.select_one(".text").get_text(strip=True)  # 取得名言文字
            author = q.select_one(".author").get_text(strip=True)  # 取得作者名稱

            # 取得標籤，組成用逗號分隔的字串
            tags = ",".join([t.get_text(strip=True) for t in q.select(".tag")])
            
            # 將抓到的資料加入列表
            quotes_list.append({
                "text": text,
                "author": author,
                "tags": tags
            })

        try: 
            #找到下一頁按鈕
            next_btn = driver.find_element(By.CSS_SELECTOR, "li.next > a")

            #用 JavaScript 點擊下一頁按鈕，避免 click() 無法點擊
            driver.execute_script("arguments[0].click();", next_btn) 

            #等待下一頁的名言區塊出現，確保頁面載入完成
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "quote")))
            
            current_page += 1 # 爬取頁數加 1
        except: # 如果找不到下一頁按鈕就跳出迴圈
            break

    driver.quit() # 關閉瀏覽器
    print(f"爬取完成，共取得 {len(quotes_list)} 筆名言資料。")
    return quotes_list

#把名言存入 SQLite 資料庫
def save_to_db(quotes):
    conn = sqlite3.connect("quotes.db") # 連接資料庫（不存在會自動建立）
    cursor = conn.cursor()  # 建立游標，用來執行 SQL

    #建立資料表 quotes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quotes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,  
        text TEXT NOT NULL,
        author TEXT NOT NULL,
        tags TEXT
    )
    """)

    # 將每筆名言存入資料庫
    for q in quotes:
        cursor.execute(
            "INSERT INTO quotes (text, author, tags) VALUES (?, ?, ?)",
            (q["text"], q["author"], q["tags"])
        )
    conn.commit() # 提交更改
    conn.close()  # 關閉資料庫
    print("資料已存入 quotes.db")

# 程式進入點
if __name__ == "__main__":
    quotes = scrape_quotes()  #執行爬取名言函數
    save_to_db(quotes) # 存入資料庫

    # 測試(顯示前 10 筆名言)
    for q in quotes[:10]:
        print(f"{q['text']} - {q['author']} - {q['tags']}")
