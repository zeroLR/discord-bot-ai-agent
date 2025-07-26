import logging
import discord
from discord.ext import commands
from discord.ext.commands import Context
from google import genai
from google.genai import types
from pydantic import BaseModel
import enum
import os  # 用於從環境變數讀取 TOKEN
from utils import transform_response_content


# Gemini Model Enum
class GeminiModel(enum.Enum):
    GEMINI_25_FLASH_LITE = "gemini-2.5-flash-lite"
    GEMINI_25_FLASH = "gemini-2.5-flash"
    GEMINI_25_PRO = "gemini-2.5-pro"


# 載入 .env 檔案
from dotenv import load_dotenv

load_dotenv()

# 啟用必要的 Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # 如果需要處理成員相關資訊，建議開啟

# 初始化 Bot，可以設定一個指令前綴，即使主要用提及
bot = commands.Bot(command_prefix="!", intents=intents)

used_gemini_model = GeminiModel.GEMINI_25_FLASH_LITE
system_instruction = "以繁體中文回答問題，語氣保持專業與嚴謹"


# 顯示當前使用即可用的模型
@bot.command()
async def showUsedModel(ctx: Context):
    await ctx.send(
        f"{ctx.author.mention}，當前使用的模型是：{used_gemini_model.value}\n可使用的模型列表： {list(GeminiModel)}"
    )


# 設定使用的模型
@bot.command()
async def setModel(ctx: Context, model_name: str):
    global used_gemini_model
    try:
        used_gemini_model = GeminiModel[model_name]
        await ctx.send(
            f"{ctx.author.mention}，已成功設定使用的模型為：{used_gemini_model.value}"
        )
    except KeyError:
        await ctx.send(
            f"{ctx.author.mention}，無效的模型名稱。可用的模型列表： {list(GeminiModel)}"
        )


# 顯示當前的 system instruction
@bot.command()
async def showSystemInstruction(ctx: Context):
    await ctx.send(f"{ctx.author.mention}，當前的系統指令是：{system_instruction}")


# 設定 system instruction
@bot.command()
async def setSystemInstruction(ctx: Context, instruction: str):
    global system_instruction
    system_instruction = instruction
    await ctx.send(f"{ctx.author.mention}，已更新系統指令")


# Bot 收到指令時的事件
@bot.event
async def on_command(ctx: Context):
    logging.info(msg=f"使用者 {ctx.author} 執行了指令: {ctx.command}")


# Bot 執行完指令時的事件
@bot.event
async def on_command_completion(ctx: Context):
    logging.info(msg=f"指令 {ctx.command} 執行完成")


# 初始化 Google GenAI 客戶端
client = genai.Client()
chat = client.chats.create(
    model=used_gemini_model.value,
    config=types.GenerateContentConfig(
        system_instruction=system_instruction,
        max_output_tokens=10000,  # 最大輸出字數
        top_k=2,  # top-k 採樣
        top_p=0.5,  # top-p 採樣
        temperature=0.5,  # 溫度控制
        response_mime_type="application/json",  # 回應的 MIME 類型
        stop_sequences=["\n"],  # 停止序列
        seed=42,  # 隨機種子
    ),
)


# Bot 發生錯誤時的事件
@bot.event
async def on_error(event, *args, **kwargs):
    # 捕捉所有事件的錯誤
    import traceback

    # print(f"發生錯誤：{event}")
    logging.error(f"發生錯誤：{event}")
    traceback.print_exc()


# Bot 啟動時的事件
@bot.event
async def on_ready():
    print(f"Bot 已上線！登入為 {bot.user.name}")
    print(f"Bot ID: {bot.user.id}")
    print("---")
    # 發送一條訊息到所有伺服器的第一個頻道
    for guild in bot.guilds:
        # 確保 Bot 有權限發送訊息到這個頻道
        if guild.text_channels:
            channel = guild.text_channels[0]
            try:
                await channel.send(f"我上線囉！")
            except discord.Forbidden:
                print(
                    f"無法在 {guild.name} 的 {channel.name} 頻道發送訊息，可能是權限不足。"
                )


# 監聽所有訊息的事件
@bot.event
async def on_message(message: discord.Message):
    # 忽略機器人自己的訊息，防止無限迴圈
    if message.author == bot.user:
        return

    # 檢查訊息中是否提及了這個機器人
    # message.mentions 是一個列表，包含所有被提及的用戶或角色
    # bot.user 是你的機器人帳號
    if bot.user.mentioned_in(message):
        # 移除提及部分，只保留實際的訊息內容
        # message.clean_content 會自動處理提及標籤，例如 @BotName 會被移除
        # 但是它會將 mentions 替換為可讀的名稱，所以我們再進一步處理

        # 獲取純淨的訊息內容，通常會移除提及的 `@{Bot名稱}` 部分
        # 並去除前後空白
        content_after_mention = message.clean_content.replace(
            f"@{bot.user.name}", ""
        ).strip()

        logging.info(
            msg=f"[{message.guild.name}/{message.channel.name}] {message.author.name} 提及了 Bot：'{content_after_mention}'"
        )

        # 這裡是你串接 AI 的地方
        await process_gemini_send_message_and_reply(message, content_after_mention)

    # 確保 Bot 的指令也能正常運作
    await bot.process_commands(message)


class CommonResponse(BaseModel):
    result: str


async def process_gemini_send_message_and_reply(message: discord.Message, content: str):

    if content.strip() == "":
        message.reply(
            f"哈囉 {message.author.mention}！你提及了我，但沒有給我具體的問題呢。"
        )
        return

    response = chat.send_message(
        message=content,
        config={
            "response_mime_type": "application/json",
            "response_schema": CommonResponse,
        },
    )

    # 處理 AI 候選回覆
    finish_reason_message = ""
    if response and response.candidates:
        finish_reason: types.FinishReason = response.candidates[0].finish_reason

        if finish_reason != types.FinishReason.STOP:
            match finish_reason:
                case types.FinishReason.MAX_TOKENS:
                    finish_reason_message = "回應因達到最大字數限制而停止。"
                case types.FinishReason.TIMEOUT:
                    finish_reason_message = "回應因超時而停止。"
                case _:
                    finish_reason_message = f"未知的結束原因：{finish_reason}"

            # 印出回應和結束原因
            logging.error(msg=f"結束原因：{finish_reason_message}, 回應：{response}")
            await message.reply(f"結束原因：{finish_reason_message}")
            return

    # Use instantiated objects.
    struct_response: CommonResponse = response.parsed
    chunks = transform_response_content(struct_response.result)

    # 依序發送每一段分割內容
    for chunk in chunks:
        await message.reply(chunk)


# 執行 Bot
# 建議將 TOKEN 儲存在環境變數中，確保安全性
# 例如：在執行腳本前設定環境變數 DISCORD_BOT_TOKEN="你的TOKEN"
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("錯誤：請設定環境變數 'DISCORD_BOT_TOKEN' 以提供 Bot 的 Token。")
