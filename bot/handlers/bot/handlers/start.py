from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from db.database import get_db
from bot.keyboards.keyboards import main_menu
from utils.calculations import mifflin_st_jeor, calculate_tdee, calculate_macros

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id

    async with await get_db() as db:
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            user = await cursor.fetchone()

    if user:
        await message.answer(
            f"С возвращением, {message.from_user.first_name}!\n\n"
            "Я твой дневник тренировок и питания.\n"
            "Выбери действие в меню 👇",
            reply_markup=main_menu()
        )
    else:
        weight = 56.0
        height = 165.0
        age = 45
        gender = "female"

        bmr = mifflin_st_jeor(weight, height, age, gender)
        tdee = calculate_tdee(bmr, "moderate")
        macros = calculate_macros(tdee, "strength_endurance_hypertrophy")

        protein = round(macros["protein_per_kg"] * weight)
        fat = round((macros["calories"] * macros["fat_percent"]) / 9)
        carbs = round((macros["calories"] - protein * 4 - fat * 9) / 4)

        limitations = (
            "Плечо: боль при жиме на наклонной (особенно в нижней точке, когда гантели на уровне груди). "
            "Голеностоп: очень слабая мобильность, пятки отрываются в приседе, проблемы с внутренней ротацией голеностопа и внешней ротацией бедра. "
            "Присед выполняется с клиньями + обязательная работа над мобильностью."
        )

        async with await get_db() as db:
            await db.execute(
                """
                INSERT INTO users (
                    user_id, full_name, gender, age, height, weight,
                    goal, limitations, calorie_goal, protein_goal, fat_goal, carb_goal
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    message.from_user.full_name,
                    gender,
                    age,
                    height,
                    weight,
                    "strength_endurance_hypertrophy",
                    limitations,
                    macros["calories"],
                    protein,
                    fat,
                    carbs,
                )
            )
            await db.commit()

        text = (
            f"Привет, {message.from_user.first_name}! 👋\n\n"
            "Я создал тебе профиль на основе данных, которые ты указала:\n\n"
            f"• Пол: женский\n"
            f"• Возраст: 45 лет\n"
            f"• Рост: 165 см\n"
            f"• Вес: 56 кг\n"
            f"• Цель: сила + выносливость + набор мышц\n\n"
            f"<b>Рекомендуемая норма КБЖУ:</b>\n"
            f"🔥 Калории: ~{macros['calories']} ккал\n"
            f"🥩 Белок: {protein} г\n"
            f"🥑 Жиры: {fat} г\n"
            f"🍞 Углеводы: {carbs} г\n\n"
            "<b>Учтённые ограничения:</b>\n"
            "• Проблемы с плечом (особенно жим на наклонной)\n"
            "• Слабая мобильность голеностопа + внешняя ротация бедра\n\n"
            "Теперь можешь записывать тренировки и питание.\n"
            "Используй меню внизу 👇"
        )
        await message.answer(text, reply_markup=main_menu(), parse_mode="HTML")


@router.message(Command("help"))
@router.message(F.text == "❓ Помощь")
async def cmd_help(message: Message):
    text = (
        "<b>Как пользоваться ботом:</b>\n\n"
        "🏋️ <b>Тренировка</b> — записать тренировку (зал верх/низ или бассейн)\n"
        "🍽 <b>Питание</b> — записать еду и КБЖУ\n"
        "📊 <b>Статистика</b> — посмотреть итоги за день/неделю\n"
        "📋 <b>Программы</b> — текущие и прошлые программы\n"
        "💡 <b>Рекомендации</b> — советы по прогрессии и восстановлению\n"
        "👤 <b>Профиль</b> — твои данные и норма КБЖУ\n\n"
        "<b>Быстрый ввод тренировки:</b>\n"
        "Можно писать прямо текстом, например:\n"
        "<code>Жим лэндмайн 25 8 3</code>\n"
        "<code>Присед 25 8 4</code>\n"
        "<code>Кроль 1600 50</code>\n"
    )
    await message.answer(text, parse_mode="HTML")
