import tkinter as tk
from tkinter import ttk #tkinter 的進階元件，如 Treeview、Scrollbar
import threading   #匯入 threading，用來開子執行緒，避免 GUI 卡住
import requests

API_URL = "http://127.0.0.1:8000/quotes"


class QuoteApp:
    def __init__(self, root):
        self.root = root    # 保存 Tk 主視窗
        self.root.title("名言佳句管理系統 (Threading 版)")  # 設定視窗標題
        self.root.geometry("800x600")  # 設定視窗大小

        self.selected_id = None   # 目前選到的資料

        #上方訊息 Label
        self.msg_label = tk.Label(self.root, text="", font=("Arial", 12), anchor="center")
        self.msg_label.pack(fill=tk.X, pady=5)   # 填滿 X 軸並留上下距離

        # 建立各個 UI 區塊
        self.create_treeview()    #表格
        self.create_form()        #編輯/新增表單
        self.create_buttons()     #操作按鈕
        self.create_statusbar()   #狀態列

        # 程式啟動時，先載入資料
        self.refresh_quotes()

    # Treeview（表格)
    def create_treeview(self):
        frame = ttk.Frame(self.root) # 外層容器
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        columns = ("ID", "Author", "Text", "Tags")  # 定義欄位名稱
        self.tree = ttk.Treeview(frame, columns=columns, show="headings")    # show="headings" 只顯示標題，不顯示樹狀

        # 設定每一欄的標題與寬度
        for col, w in zip(columns, [50, 120, 380, 200]):
            self.tree.heading(col, text=col)  # 設定欄位名稱
            self.tree.column(col, width=w)  # 設定欄位寬度

        # 建立垂直捲軸  # orient="vertical" 垂直方向  # command=self.tree.yview 捲動Treeview
        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)  # Treeview 綁定捲軸
        vsb.pack(side="right", fill="y")  # 捲軸靠右
        self.tree.pack(fill=tk.BOTH, expand=True)

        # 綁定「選取資料列」事件
        self.tree.bind("<<TreeviewSelect>>", self.on_select)


    #表單區 
    def create_form(self):
        form_frame = ttk.LabelFrame(self.root, text="編輯/新增區")
        form_frame.pack(fill=tk.X, padx=10, pady=5)

        # 名言內容標籤
        ttk.Label(form_frame, text="名言內容 (Text):").grid(row=0, column=0, sticky="w")
        
        # 多行文字輸入框
        self.text_box = tk.Text(form_frame, height=5)
        self.text_box.grid(row=1, column=0, columnspan=4, sticky="we", pady=5)

        # 作者標籤
        ttk.Label(form_frame, text="作者 (Author):").grid(row=2, column=0, sticky="w")
        
        # 作者輸入框
        self.author_entry = ttk.Entry(form_frame)
        self.author_entry.grid(row=3, column=0, sticky="we", padx=5)

        # 標籤標籤
        ttk.Label(form_frame, text="標籤 (Tags):").grid(row=2, column=2, sticky="w")
        self.tags_entry = ttk.Entry(form_frame)
        self.tags_entry.grid(row=3, column=2, sticky="we", padx=5)

        # 讓欄位可以跟著視窗伸縮
        form_frame.columnconfigure(0, weight=1)
        form_frame.columnconfigure(2, weight=1)

    #操作按鈕
    def create_buttons(self):
        btn_frame = ttk.LabelFrame(self.root, text="操作選項")
        btn_frame.pack(fill=tk.X, padx=10, pady=5)

        # 重新整理按鈕
        self.refresh_btn = tk.Button(btn_frame, text="重新整理 (Refresh)", bg="#5bc0de", fg="white",command=lambda: self.on_button_click(self.refresh_btn, self._get_worker))
        self.refresh_btn.grid(row=0, column=0, sticky="we", padx=5)

        # 新增按鈕
        self.add_btn = tk.Button(btn_frame, text="新增 (Add)", bg="#5cb85c", fg="white",command=lambda: self.on_button_click(self.add_btn, self._add_worker))
        self.add_btn.grid(row=0, column=1, sticky="we", padx=5)

        # 更新按鈕
        self.update_btn = tk.Button(btn_frame, text="更新 (Update)", bg="#f0ad4e", fg="white",command=lambda: self.on_button_click(self.update_btn, self._update_worker),state=tk.DISABLED)
        self.update_btn.grid(row=0, column=2, sticky="we", padx=5)

         # 刪除按鈕
        self.delete_btn = tk.Button(btn_frame, text="刪除 (Delete)", bg="#d9534f", fg="white",command=lambda: self.on_button_click(self.delete_btn, self._delete_worker),state=tk.DISABLED)
        self.delete_btn.grid(row=0, column=3, sticky="we", padx=5)

        # 讓四顆按鈕平均分配寬度
        for i in range(4):
            btn_frame.columnconfigure(i, weight=1)

    #底部狀態列
    def create_statusbar(self):
        self.status = tk.Label(self.root, text="就緒", relief=tk.SUNKEN, anchor=tk.W)
        self.status.pack(fill=tk.X, side=tk.BOTTOM)

    
    def set_status(self, text, color="black"):
        self.status.config(text=text, fg=color) # 更新狀態列文字與顏色

    def show_message(self, text, color="green", duration=3000):
        """上方顯示訊息,green=成功, red=失敗"""
        self.msg_label.config(text=text, fg=color)
        self.root.after(duration, lambda: self.msg_label.config(text=""))

    def clear_form(self):
        """把「新增 / 編輯區」裡所有輸入的內容清空，回到空白狀態"""
        self.text_box.delete("1.0", tk.END) #清空「名言內容」，從第一個字，刪到最後一個字
        self.author_entry.delete(0, tk.END) #整行清空「作者」欄位
        self.tags_entry.delete(0, tk.END)   #清空標籤欄位
        self.selected_id = None            # 取消選取 id
        self.update_btn.config(state=tk.DISABLED)  #把 更新 (Update)按鈕關掉
        self.delete_btn.config(state=tk.DISABLED)  #把刪除 (Delete)按鈕 關掉，因為刪除一定要「先選一筆」
        self.set_status("已選取ID：None")  #目前「沒有選任何一筆資料」

    #當使用者在表格 (Treeview) 點一列時 呼叫
    def on_select(self, event):
        selected = self.tree.selection() #現在被選到的是某一列
        if not selected:   #使用者點到空白or取消選取，就直接離開函式
            return
        item = self.tree.item(selected[0])["values"]  #取得那一列的實際資料
        self.selected_id = item[0]   #記住選到哪個id

        self.text_box.delete("1.0", tk.END)   #先清空"名言內容"
        self.text_box.insert(tk.END, item[2]) #再把選到的名言文字放進去
        self.author_entry.delete(0, tk.END)  #清空作者欄位
        self.author_entry.insert(0, item[1]) #填入選到那筆資料的作者
        self.tags_entry.delete(0, tk.END)   #清空標籤
        self.tags_entry.insert(0, item[3])  #填入對應的 tags

        self.update_btn.config(state=tk.NORMAL)  #開啟更新按紐
        self.delete_btn.config(state=tk.NORMAL)  #開啟刪除按紐
        self.set_status(f"已選取ID：{self.selected_id}")  #在狀態列顯示 ex.已選取ID：11

    #載入中 + 多執行緒設計
    def on_button_click(self, btn, worker_func):
        original_text = btn.cget("text")   #記住原本按鈕文字
        btn.config(text="載入中…", state=tk.DISABLED)  #顯示「載入中」並鎖住按鈕

        def wrapper():  #在「子執行緒」中執行
            try:
                worker_func()
            finally:   #不管成功或失敗，一定會執行下面的還原動作
                #回主執行緒還原按鈕
                self.root.after(0, lambda: btn.config(text=original_text, state=tk.NORMAL))
        #啟動子執行緒
        threading.Thread(target=wrapper, daemon=True).start()

    #GET(重新整理資料)
    def refresh_quotes(self):

        #顯示「載入中」，用子執行緒跑 _get_worker
        self.on_button_click(self.refresh_btn, self._get_worker)

    def _get_worker(self):
        try:
            res = requests.get(API_URL)
            res.raise_for_status()
            data = res.json()   #把 API 回傳的 JSON，轉成 Python 的 list/dict
            self.root.after(0, lambda: self._update_tree(data))#回到主執行緒，更新 Treeview
        except Exception as e:  #如果 API 失敗
            self.root.after(0, lambda: self.set_status("錯誤：無法連線至後端 API", color="red"))
            self.root.after(0, lambda: self.show_message("資料載入失敗", color="red"))
            print("API error:", e)

    #更新 Treeview
    def _update_tree(self, data):
        self.tree.delete(*self.tree.get_children()) #把表格全部清空
        for q in data:
            #插入一列到表格， 對應欄位順序
            self.tree.insert("", tk.END, values=(q["id"], q["author"], q["text"], q["tags"]))
        self.set_status("資料載入完成", color="green")
        self.show_message("資料載入完成", color="green")
        self.clear_form()  #回到未選取狀態

    def add_quote(self):  #按下新增按鈕時，統一處理「載入中 / 鎖按鈕 / 開執行緒」
        self.on_button_click(self.add_btn, self._add_worker)

    def _add_worker(self):
        data = {
            #從 Text 元件取得內容   #"1.0" 代表第1行第0個字元開始  #tk.END 代表到最後   #strip() 用來去掉前後多餘的換行與空白
            "text": self.text_box.get("1.0", tk.END).strip(),
            "author": self.author_entry.get(), # 從作者輸入框取得文字
            "tags": self.tags_entry.get()      # 從標籤輸入框取得文字
        }
        try:
            requests.post(API_URL, json=data)        #將 data 轉成 JSON 傳給後端 API
            self.root.after(0, self.refresh_quotes)  # 用 after 回到主執行緒重新整理清單
            self.root.after(0, lambda: self.show_message("新增成功！", color="green"))
        except Exception as e:   # 發生錯誤
            self.root.after(0, lambda: self.show_message("新增失敗", color="red"))
            print("API error:", e)    # 在終端機印出錯誤，方便除錯

    #按下更新按鈕時執行
    def update_quote(self):

        #如果沒有選取任何一筆資料（Treeview 沒點）
        if not self.selected_id:
            return   # 直接離開
        
        # 有選取 id 才啟動 loading + 子執行緒
        self.on_button_click(self.update_btn, self._update_worker)

    #執行「更新資料」
    def _update_worker(self):

        # 再檢查一次是否有選取 id
        if not self.selected_id:
            return
        
        data = {   # 從畫面取得目前輸入的內容
            "text": self.text_box.get("1.0", tk.END).strip(),
            "author": self.author_entry.get(),
            "tags": self.tags_entry.get()
        }
        try:
            requests.put(f"{API_URL}/{self.selected_id}", json=data)

            
            self.root.after(0, self.refresh_quotes) # 更新完成後，重新抓資料刷新表格
            self.root.after(0, lambda: self.show_message("更新成功！", color="green"))
        
        except Exception as e:
            # 發生錯誤時顯示紅色錯誤訊息
            self.root.after(0, lambda: self.show_message("更新失敗", color="red"))
            print("API error:", e)

    #按下刪除按鈕時
    def delete_quote(self):
        if not self.selected_id:
            return
        self.on_button_click(self.delete_btn, self._delete_worker)

    #執行刪除 API
    def _delete_worker(self):
        if not self.selected_id:
            return
        try:
            # 呼叫 DELETE API
            # API_URL/ID = 刪除指定那一筆
            requests.delete(f"{API_URL}/{self.selected_id}")

            # 刪除成功後重新整理資料
            self.root.after(0, self.refresh_quotes)
            # 顯示刪除成功
            self.root.after(0, lambda: self.show_message("刪除成功！", color="green"))
        
        except Exception as e: # # 刪除失敗顯示紅色訊息
            self.root.after(0, lambda: self.show_message("刪除失敗", color="red"))
            print("API error:", e)


if __name__ == "__main__":
    root = tk.Tk()       # 建立 Tkinter 主視窗
    app = QuoteApp(root) # 建立 QuoteApp 類別實體，並把視窗傳進去
    root.mainloop()      # 啟動 GUI 事件迴圈
