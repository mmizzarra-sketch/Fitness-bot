from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


def main_menu():
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="🏋️ Тренировка"),
        KeyboardButton(text="🍽 Питание")
    )
    builder.row(
        KeyboardButton(text="📊 Статистика"),
        KeyboardButton(text="📋 Программы")
    )
    builder.row(
        KeyboardButton(text="👤 Профиль"),
        KeyboardButton(text="⚙️ Настройки")
    )
    builder.row(KeyboardButton(text="💡 Рекомендации"))
    return builder.as_markup(resize_keyboard=True)


def workout_type_kb():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💪 Верх тела", callback_data="wtype_gym_upper"),
        InlineKeyboardButton(text="🦵 Низ тела", callback_data="wtype_gym_lower")
    )
    builder.row(
        InlineKeyboardButton(text="🏊 Бассейн", callback_data="wtype_pool"),
        InlineKeyboardButton(text="🔄 Другое", callback_data="wtype_other")
    )
    builder.row(InlineKeyboardButton(text="⚡️ Быстрый ввод", callback_data="wtype_quick"))
    return builder.as_markup()


def energy_kb():
    builder = InlineKeyboardBuilder()
    for i in range(1, 11):
        builder.add(InlineKeyboardButton(text=str(i), callback_data=f"energy_{i}"))
    builder.adjust(5)
    return builder.as_markup()


def confirm_kb(prefix: str = "confirm"):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Сохранить", callback_data=f"{prefix}_yes"),
        InlineKeyboardButton(text="❌ Отмена", callback_data=f"{prefix}_no")
    )
    return builder.as_markup()


def profile_kb():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✏️ Изменить вес", callback_data="edit_weight"))
    builder.row(InlineKeyboardButton(text="✏️ Изменить ограничения", callback_data="edit_limitations"))
    builder.row(InlineKeyboardButton(text="📊 Пересчитать КБЖУ", callback_data="recalc_macros"))
    return builder.as_markup()


def yes_no_kb():
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="Да"), KeyboardButton(text="Нет"))
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def cancel_kb():
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="❌ Отмена"))
    return builder.as_markup(resize_keyboard=True)
