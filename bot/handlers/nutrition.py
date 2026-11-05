from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from datetime import date

from db.database import get_db
from bot.states.states import MealStates
from bot.keyboards.keyboards import main_menu, cancel_kb

router = Router()


@router.message(F.text == "🍽 Питание")
async def start_meal(message: Message, state: FSMContext):
    await state.set_state(MealStates.description)
    await message.answer(
        "Что ты ела? Опиши блюда.\n\n"
        "Можно так:\n"
        "<code>Овсянка 60г, банан, творог 150г 5%</code>\n"
        "<code>Куриная грудка 150г, рис 80г, овощи</code>\n\n"
        "После описания я попрошу ввести калории и БЖУ.",
        parse_mode="HTML",
        reply_markup=cancel_kb()
    )


@router.message(MealStates.description)
async def process_meal_description(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено", reply_markup=main_menu())
        return

    await state.update_data(description=message.text)
    await state.set_state(MealStates.macros)
    await message.answer(
        "Теперь введи КБЖУ примерно в формате:\n"
        "<code>калории белок жиры углеводы</code>\n\n"
        "Пример:\n"
        "<code>450 35 12 40</code>",
        parse_mode="HTML"
    )


@router.message(MealStates.macros)
async def process_macros(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено", reply_markup=main_menu())
        return

    parts = message.text.replace(",", ".").split()
    try:
        calories = float(parts[0]) if len(parts) > 0 else 0
        protein = float(parts[1]) if len(parts) > 1 else 0
        fat = float(parts[2]) if len(parts) > 2 else 0
        carbs = float(parts[3]) if len(parts) > 3 else 0
    except ValueError:
        await message.answer("Не получилось распознать. Попробуй ещё раз в формате: 450 35 12 40")
        return

    data = await state.get_data()
    description = data.get("description", "")
    today = date.today().isoformat()
    user_id = message.from_user.id

    async with await get_db() as db:
        await db.execute(
            """
            INSERT INTO meals (user_id, date, description, calories, protein, fat, carbs)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, today, description, calories, protein, fat, carbs)
        )
        await db.commit()

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
            day_total = await cursor.fetchone()

        async with db.execute(
            "SELECT calorie_goal, protein_goal, fat_goal, carb_goal FROM users WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            goals = await cursor.fetchone()

    await state.clear()

    text = (
        f"✅ Запись добавлена!\n\n"
        f"<b>{description}</b>\n"
        f"🔥 {calories} ккал | 🥩 {protein}г | 🥑 {fat}г | 🍞 {carbs}г\n\n"
        f"<b>Итого за сегодня:</b>\n"
        f"🔥 {day_total['cal']:.0f} / {goals['calorie_goal'] if goals else '?'} ккал\n"
        f"🥩 {day_total['prot']:.0f} / {goals['protein_goal'] if goals else '?'} г белка\n"
        f"🥑 {day_total['f']:.0f} / {goals['fat_goal'] if goals else '?'} г жиров\n"
        f"🍞 {day_total['c']:.0f} / {goals['carb_goal'] if goals else '?'} г углеводов"
    )
    await message.answer(text, reply_markup=main_menu(), parse_mode="HTML")
