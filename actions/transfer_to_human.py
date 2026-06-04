"""Action to transfer conversation to a human agent."""

from __future__ import annotations

import logging
from typing import Any

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

logger = logging.getLogger(__name__)


class ActionTransferToHuman(Action):
    """Signals the frontend to transfer the chat to a live agent."""

    def name(self) -> str:
        return "action_transfer_to_human"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: dict[str, Any],
    ) -> list[dict[str, Any]]:
        dispatcher.utter_message(
            text="I'm connecting you with a human agent now. Please hold on.",
            json_message={
                "type": "handoff",
                "agent": "human",
                "conversation_id": tracker.sender_id,
            },
        )

        logger.info("Handoff triggered for conversation: %s", tracker.sender_id)

        return []
