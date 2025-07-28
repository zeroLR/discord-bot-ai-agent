FROM python:3.11-slim

# 安全性：建立非 root 用戶
RUN useradd -m botuser

WORKDIR /app

# 只複製必要檔案，減少 build context
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 複製專案程式碼
COPY . .

# 設定權限給非 root 用戶
RUN chown -R botuser:botuser /app
USER botuser

# 預設不複製 .env，建議用 docker run --env-file 傳入
# CMD 可用 python -O 關閉 assert，提升安全性
CMD ["python", "-O", "bot.py"]
