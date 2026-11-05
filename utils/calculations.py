"""
Расчёты калорий, КБЖУ и рекомендации.
"""

def mifflin_st_jeor(weight: float, height: float, age: int, gender: str = "female") -> float:
    """Базовый метаболизм (BMR) по формуле Миффлина-Сен Жеора."""
    if gender == "male":
        return 10 * weight + 6.25 * height - 5 * age + 5
    return 10 * weight + 6.25 * height - 5 * age - 161


def calculate_tdee(bmr: float, activity_level: str = "moderate") -> float:
    multipliers = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "very_active": 1.9,
    }
    return bmr * multipliers.get(activity_level, 1.55)


def calculate_macros(tdee: float, goal: str = "hypertrophy") -> dict:
    if goal in ("hypertrophy", "strength_endurance_hypertrophy"):
        calories = tdee + 150
        protein = 1.8
        fat_percent = 0.28
    elif goal == "strength":
        calories = tdee + 100
        protein = 1.8
        fat_percent = 0.25
    else:
        calories = tdee - 200
        protein = 2.0
        fat_percent = 0.25

    return {
        "calories": round(calories),
        "protein_per_kg": protein,
        "fat_percent": fat_percent,
    }


def estimate_calories_burned(
    weight: float,
    duration_min: int,
    workout_type: str,
    intensity: str = "moderate"
) -> int:
    met_values = {
        "gym_upper": {"light": 3.5, "moderate": 5.0, "hard": 6.0},
        "gym_lower": {"light": 4.0, "moderate": 5.5, "hard": 6.5},
        "pool": {
            "light": 5.8,
            "moderate": 8.0,
            "hard": 10.0
        },
        "other": {"light": 3.5, "moderate": 5.0, "hard": 7.0},
    }

    mets = met_values.get(workout_type, met_values["other"])
    met = mets.get(intensity, 5.0)

    hours = duration_min / 60
    calories = met * weight * hours
    return round(calories)


def get_progression_recommendation(
    last_weight: float,
    last_reps: str,
    energy: int,
    exercise_name: str,
    limitations: str = ""
) -> str:
    name_lower = exercise_name.lower()
    limitations_lower = limitations.lower()

    if any(word in name_lower for word in ["жим", "press", "наклонн"]) and "плеч" in limitations_lower:
        return (
            "⚠️ Учитывая проблемы с плечом: не увеличивай вес в жимовых движениях, "
            "пока нет полной свободы в нижней точке. Лучше работай над техникой и объёмом "
            "в безопасном диапазоне (face pulls, внешняя ротация, тяги)."
        )

    if "присед" in name_lower and ("голеностоп" in limitations_lower or "пятк" in limitations_lower):
        return (
            "⚠️ Из-за ограниченной мобильности голеностопа продолжай приседать с клиньями. "
            "Прогрессируй очень аккуратно. Параллельно обязательно делай упражнения на "
            "мобильность голеностопа и внешнюю ротацию бедра."
        )

    if energy >= 8:
        return (
            f"Самочувствие хорошее ({energy}/10). Можно попробовать +1.25–2.5 кг "
            f"или +1 повтор в подходах при сохранении техники."
        )
    elif energy >= 6:
        return (
            f"Самочувствие среднее ({energy}/10). Оставь вес прежним или добавь "
            f"1 повтор. Не форсируй прогрессию."
        )
    else:
        return (
            f"Самочувствие низкое ({energy}/10). Лучше оставить нагрузку прежней "
            f"или даже слегка снизить. Приоритет — восстановление ЦНС и качество движения."
        )


def suggest_deload(workouts_last_14_days: int, avg_energy: float) -> str | None:
    if workouts_last_14_days >= 10 and avg_energy < 6.5:
        return (
            "📉 Похоже, накопилась усталость (много тренировок + невысокий запас сил). "
            "Рекомендую сделать разгрузочную неделю: снизить веса на 30–40% и объём на 40%, "
            "или заменить часть силовых на технику + бассейн лёгкой интенсивности."
        )
    return None
