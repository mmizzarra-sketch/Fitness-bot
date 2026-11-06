from aiogram import Router, F
from aiogram.types import Message
from datetime import date, timedelta

from db.database import get_db
from bot.keyboards.keyboards import main_menu
from utils.calculations import suggest_deload

router = Router()


@router.message(F.text == "💡 Рекомендации")
async def show_recommendations(message: Message):
    user_id = message.from_user.id
    week_ago = (date.today() - timedelta(days=14)).isoformat()

    async with await get_db() as db:
        async with db.execute(
            "SELECT limitations, weight FROM users WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            user = await cursor.fetchone()

        async with db.execute(
            """
            SELECT COUNT(*) as cnt, AVG(energy_level) as avg_energy
            FROM workouts WHERE user_id = ? AND date >= ?
            """,
            (user_id, week_ago)
        ) as cursor:
            stats = await cursor.fetchone()

        async with db.execute(
            """
            SELECT e.name, e.weight, e.reps, e.sets, w.date, w.energy_level
            FROM exercises e
            JOIN workouts w ON e.workout_id = w.id
            WHERE w.user_id = ?
            ORDER BY w.date DESC, e.id DESC
            LIMIT 8
            """,
            (user_id,)
        ) as cursor:
            last_exercises = await cursor.fetchall()

    text = "<b>💡 Персональные рекомендации</b>\n\n"

    if user and user["limitations"]:
        text += (
            "<b>С учётом твоих ограничений:</b>\n"
            "• <b>Плечо:</b> избегай или сильно ограничивай жим на наклонной и любые движения, "
            "где гантели/штанга опускаются до уровня груди с нагрузкой. "
            "Приоритет — внешняя ротация, face pulls, тяги, Y-W-T.\n"
            "• <b>Голеностоп + бедро:</b> продолжай присед с клиньями. "
            "Обязательно отдельно работай над мобильностью голеностопа и внешней ротацией бедра.\n\n"
        )

    if stats and stats["cnt"]:
        deload = suggest_deload(stats["cnt"], stats["avg_energy"] or 7)
        if deload:
            text += deload + "\n\n"

    text += (
        "<b>Общие принципы прогрессии для тебя:</b>\n"
        "1. В тяговых движениях можно прогрессировать смелее — +1.25–2.5 кг или +1–2 повтора.\n"
        "2. В приседе и RDL на одной ноге — очень аккуратно. Лучше сначала добавлять повторы.\n"
        "3. Если самочувствие 6/10 и ниже два раза подряд — снижай объём.\n"
        "4. После болезни возвращайся плавно: первая неделя — 60–70% обычных весов.\n\n"
    )

    if last_exercises:
        text += "<b>Последние записанные упражнения:</b>\n"
        for ex in last_exercises[:5]:
            text += f"• {ex['name']}: {ex['sets']}×{ex['reps']} × {ex['weight']} кг ({ex['date']})\n"

    await message.answer(text, reply_markup=main_menu(), parse_mode="HTML")
