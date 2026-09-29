"""Обработчики Telegram: анкета, фото еды, дневник, вес."""
import json
import logging
from datetime import datetime, timedelta, timezone

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from .config import Config
from .db import Database
from .nutrition import daily_targets, meal_totals
from .texts import lang_of, t
from .vision import FoodRecognizer, RecognitionRefused

log = logging.getLogger(__name__)
router = Router()

FACTOR_STEP = 0.25
FACTOR_MIN, FACTOR_MAX = 0.25, 3.0


class Onboarding(StatesGroup):
    sex = State()
    age = State()
    height = State()
    weight = State()
    goal_weight = State()
    activity = State()


class WeightLog(StatesGroup):
    value = State()


def local_day(tz_offset_min: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(minutes=tz_offset_min)).date().isoformat()


def parse_number(text: str | None, lo: float, hi: float) -> float | None:
    try:
        value = float((text or "").replace(",", ".").strip())
    except ValueError:
        return None
    return value if lo <= value <= hi else None


def has_access(user, cfg: Config) -> bool:
    if user["paid_until"] and datetime.fromisoformat(user["paid_until"]) > datetime.now(timezone.utc):
        return True
    return user["photos_used"] < cfg.free_photos


def kb(rows: list[list[tuple[str, str]]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=txt, callback_data=data) for txt, data in row] for row in rows]
    )


# ---------- анкета ----------

@router.message(CommandStart())
async def start(message: Message, state: FSMContext, db: Database):
    user = await db.ensure_user(message.from_user.id, lang_of(message.from_user.language_code))
    lang = user["lang"]
    await state.clear()
    await state.set_state(Onboarding.sex)
    await message.answer(
        t(lang, "welcome"),
        reply_markup=kb([[(t(lang, "sex_female"), "sex:female"), (t(lang, "sex_male"), "sex:male")]]),
    )


@router.callback_query(Onboarding.sex, F.data.startswith("sex:"))
async def on_sex(call: CallbackQuery, state: FSMContext, db: Database):
    lang = (await db.get_user(call.from_user.id))["lang"]
    await state.update_data(sex=call.data.split(":")[1])
    await state.set_state(Onboarding.age)
    await call.message.edit_reply_markup()
    await call.message.answer(t(lang, "ask_age"))
    await call.answer()


async def _ask_number(message: Message, state: FSMContext, db: Database, field: str,
                      lo: float, hi: float, example: str, next_state: State | None, next_key: str | None):
    lang = (await db.get_user(message.from_user.id))["lang"]
    value = parse_number(message.text, lo, hi)
    if value is None:
        await message.answer(t(lang, "bad_number", example=example))
        return None
    await state.update_data(**{field: value})
    if next_state:
        await state.set_state(next_state)
        await message.answer(t(lang, next_key))
    return lang


@router.message(Onboarding.age)
async def on_age(message: Message, state: FSMContext, db: Database):
    await _ask_number(message, state, db, "age", 14, 90, "32", Onboarding.height, "ask_height")


@router.message(Onboarding.height)
async def on_height(message: Message, state: FSMContext, db: Database):
    await _ask_number(message, state, db, "height", 120, 230, "168", Onboarding.weight, "ask_weight")


@router.message(Onboarding.weight)
async def on_weight(message: Message, state: FSMContext, db: Database):
    await _ask_number(message, state, db, "weight", 35, 300, "74.5", Onboarding.goal_weight, "ask_goal_weight")


@router.message(Onboarding.goal_weight)
async def on_goal_weight(message: Message, state: FSMContext, db: Database):
    lang = await _ask_number(message, state, db, "goal_weight", 35, 300, "65", None, None)
    if lang is None:
        return
    await state.set_state(Onboarding.activity)
    await message.answer(
        t(lang, "ask_activity"),
        reply_markup=kb([[(t(lang, f"act_{a}"), f"act:{a}")] for a in ("low", "light", "medium", "high")]),
    )


@router.callback_query(Onboarding.activity, F.data.startswith("act:"))
async def on_activity(call: CallbackQuery, state: FSMContext, db: Database):
    data = await state.get_data()
    activity = call.data.split(":")[1]
    diff = data["goal_weight"] - data["weight"]
    goal = "keep" if abs(diff) < 1 else ("lose" if diff < 0 else "gain")
    targets = daily_targets(data["sex"], data["weight"], data["height"], int(data["age"]), activity, goal)
    await db.save_profile(
        call.from_user.id, sex=data["sex"], age=int(data["age"]), height=data["height"],
        weight=data["weight"], goal_weight=data["goal_weight"], activity=activity, goal=goal,
        kcal=targets.kcal, protein=targets.protein, fat=targets.fat, carbs=targets.carbs,
    )
    user = await db.get_user(call.from_user.id)
    await db.add_weight(user["id"], local_day(user["tz_offset"]), data["weight"])
    await state.clear()
    lang = user["lang"]
    await call.message.edit_reply_markup()
    await call.message.answer(t(
        lang, "plan", kcal=targets.kcal, protein=targets.protein, fat=targets.fat, carbs=targets.carbs,
        weight=data["weight"], goal_weight=data["goal_weight"],
    ))
    await call.answer()


# ---------- фото еды ----------

def render_meal(lang: str, dish: str, items: list[dict], factor: float, comment: str,
                day_kcal: float, target: int) -> str:
    lines = []
    for it in items:
        grams = it["grams"] * factor
        lines.append(t(
            lang, "item", name=it["name"], grams=round(grams),
            kcal=round(it["kcal_per_100g"] * grams / 100),
            mark=t(lang, "low_conf") if it["confidence"] == "low" else "",
        ))
    total = meal_totals(items, factor)
    return t(
        lang, "meal", dish=dish, items="\n".join(lines),
        kcal=round(total.kcal), protein=round(total.protein), fat=round(total.fat), carbs=round(total.carbs),
        factor_note=t(lang, "factor_note", factor=f"{factor:g}") + "\n" if factor != 1 else "",
        comment=comment, day_kcal=round(day_kcal), target=target,
    )


def meal_kb(lang: str, meal_id: int) -> InlineKeyboardMarkup:
    return kb([
        [(t(lang, "btn_less"), f"m:less:{meal_id}"), (t(lang, "btn_more"), f"m:more:{meal_id}")],
        [(t(lang, "btn_delete"), f"m:del:{meal_id}")],
    ])


async def day_kcal(db: Database, user) -> float:
    meals = await db.meals_for_day(user["id"], local_day(user["tz_offset"]))
    return sum(meal_totals(json.loads(m["items"]), m["factor"]).kcal for m in meals)


@router.message(F.photo)
async def on_photo(message: Message, bot: Bot, db: Database, cfg: Config, recognizer: FoodRecognizer):
    user = await db.ensure_user(message.from_user.id, lang_of(message.from_user.language_code))
    lang = user["lang"]
    if not user["kcal"]:
        await message.answer(t(lang, "need_profile"))
        return
    if not has_access(user, cfg):
        await message.answer(t(lang, "paywall"))
        return

    status = await message.answer(t(lang, "analyzing"))
    photo = await bot.download(message.photo[-1])
    try:
        analysis = await recognizer.analyze(photo.read(), lang, message.caption)
    except RecognitionRefused:
        await status.edit_text(t(lang, "refused"))
        return
    except Exception:
        log.exception("food recognition failed")
        await status.edit_text(t(lang, "error"))
        return

    if not analysis.is_food or not analysis.items:
        await status.edit_text(t(lang, "not_food"))
        return

    items = [i.model_dump() for i in analysis.items]
    meal_id = await db.add_meal(user["id"], local_day(user["tz_offset"]), analysis.dish, items)
    await db.use_photo(user["id"])
    # комментарий храним только в сообщении — в дневнике он не нужен
    await status.edit_text(
        render_meal(lang, analysis.dish, items, 1.0, analysis.comment, await day_kcal(db, user), user["kcal"]),
        reply_markup=meal_kb(lang, meal_id),
    )


@router.callback_query(F.data.startswith("m:"))
async def on_meal_button(call: CallbackQuery, db: Database):
    _, action, meal_id = call.data.split(":")
    user = await db.get_user(call.from_user.id)
    lang = user["lang"]
    meal = await db.get_meal(int(meal_id), user["id"])
    if meal is None:
        await call.answer()
        return
    if action == "del":
        await db.delete_meal(meal["id"], user["id"])
        await call.message.edit_text(t(lang, "deleted"))
        await call.answer()
        return

    step = -FACTOR_STEP if action == "less" else FACTOR_STEP
    factor = min(max(meal["factor"] + step, FACTOR_MIN), FACTOR_MAX)
    await db.set_meal_factor(meal["id"], user["id"], factor)
    # последняя строка-совет из исходного сообщения сохраняется при пересчёте
    comment = next((ln[2:] for ln in (call.message.text or "").splitlines() if ln.startswith("💡 ")), "")
    await call.message.edit_text(
        render_meal(lang, meal["dish"], json.loads(meal["items"]), factor, comment,
                    await day_kcal(db, user), user["kcal"]),
        reply_markup=meal_kb(lang, meal["id"]),
    )
    await call.answer()


# ---------- итоги дня и вес ----------

@router.message(Command("today"))
async def today(message: Message, db: Database):
    user = await db.ensure_user(message.from_user.id, lang_of(message.from_user.language_code))
    lang = user["lang"]
    if not user["kcal"]:
        await message.answer(t(lang, "need_profile"))
        return
    meals = await db.meals_for_day(user["id"], local_day(user["tz_offset"]))
    if not meals:
        await message.answer(t(lang, "today_empty"))
        return
    lines, total = [], None
    for m in meals:
        mt = meal_totals(json.loads(m["items"]), m["factor"])
        total = mt if total is None else total + mt
        lines.append(t(lang, "today_meal", dish=m["dish"], kcal=round(mt.kcal)))
    left = user["kcal"] - total.kcal
    verdict = (t(lang, "verdict_left", left=round(left)) if left >= 0
               else t(lang, "verdict_over", over=round(-left)))
    await message.answer(t(
        lang, "today", meals="\n".join(lines), kcal=round(total.kcal), target=user["kcal"],
        protein=round(total.protein), fat=round(total.fat), carbs=round(total.carbs),
        t_protein=user["protein"], t_fat=user["fat"], t_carbs=user["carbs"], verdict=verdict,
    ))


@router.message(Command("weight"))
async def weight_cmd(message: Message, state: FSMContext, db: Database):
    user = await db.ensure_user(message.from_user.id, lang_of(message.from_user.language_code))
    if not user["kcal"]:
        await message.answer(t(user["lang"], "need_profile"))
        return
    await state.set_state(WeightLog.value)
    await message.answer(t(user["lang"], "ask_new_weight"))


@router.message(WeightLog.value)
async def weight_value(message: Message, state: FSMContext, db: Database):
    user = await db.get_user(message.from_user.id)
    lang = user["lang"]
    value = parse_number(message.text, 35, 300)
    if value is None:
        await message.answer(t(lang, "bad_number", example="72.4"))
        return
    history = await db.weight_history(user["id"], limit=1)
    await db.add_weight(user["id"], local_day(user["tz_offset"]), value)
    await state.clear()
    if history:
        diff = round(value - history[0]["weight"], 1)
        trend = (t(lang, "trend_down", diff=-diff) if diff < 0
                 else t(lang, "trend_up", diff=diff) if diff > 0 else t(lang, "trend_same"))
    else:
        trend = ""
    await message.answer(t(lang, "weight_saved", weight=value, trend=trend,
                           left=round(abs(value - user["goal_weight"]), 1)))


@router.message(Command("help"))
async def help_cmd(message: Message, db: Database):
    user = await db.ensure_user(message.from_user.id, lang_of(message.from_user.language_code))
    await message.answer(t(user["lang"], "help"))
