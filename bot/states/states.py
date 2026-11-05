from aiogram.fsm.state import State, StatesGroup


class ProfileStates(StatesGroup):
    weight = State()
    height = State()
    age = State()
    limitations = State()
    confirm = State()


class WorkoutStates(StatesGroup):
    choose_type = State()
    date = State()
    duration = State()
    energy = State()
    add_exercise = State()
    exercise_name = State()
    exercise_sets = State()
    exercise_reps = State()
    exercise_weight = State()
    exercise_notes = State()
    quick_input = State()
    notes = State()
    confirm = State()


class MealStates(StatesGroup):
    date = State()
    description = State()
    macros = State()
    confirm = State()


class QuickLogStates(StatesGroup):
    waiting = State()
