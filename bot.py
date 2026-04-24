from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

from config import BOT_TOKEN
from sheets import get_branches, get_employees_by_branch, find_employee, get_tm_chat_ids, get_ready_for_tm

import asyncio

asyncio.set_event_loop(asyncio.new_event_loop())

MAIN_MENU = ReplyKeyboardMarkup(
    [
        ["📍 Филиалы", "🔎 Найти сотрудника"],
        ["⚠️ Уведомить ТМ", "ℹ️ Помощь"]
    ],
    resize_keyboard=True
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Добро пожаловать в бот обучения замещающих менеджеров.\n\nВыберите раздел:",
        reply_markup=MAIN_MENU
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text == "📍 Филиалы":
        branches = get_branches()

        if not branches:
            await update.message.reply_text("Филиалы не найдены.")
            return

        msg = "Список филиалов:\n\n"
        for branch in branches:
            msg += f"• {branch}\n"

        msg += "\nНапиши просто название филиала"
        await update.message.reply_text(msg)

    elif text.lower().startswith("филиал "):
        branch = text.replace("филиал", "", 1).strip()
        employees = get_employees_by_branch(branch)

        if not employees:
            await update.message.reply_text("По этому филиалу сотрудники не найдены.")
            return

        msg = f"Филиал: {branch}\n\n"

        for row in employees:
            fio = row.get("ФИО", "")
            percent = row.get("% готовности", "")
            level = row.get("Уровень", "")
            notify = row.get("Уведомить ТМ", "")

            mark = "✅" if str(notify).strip().lower() == "да" else ""
            msg += f"{fio} — {percent}% — {level} {mark}\n"

        await update.message.reply_text(msg)

    elif text == "🔎 Найти сотрудника":
        await update.message.reply_text(
            "Напиши имя или ID сотрудника\n\nНапример:\nАлиев\nEMP001"
        )

    elif text == "⚠️ Уведомить ТМ":
        all_rows = []

        for branch in get_branches():
            all_rows.extend(get_employees_by_branch(branch))

        ready = [
            row for row in all_rows
            if str(row.get("Уведомить ТМ", "")).strip().lower() == "да"
        ]

        if not ready:
            await update.message.reply_text("Пока нет сотрудников для уведомления ТМ.")
            return

        msg = "Сотрудники для уведомления ТМ:\n\n"

        for row in ready:
            msg += (
                f"✅ {row.get('ФИО', '')}\n"
                f"🏢 {row.get('Филиал', '')}\n"
                f"📊 {row.get('% готовности', '')}%\n"
                f"🎯 {row.get('Уровень', '')}\n\n"
            )

        await update.message.reply_text(msg)

    elif text == "ℹ️ Помощь":
        await update.message.reply_text(
            "Команды:\n\n"
            "📍 Филиалы — список филиалов\n"
            "Напиши просто: Сергели\n"
            "🔎 Найти сотрудника — поиск\n"
            "⚠️ Уведомить ТМ — готовые сотрудники"
        )

    else:
        text_lower = text.lower()

        # Проверка филиала
        branches = get_branches()
        for branch in branches:
            if text_lower == branch.lower():
                employees = get_employees_by_branch(branch)

                if not employees:
                    await update.message.reply_text("Сотрудники не найдены.")
                    return

                msg = f"Филиал: {branch}\n\n"

                for row in employees:
                    fio = row.get("ФИО", "")
                    percent = row.get("% готовности", "")
                    level = row.get("Уровень", "")

                    msg += f"{fio} — {percent}% — {level}\n"

                await update.message.reply_text(msg)
                return

        # Проверка сотрудника
        results = find_employee(text)

        if results:
            msg = "Найдено:\n\n"
            for row in results[:5]:
                msg += (
                    f"{row.get('ФИО')}\n"
                    f"{row.get('% готовности')}% — {row.get('Уровень')}\n\n"
                )
            await update.message.reply_text(msg)
            return

        await update.message.reply_text("Не нашла. Попробуй ещё раз 🙏")
        
async def auto_notify_tm(context: ContextTypes.DEFAULT_TYPE):
    ready = get_ready_for_tm()
    tm_ids = get_tm_chat_ids()

    if not ready or not tm_ids:
        return

    msg = "🔔 Авто-уведомление ТМ\n\nСотрудники готовы:\n\n"

    for row in ready:
        msg += (
            f"✅ {row.get('ФИО', '')}\n"
            f"🏢 Филиал: {row.get('Филиал', '')}\n"
            f"📊 Готовность: {row.get('% готовности', '')}%\n"
            f"🎯 Уровень: {row.get('Уровень', '')}\n\n"
        )

    for chat_id in tm_ids:
        await context.bot.send_message(chat_id=chat_id, text=msg)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.job_queue.run_repeating(auto_notify_tm, interval=600, first=10)

    print("Бот запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()
