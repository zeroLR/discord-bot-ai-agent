import os
import logging
from returns.result import Success, Failure

from dotenv import load_dotenv

import discord
from discord.ext import commands
from discord.ext.commands import Context

from core.enum import model
from client import provider
from util.utils import transform_response_content

# 載入 .env 檔案
load_dotenv()
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

# 啟用必要的 Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # 如果需要處理成員相關資訊，建議開啟

# 初始化 Bot，可以設定一個指令前綴，即使主要用提及
bot = commands.Bot(command_prefix="!", intents=intents)

# 初始化 AI 客戶端
ai_client = provider.AIProvider.get_client(model.Provider.GOOGLE)

if ai_client is None:
    logging.error("無法初始化 Provider 客戶端，請檢查環境變數或客戶端實現。")
    exit(1)


# Bot 收到指令時的事件
@bot.event
async def on_command(ctx: Context):
    logging.info(msg=f"使用者 {ctx.author} 執行了指令: {ctx.command}")


# Bot 執行完指令時的事件
@bot.event
async def on_command_completion(ctx: Context):
    logging.info(msg=f"指令 {ctx.command} 執行完成")


# Bot 發生錯誤時的事件
@bot.event
async def on_error(event, *args, **kwargs):
    # 捕捉所有事件的錯誤
    import traceback

    logging.error(f"發生錯誤：{event}")
    traceback.print_exc()


# Bot 啟動時的事件
@bot.event
async def on_ready():
    logging.info(f"Bot 已上線！登入為 {bot.user.name}")
    logging.info(f"Bot ID: {bot.user.id}")
    logging.info("---")
    # 發送一條訊息到所有伺服器的第一個頻道
    for guild in bot.guilds:
        # 確保 Bot 有權限發送訊息到這個頻道
        if guild.text_channels:
            channel = guild.text_channels[0]
            try:
                await channel.send(f"我上線囉！")
            except discord.Forbidden:
                logging.info(
                    f"無法在 {guild.name} 的 {channel.name} 頻道發送訊息，可能是權限不足。"
                )


# 監聽所有訊息的事件
@bot.event
async def on_message(message: discord.Message):
    # 忽略機器人自己的訊息，防止無限迴圈
    if message.author == bot.user:
        return

    # 檢查是否是回覆機器人的訊息
    if message.reference:
        replied_message = await message.channel.fetch_message(
            message.reference.message_id
        )
        if replied_message.author == bot.user:
            # 這是回覆機器人的訊息
            content_after_reply = message.clean_content.replace(
                f"@{bot.user.name}", ""
            ).strip()
            logging.info(
                msg=f"[{message.guild.name}/{message.channel.name}] {message.author.name} 回覆了 Bot：'{content_after_reply}'"
            )

            # 這裡是你串接 AI 的地方
            await process_send_message_and_reply(message, content_after_reply)
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
        await process_send_message_and_reply(message, content_after_mention)

    # 確保 Bot 的指令也能正常運作
    await bot.process_commands(message)


async def process_send_message_and_reply(message: discord.Message, content: str):

    if content.strip() == "":
        await message.reply(
            f"哈囉 {message.author.mention}！你提及了我，但沒有給我具體的問題呢。"
        )
        return

    result = ai_client.send_message(content)

    match result:
        case Success(response):
            # 成功獲取 AI 回應
            logging.debug(f"AI 回應成功：{response}")
            # 將 AI 回應內容分割成多個 chunk
            chunks = transform_response_content(response)

            # 依序發送每一段分割內容
            for chunk in chunks:
                await message.reply(chunk)
        case Failure(err):
            # 處理錯誤情況
            logging.error(f"AI 回應失敗：{err}")
            await message.reply(f"AI 回應失敗，錯誤：{err}")
            return


# 執行 Bot
# 建議將 TOKEN 儲存在環境變數中，確保安全性
# 例如：在執行腳本前設定環境變數 DISCORD_BOT_TOKEN="你的TOKEN"
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    logging.error("錯誤：請設定環境變數 'DISCORD_BOT_TOKEN' 以提供 Bot 的 Token。")
