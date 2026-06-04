"""
OpenAI fallback action for RASA.

When NLU confidence is below threshold or intent is out_of_scope,
this action queries OpenAI GPT to generate a contextual response
while maintaining the RASA conversation flow.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from openai import AsyncOpenAI
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a helpful customer support assistant for a SaaS platform.
You are knowledgeable, concise, and professional.
If you cannot answer a question, politely say so and suggest contacting the support team.
Keep responses under 3 sentences unless more detail is absolutely necessary.
Do not make up features or pricing information."""


class ActionOpenAIFallback(Action):
    """Fallback to OpenAI GPT when RASA NLU confidence is low."""

    def name(self) -> str:
        return "action_openai_fallback"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: dict[str, Any],
    ) -> list[dict[str, Any]]:
        user_message = tracker.latest_message.get("text", "")

        if not user_message:
            dispatcher.utter_message(
                text="I didn't quite catch that. Could you rephrase?"
            )
            return []

        conversation_history = self._build_history(tracker)

        try:
            response = await self._query_openai(user_message, conversation_history)
            dispatcher.utter_message(text=response)
        except Exception as exc:
            logger.error("OpenAI API error: %s", exc)
            dispatcher.utter_message(
                text="I'm having trouble processing your request. Please try again or contact our support team."
            )

        return []

    def _build_history(self, tracker: Tracker) -> list[dict[str, str]]:
        """Build recent conversation history for context (last 5 turns)."""
        history = []
        events = tracker.events[-10:]

        for event in events:
            if event.get("event") == "user":
                history.append({"role": "user", "content": event.get("text", "")})
            elif event.get("event") == "bot":
                history.append({"role": "assistant", "content": event.get("text", "")})

        return history[-5:]

    async def _query_openai(
        self,
        user_message: str,
        history: list[dict[str, str]],
    ) -> str:
        from openai.types.chat import ChatCompletionMessageParam

        client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])

        raw_messages: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": SYSTEM_PROMPT},
        ]
        for msg in history:
            role = msg.get("role", "user")
            if role in ("user", "assistant", "system"):
                raw_messages.append({"role": role, "content": msg.get("content", "")})  # type: ignore[arg-type]
        raw_messages.append({"role": "user", "content": user_message})

        completion = await client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=raw_messages,
            max_tokens=200,
            temperature=0.7,
        )

        content = completion.choices[0].message.content
        return content.strip() if content else "I'm not sure how to respond to that."
