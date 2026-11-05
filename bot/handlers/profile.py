from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from db.database import get_db
from bot.keyboards.keyboards import main_menu, profile_kb
from utils.calculations import mifflin_st_jeor, calculate_tdee, calculate_macros

router = Router()


@router.message(F.text == "👤 Профиль")
async def show_profile(message: Message):
    user_id = message.from_user.id

    async with await get_db() as db:
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            user = await cursor.fetchone()

    if not user:
        await message.answer("Профиль не найден. Нажми /start")
        return

    text = (
        f"<b>👤 Твой профиль</b>\n\n"
        f"Имя: {user['full_name']}\n"
        f"Пол: {'женский' if user['gender'] == 'female' else 'мужской'}\n"
        f"Возраст: {user['age']} лет\n"
        f"Рост: {user['height']} см\n"
        f"Вес: {user['weight']} кг\n"
        f"Цель: сила + выносливость + набор мышц\n\n"
        f"<b>Норма КБЖУ:</b>\n"
        f"🔥 Калории: {user['calorie_goal']} ккал\n"
        f"🥩 Белок: {user['protein_goal']} г\n"
        f"🥑 Жиры: {user['fat_goal']} г\n"
        f"🍞 Углеводы: {user['carb_goal']} г\n\n"
        f"<b>Ограничения:</b>\n{user['limitations'] or 'не указаны'}"
    )
    await message.answer(text, reply_markup=profile_kb(), parse_mode="HTML")


@router.callback_query(F.data == "recalc_macros")
async def recalc_macros(callback: CallbackQuery):
    user_id = callback.from_user.id

    async with await get_db() as db:
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            user = await cursor.fetchone()

        if not user:
            await callback.answer("Профиль не найден")
            return

        bmr = mifflin_st_jeor(user["weight"], user["height"], user["age"], user["gender"])
        tdee = calculate_tdee(bmr, "moderate")
        macros = calculate_macros(tdee, user["goal"])

        protein = round(macros["protein_per_kg"] * user["weight"])
        fat = round((macros["calories"] * macros["fat_percent"]) / 9)
        carbs = round((macros["calories"] - protein * 4 - fat * 9) / 4)

        await db.execute(
            """
            UPDATE users 
            SET calorie_goal = ?, protein_goal = ?, fat_goal = ?, carb_goal = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
            """,
            (macros["calories"], protein, fat, carbs, user_id)
        )
        await db.commit()

    await callback.message.edit_text(
        f"✅ Норма КБЖУ пересчитана:\n\n"
        f"🔥 Калории: {macros['calories']} ккал\n"
        f"🥩 Белок: {protein} г\n"
        f"🥑 Жиры: {fat} г\n"
        f"🍞 Углеводы: {carbs} г"
    )
    await callback.answer()
