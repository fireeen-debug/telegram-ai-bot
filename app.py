import os
import asyncio
import sqlite3
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from openai import OpenAI

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_KEY")

client = OpenAI(api_key=OPENAI_KEY)

conn = sqlite3.connect("memory.db")
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS messages (user_id TEXT, role TEXT, content TEXT)")
conn.commit()

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    text = update.message.text

    c.execute("INSERT INTO messages VALUES (?, ?, ?)", (user_id, "user", text))
    conn.commit()

    c.execute("SELECT role, content FROM messages WHERE user_id=? ORDER BY rowid DESC LIMIT 15", (user_id,))
    history = c.fetchall()
    history.reverse()

    messages = [{"role": "system", "content": "Ты — это я. Пиши c юмором, сарказмом, пошлыми шутками и довольно частым матом, но в меру"}]
    for r, content in history:
        messages.append({"role": r, "content": content})

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=1
    )

    reply = response.choices[0].message.content

    c.execute("INSERT INTO messages VALUES (?, ?, ?)", (user_id, "assistant", reply))
    conn.commit()

    await asyncio.sleep(2)
    await update.message.reply_text(reply)

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
app.run_polling()
