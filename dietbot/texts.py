"""Тексты интерфейса на русском и английском."""

TEXTS = {
    "ru": {
        "welcome": (
            "Привет! Я твой ИИ-диетолог 🥗\n\n"
            "Фотографируй еду — я посчитаю калории и БЖУ, веду дневник и помогаю "
            "дойти до цели по весу.\n\nДавай настроим план. Твой пол?"
        ),
        "sex_female": "Женский", "sex_male": "Мужской",
        "ask_age": "Сколько тебе лет?",
        "ask_height": "Рост в сантиметрах?",
        "ask_weight": "Текущий вес в килограммах?",
        "ask_goal_weight": "Какой вес хочешь? (кг)",
        "ask_activity": "Насколько ты активен?",
        "act_low": "Почти не двигаюсь", "act_light": "1–3 тренировки в неделю",
        "act_medium": "3–5 тренировок", "act_high": "Каждый день / физ. труд",
        "bad_number": "Не понял число. Напиши, например: {example}",
        "plan": (
            "Готово! Твой план на день:\n\n"
            "🔥 {kcal} ккал\n🥩 Белки {protein} г\n🧈 Жиры {fat} г\n🍞 Углеводы {carbs} г\n\n"
            "Цель: {weight} → {goal_weight} кг.\n\n"
            "Теперь просто присылай фото каждого приёма пищи. "
            "Можно добавить подпись, например «макароны 200 г» — так точнее."
        ),
        "need_profile": "Сначала настроим план — нажми /start",
        "analyzing": "Смотрю, что на тарелке… 🔍",
        "not_food": "Не вижу на фото еды. Пришли, пожалуйста, фото блюда.",
        "refused": "Не получилось распознать это фото. Попробуй другое.",
        "error": "Что-то пошло не так, попробуй ещё раз через минуту.",
        "meal": "🍽 {dish}\n\n{items}\n\nИтого: {kcal} ккал · Б {protein} · Ж {fat} · У {carbs}\n{factor_note}\n💡 {comment}\n\nЗа сегодня: {day_kcal} из {target} ккал",
        "item": "• {name} — {grams} г, {kcal} ккал{mark}",
        "low_conf": " (примерно)",
        "factor_note": "Порция скорректирована: ×{factor}",
        "btn_less": "Порция меньше", "btn_more": "Порция больше", "btn_delete": "Удалить",
        "deleted": "Удалил из дневника.",
        "today_empty": "Сегодня ещё ничего не записано. Пришли фото еды 📸",
        "today": "📊 Сегодня\n\n{meals}\n\nВсего: {kcal} из {target} ккал\nБ {protein}/{t_protein} · Ж {fat}/{t_fat} · У {carbs}/{t_carbs}\n\n{verdict}",
        "today_meal": "• {dish} — {kcal} ккал",
        "verdict_left": "Осталось {left} ккал — хватит на полноценный приём пищи.",
        "verdict_over": "Перебор на {over} ккал. Не страшно: завтра чуть легче ужин.",
        "ask_new_weight": "Напиши сегодняшний вес в кг, например 72.4",
        "weight_saved": "Записал {weight} кг. {trend}\nДо цели: {left} кг.",
        "trend_down": "С прошлого взвешивания −{diff} кг 👏",
        "trend_up": "С прошлого взвешивания +{diff} кг. Бывает — смотрим на тренд за неделю.",
        "trend_same": "Вес стабилен.",
        "paywall": (
            "Бесплатные распознавания закончились.\n\n"
            "Подписка откроет безлимитные фото, дневник, план и еженедельный разбор. "
            "Оплата появится совсем скоро."
        ),
        "help": "/today — итоги дня\n/weight — записать вес\n/start — пересчитать план\n\nИ просто присылай фото еды 📸",
    },
    "en": {
        "welcome": (
            "Hi! I'm your AI nutritionist 🥗\n\n"
            "Snap your food — I'll count calories and macros, keep your food diary "
            "and help you reach your weight goal.\n\nLet's set up your plan. Your sex?"
        ),
        "sex_female": "Female", "sex_male": "Male",
        "ask_age": "How old are you?",
        "ask_height": "Height in cm?",
        "ask_weight": "Current weight in kg?",
        "ask_goal_weight": "Target weight in kg?",
        "ask_activity": "How active are you?",
        "act_low": "Mostly sitting", "act_light": "1–3 workouts a week",
        "act_medium": "3–5 workouts", "act_high": "Daily / physical job",
        "bad_number": "I didn't get the number. Try something like: {example}",
        "plan": (
            "Done! Your daily plan:\n\n"
            "🔥 {kcal} kcal\n🥩 Protein {protein} g\n🧈 Fat {fat} g\n🍞 Carbs {carbs} g\n\n"
            "Goal: {weight} → {goal_weight} kg.\n\n"
            "Now just send a photo of every meal. "
            "Add a caption like “pasta 200 g” for better accuracy."
        ),
        "need_profile": "Let's set up your plan first — tap /start",
        "analyzing": "Looking at your plate… 🔍",
        "not_food": "I don't see any food here. Please send a photo of your meal.",
        "refused": "I couldn't analyze this photo. Try another one.",
        "error": "Something went wrong, please try again in a minute.",
        "meal": "🍽 {dish}\n\n{items}\n\nTotal: {kcal} kcal · P {protein} · F {fat} · C {carbs}\n{factor_note}\n💡 {comment}\n\nToday: {day_kcal} of {target} kcal",
        "item": "• {name} — {grams} g, {kcal} kcal{mark}",
        "low_conf": " (approx.)",
        "factor_note": "Portion adjusted: ×{factor}",
        "btn_less": "Smaller portion", "btn_more": "Bigger portion", "btn_delete": "Delete",
        "deleted": "Removed from your diary.",
        "today_empty": "Nothing logged today yet. Send a food photo 📸",
        "today": "📊 Today\n\n{meals}\n\nTotal: {kcal} of {target} kcal\nP {protein}/{t_protein} · F {fat}/{t_fat} · C {carbs}/{t_carbs}\n\n{verdict}",
        "today_meal": "• {dish} — {kcal} kcal",
        "verdict_left": "{left} kcal left — enough for a proper meal.",
        "verdict_over": "{over} kcal over. No big deal: go lighter at dinner tomorrow.",
        "ask_new_weight": "Send today's weight in kg, e.g. 72.4",
        "weight_saved": "Saved {weight} kg. {trend}\nTo goal: {left} kg.",
        "trend_down": "−{diff} kg since last weigh-in 👏",
        "trend_up": "+{diff} kg since last weigh-in. It happens — watch the weekly trend.",
        "trend_same": "Weight is stable.",
        "paywall": (
            "You've used all free photo analyses.\n\n"
            "A subscription unlocks unlimited photos, the diary, your plan and weekly reviews. "
            "Payments are coming very soon."
        ),
        "help": "/today — daily summary\n/weight — log weight\n/start — recalculate plan\n\nAnd just send food photos 📸",
    },
}


def lang_of(language_code: str | None) -> str:
    """Русский для пользователей из RU/CIS-локалей, английский для остальных."""
    if language_code and language_code.split("-")[0] in {"ru", "uk", "be", "kk", "uz", "ky"}:
        return "ru"
    return "en"


def t(lang: str, key: str, **kwargs) -> str:
    return TEXTS[lang][key].format(**kwargs)
