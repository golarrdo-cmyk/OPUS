"""Расчёт суточной нормы калорий и БЖУ по формуле Миффлина — Сан Жеора."""
from dataclasses import dataclass

ACTIVITY_FACTORS = {
    "low": 1.2,       # сидячая работа, почти без спорта
    "light": 1.375,   # 1–3 тренировки в неделю
    "medium": 1.55,   # 3–5 тренировок
    "high": 1.725,    # тяжёлый труд или ежедневный спорт
}

GOAL_FACTORS = {"lose": 0.85, "keep": 1.0, "gain": 1.1}

# Ниже этих значений бот не опускает норму: это граница безопасного дефицита
MIN_KCAL = {"female": 1200, "male": 1500}


@dataclass(frozen=True)
class Targets:
    kcal: int
    protein: int
    fat: int
    carbs: int


def bmr(sex: str, weight_kg: float, height_cm: float, age: int) -> float:
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    return base + 5 if sex == "male" else base - 161


def daily_targets(
    sex: str, weight_kg: float, height_cm: float, age: int, activity: str, goal: str
) -> Targets:
    kcal = bmr(sex, weight_kg, height_cm, age) * ACTIVITY_FACTORS[activity] * GOAL_FACTORS[goal]
    kcal = max(kcal, MIN_KCAL[sex])
    protein = (1.6 if goal == "lose" else 1.4) * weight_kg
    fat = 0.9 * weight_kg
    carbs = max((kcal - protein * 4 - fat * 9) / 4, 0)
    return Targets(round(kcal), round(protein), round(fat), round(carbs))


@dataclass(frozen=True)
class Totals:
    kcal: float = 0
    protein: float = 0
    fat: float = 0
    carbs: float = 0

    def __add__(self, other: "Totals") -> "Totals":
        return Totals(
            self.kcal + other.kcal, self.protein + other.protein,
            self.fat + other.fat, self.carbs + other.carbs,
        )


def meal_totals(items: list[dict], factor: float = 1.0) -> Totals:
    """Сумма КБЖУ по компонентам блюда; factor — поправка порции пользователем."""
    total = Totals()
    for it in items:
        grams = it["grams"] * factor
        total += Totals(
            it["kcal_per_100g"] * grams / 100,
            it["protein_per_100g"] * grams / 100,
            it["fat_per_100g"] * grams / 100,
            it["carbs_per_100g"] * grams / 100,
        )
    return total
