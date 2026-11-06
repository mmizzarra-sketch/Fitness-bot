from aiogram import Router, F
from aiogram.types import Message

from db.database import get_db
from bot.keyboards.keyboards import main_menu

router = Router()


@router.message(F.text == "📋 Программы")
async def show_programs(message: Message):
    user_id = message.from_user.id

    async with await get_db() as db:
        async with db.execute(
            "SELECT title, content, created_at FROM programs WHERE user_id = ? ORDER BY created_at DESC LIMIT 5",
            (user_id,)
        ) as cursor:
            programs = await cursor.fetchall()

    text = (
        "<b>📋 Программы тренировок</b>\n\n"
        "Сейчас у тебя зафиксирована текущая программа (верх / низ + бассейн).\n\n"
        "<b>Верх тела:</b>\n"
        "• Разминка на мобильность\n"
        "• Внешняя ротация с гантелью\n"
        "• Мёртвый жук\n"
        "• Жим Лэндмайн одной рукой\n"
        "• Вертикальная тяга\n"
        "• Тяга на наклонной скамье\n"
        "• Face pulls\n"
        "• Y-W-T\n"
        "• Растяжка\n\n"
        "<b>Низ тела:</b>\n"
        "• Мобильность и активация (голеностоп + бедро)\n"
        "• Step down\n"
        "• Airplane / DNS star\n"
        "• Присед со штангой (с клиньями)\n"
        "• RDL на одной ноге\n\n"
        "<b>Бассейн:</b> 2 раза в неделю 45–60 минут.\n\n"
    )

    if programs:
        text += "<b>Сохранённые версии:</b>\n"
        for p in programs:
            text += f"• {p['title']} ({p['created_at'][:10]})\n"
    else:
        text += "Пока сохранённых программ в базе нет.\nКогда понадобится корректировка — смогу сгенерировать обновлённую."

    await message.answer(text, reply_markup=main_menu(), parse_mode="HTML")
