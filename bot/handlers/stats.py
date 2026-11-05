from aiogram import Router, F
from aiogram.types import Message
from datetime import date, timedelta

from db.database import get_db
from bot.keyboards.keyboards import main_menu

router = Router()


@router.message(F.text == "📊 Статистика")
async def show_stats(message: Message):
    user_id = message.from_user.id
    today = date.today().isoformat()
    week_ago = (date.today() - timedelta(days=7)).isoformat()

    async with await get_db() as db:
        async with db.execute(
            """
            SELECT workout_type, duration_min, energy_level, calories_burned
            FROM workouts WHERE user_id = ? AND date = ?
            """,
            (user_id, today)
        ) as cursor:
            today_workouts = await cursor.fetchall()

        async with db.execute(
            """
            SELECT 
                COALESCE(SUM(calories), 0) as cal,
                COALESCE(SUM(protein), 0) as prot,
                COALESCE(SUM(fat), 0) as f,
                COALESCE(SUM(carbs), 0) as c
            FROM meals WHERE user_id = ? AND date = ?
            """,
            (user_id, today)
        ) as cursor:
            today_meals = await cursor.fetchone()

        async with db.execute(
            "SELECT calorie_goal, protein_goal, fat_goal, carb_goal, weight FROM users WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            user = await cursor.fetchone()

        async with db.execute(
            """
            SELECT COUNT(*) as cnt, AVG(energy_level) as avg_energy,
                   SUM(calories_burned) as total_burned
            FROM workouts WHERE user_id = ? AND date >= ?
            """,
            (user_id, week_ago)
        ) as cursor:
            week_stats = await cursor.fetchone()

    text = f"<b>📊 Статистика на {today}</b>\n\n"

    if today_workouts:
        text += "<b>Тренировки сегодня:</b>\n"
        total_burned_today = 0
        for w in today_workouts:
            type_name = {
                "gym_upper": "Верх",
                "gym_lower": "Низ",
                "pool": "Бассейн",
                "other": "Другое"
            }.get(w["workout_type"], w["workout_type"])
            text += f"• {type_name}: {w['duration_min']} мин, самочувствие {w['energy_level']}/10, ~{w['calories_burned']} ккал\n"
            total_burned_today += w["calories_burned"] or 0
        text += f"Всего сожжено сегодня: ~{total_burned_today} ккал\n\n"
    else:
        text += "Тренировок сегодня пока нет.\n\n"

    if user:
        text += (
            f"<b>Питание сегодня:</b>\n"
            f"🔥 {today_meals['cal']:.0f} / {user['calorie_goal']} ккал\n"
            f"🥩 {today_meals['prot']:.0f} / {user['protein_goal']} г\n"
            f"🥑 {today_meals['f']:.0f} / {user['fat_goal']} г\n"
            f"🍞 {today_meals['c']:.0f} / {user['carb_goal']} г\n\n"
        )

    if week_stats and week_stats["cnt"]:
        text += (
            f"<b>За последние 7 дней:</b>\n"
            f"Тренировок: {week_stats['cnt']}\n"
            f"Средний запас сил: {week_stats['avg_energy']:.1f}/10\n"
            f"Примерный расход на тренировках: ~{week_stats['total_burned'] or 0} ккал\n"
        )

    await message.answer(text, reply_markup=main_menu(), parse_mode="HTML")
