from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import date

from db.database import get_db
from bot.states.states import WorkoutStates
from bot.keyboards.keyboards import (
    main_menu, workout_type_kb, energy_kb, confirm_kb, cancel_kb
)
from utils.calculations import estimate_calories_burned, get_progression_recommendation

router = Router()


@router.message(F.text == "🏋️ Тренировка")
async def start_workout(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Выбери тип тренировки:",
        reply_markup=workout_type_kb()
    )


@router.callback_query(F.data.startswith("wtype_"))
async def choose_workout_type(callback: CallbackQuery, state: FSMContext):
    wtype = callback.data.replace("wtype_", "")

    if wtype == "quick":
        await state.set_state(WorkoutStates.quick_input)
        await callback.message.edit_text(
            "⚡️ <b>Быстрый ввод</b>\n\n"
            "Напиши упражнения в свободной форме.\n"
            "Примеры:\n"
            "<code>Жим лэндмайн 25 8 3\n"
            "Тяга вертикальная 32 10 3\n"
            "Face pulls 16 12 3</code>\n\n"
            "Или для бассейна:\n"
            "<code>Кроль 1600 50</code>\n"
            "<code>Бассейн 45 минут средняя интенсивность</code>",
            parse_mode="HTML"
        )
        await callback.answer()
        return

    type_names = {
        "gym_upper": "Верх тела",
        "gym_lower": "Низ тела",
        "pool": "Бассейн",
        "other": "Другое"
    }

    await state.update_data(workout_type=wtype, exercises=[])
    await state.set_state(WorkoutStates.duration)

    await callback.message.edit_text(
        f"Тип: <b>{type_names.get(wtype, wtype)}</b>\n\n"
        "Сколько минут длилась тренировка? (просто число)",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(WorkoutStates.duration)
async def process_duration(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Введи число минут, например: 55")
        return

    duration = int(message.text)
    await state.update_data(duration=duration)
    await state.set_state(WorkoutStates.energy)

    await message.answer(
        "Оцени запас сил / самочувствие после тренировки (1–10):",
        reply_markup=energy_kb()
    )


@router.callback_query(F.data.startswith("energy_"))
async def process_energy(callback: CallbackQuery, state: FSMContext):
    energy = int(callback.data.replace("energy_", ""))
    await state.update_data(energy=energy)

    data = await state.get_data()

    if data.get("workout_type") == "pool":
        await save_workout(callback.from_user.id, data, callback.message)
        await state.clear()
        await callback.answer()
        return

    await state.set_state(WorkoutStates.add_exercise)
    await callback.message.edit_text(
        f"Самочувствие: {energy}/10\n\n"
        "Теперь добавим упражнения.\n"
        "Напиши название первого упражнения\n"
        "(или нажми «Готово», если хочешь закончить):"
    )
    await callback.answer()


@router.message(WorkoutStates.add_exercise)
async def add_exercise_name(message: Message, state: FSMContext):
    if message.text.lower() in ("готово", "готов", "всё", "все", "стоп"):
        data = await state.get_data()
        await save_workout(message.from_user.id, data, message)
        await state.clear()
        return

    await state.update_data(current_exercise={"name": message.text})
    await state.set_state(WorkoutStates.exercise_sets)
    await message.answer("Количество подходов (число):")


@router.message(WorkoutStates.exercise_sets)
async def process_sets(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Введи число подходов")
        return

    data = await state.get_data()
    current = data["current_exercise"]
    current["sets"] = int(message.text)
    await state.update_data(current_exercise=current)
    await state.set_state(WorkoutStates.exercise_reps)
    await message.answer("Повторения (например: 8 или 8-10):")


@router.message(WorkoutStates.exercise_reps)
async def process_reps(message: Message, state: FSMContext):
    data = await state.get_data()
    current = data["current_exercise"]
    current["reps"] = message.text.strip()
    await state.update_data(current_exercise=current)
    await state.set_state(WorkoutStates.exercise_weight)
    await message.answer("Вес (кг). Если без веса — напиши 0:")


@router.message(WorkoutStates.exercise_weight)
async def process_weight(message: Message, state: FSMContext):
    try:
        weight = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Введи число (можно с точкой)")
        return

    data = await state.get_data()
    current = data["current_exercise"]
    current["weight"] = weight

    exercises = data.get("exercises", [])
    exercises.append(current)
    await state.update_data(exercises=exercises, current_exercise={})

    async with await get_db() as db:
        async with db.execute(
            "SELECT limitations FROM users WHERE user_id = ?",
            (message.from_user.id,)
        ) as cursor:
            user = await cursor.fetchone()
            limitations = user["limitations"] if user else ""

    rec = get_progression_recommendation(
        last_weight=weight,
        last_reps=current["reps"],
        energy=data.get("energy", 7),
        exercise_name=current["name"],
        limitations=limitations
    )

    await state.set_state(WorkoutStates.add_exercise)
    await message.answer(
        f"✅ Добавлено: <b>{current['name']}</b>\n"
        f"{current['sets']} × {current['reps']} × {weight} кг\n\n"
        f"{rec}\n\n"
        "Следующее упражнение или напиши <b>Готово</b>:",
        parse_mode="HTML"
    )


async def save_workout(user_id: int, data: dict, message_obj):
    workout_type = data.get("workout_type", "other")
    duration = data.get("duration", 45)
    energy = data.get("energy", 7)
    exercises = data.get("exercises", [])
    today = date.today().isoformat()

    async with await get_db() as db:
        async with db.execute(
            "SELECT weight FROM users WHERE user_id = ?", (user_id,)
        ) as cursor:
            user = await cursor.fetchone()
            weight = user["weight"] if user else 56.0

        intensity = "moderate"
        if energy >= 8:
            intensity = "hard"
        elif energy <= 5:
            intensity = "light"

        calories = estimate_calories_burned(weight, duration, workout_type, intensity)

        cursor = await db.execute(
            """
            INSERT INTO workouts (user_id, date, workout_type, duration_min, energy_level, calories_burned)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, today, workout_type, duration, energy, calories)
        )
        workout_id = cursor.lastrowid

        for ex in exercises:
            await db.execute(
                """
                INSERT INTO exercises (workout_id, name, sets, reps, weight)
                VALUES (?, ?, ?, ?, ?)
                """,
                (workout_id, ex["name"], ex.get("sets"), ex.get("reps"), ex.get("weight", 0))
            )

        await db.commit()

    type_names = {
        "gym_upper": "Верх тела",
        "gym_lower": "Низ тела",
        "pool": "Бассейн",
        "other": "Другое"
    }

    text = (
        f"✅ <b>Тренировка сохранена!</b>\n\n"
        f"Тип: {type_names.get(workout_type, workout_type)}\n"
        f"Длительность: {duration} мин\n"
        f"Самочувствие: {energy}/10\n"
        f"Примерный расход: ~{calories} ккал\n"
    )

    if exercises:
        text += "\n<b>Упражнения:</b>\n"
        for ex in exercises:
            text += f"• {ex['name']}: {ex.get('sets')}×{ex.get('reps')} × {ex.get('weight')} кг\n"

    if hasattr(message_obj, "answer"):
        await message_obj.answer(text, reply_markup=main_menu(), parse_mode="HTML")
    else:
        await message_obj.edit_text(text, parse_mode="HTML")
        await message_obj.answer("Главное меню:", reply_markup=main_menu())


@router.message(WorkoutStates.quick_input)
async def process_quick_input(message: Message, state: FSMContext):
    text = message.text.strip()
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    exercises = []
    duration = 50
    workout_type = "gym_upper"
    energy = 7

    for line in lines:
        lower = line.lower()
        if "кроль" in lower or "бассейн" in lower or "плав" in lower:
            workout_type = "pool"
            parts = line.replace(",", ".").split()
            for i, p in enumerate(parts):
                if p.replace(".", "").isdigit():
                    num = float(p)
                    if num > 20:
                        duration = int(num)
            continue

        parts = line.split()
        if len(parts) >= 3:
            try:
                nums = []
                name_parts = []
                for p in reversed(parts):
                    try:
                        nums.append(float(p.replace(",", ".")))
                    except ValueError:
                        name_parts.insert(0, p)
                        break
                name_parts = parts[:len(parts) - len(nums)]
                name = " ".join(name_parts) if name_parts else "Упражнение"

                weight = nums[0] if nums else 0
                reps = str(int(nums[1])) if len(nums) > 1 else "8"
                sets = int(nums[2]) if len(nums) > 2 else 3

                exercises.append({
                    "name": name,
                    "sets": sets,
                    "reps": reps,
                    "weight": weight
                })
            except Exception:
                exercises.append({"name": line, "sets": 3, "reps": "8", "weight": 0})

    data = {
        "workout_type": workout_type,
        "duration": duration,
        "energy": energy,
        "exercises": exercises
    }

    await save_workout(message.from_user.id, data, message)
    await state.clear()
