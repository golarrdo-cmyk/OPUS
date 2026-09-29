"""Распознавание еды на фото через Claude.

Модель определяет блюда, оценивает вес каждой порции в граммах и даёт пищевую
ценность на 100 г. Калории порции бот считает сам: так пользователь может
поправить вес кнопками, и цифры пересчитаются без повторного запроса к модели.
"""
import base64
import json
from typing import Literal

import anthropic
from pydantic import BaseModel, Field


class FoodItem(BaseModel):
    name: str
    grams: float = Field(ge=0)
    kcal_per_100g: float = Field(ge=0)
    protein_per_100g: float = Field(ge=0)
    fat_per_100g: float = Field(ge=0)
    carbs_per_100g: float = Field(ge=0)
    confidence: Literal["high", "medium", "low"]


class FoodAnalysis(BaseModel):
    is_food: bool
    dish: str
    items: list[FoodItem]
    comment: str


class RecognitionRefused(Exception):
    pass


SCHEMA = {
    "type": "object",
    "properties": {
        "is_food": {"type": "boolean"},
        "dish": {"type": "string"},
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "grams": {"type": "number"},
                    "kcal_per_100g": {"type": "number"},
                    "protein_per_100g": {"type": "number"},
                    "fat_per_100g": {"type": "number"},
                    "carbs_per_100g": {"type": "number"},
                    "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                },
                "required": [
                    "name", "grams", "kcal_per_100g", "protein_per_100g",
                    "fat_per_100g", "carbs_per_100g", "confidence",
                ],
                "additionalProperties": False,
            },
        },
        "comment": {"type": "string"},
    },
    "required": ["is_food", "dish", "items", "comment"],
    "additionalProperties": False,
}

SYSTEM_PROMPT = """You are a nutritionist who estimates meals from photos.
For each separate component of the meal on the photo return its name, the estimated
portion weight in grams, and nutrition values per 100 g of the food as served (cooked,
with typical oil and sauce for that dish). Estimate portion size from plate, cutlery,
hands and packaging. Use standard reference values (USDA / Russian food composition tables).
If the user added a caption with weights or ingredients, trust it over your visual estimate.
If there is no food or drink on the photo, set is_food to false and leave items empty.
Write `dish`, item names and `comment` in the language: {lang}.
`comment` is one short friendly sentence: a practical nutrition tip about this meal,
no medical advice, no diagnoses, no mention of medications."""


def encode_image(data: bytes) -> dict:
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": "image/jpeg",
            "data": base64.standard_b64encode(data).decode("ascii"),
        },
    }


class FoodRecognizer:
    def __init__(self, model: str, client: anthropic.AsyncAnthropic | None = None):
        self.model = model
        self.client = client or anthropic.AsyncAnthropic()

    async def analyze(self, image: bytes, lang: str, caption: str | None = None) -> FoodAnalysis:
        user_text = f"User caption: {caption}" if caption else "Analyze this meal."
        output_config: dict = {"format": {"type": "json_schema", "schema": SCHEMA}}
        extra: dict = {}
        # Haiku 4.5 не принимает effort и серверный fallback
        if not self.model.startswith("claude-haiku"):
            output_config["effort"] = "low"
            extra = {"betas": ["server-side-fallback-2026-07-01"], "fallbacks": "default"}
        response = await self.client.beta.messages.create(
            model=self.model,
            max_tokens=4000,
            system=SYSTEM_PROMPT.format(lang="Russian" if lang == "ru" else "English"),
            messages=[{"role": "user", "content": [encode_image(image), {"type": "text", "text": user_text}]}],
            output_config=output_config,
            **extra,
        )
        if response.stop_reason == "refusal":
            raise RecognitionRefused()
        text = next(b.text for b in response.content if b.type == "text")
        return FoodAnalysis.model_validate(json.loads(text))
