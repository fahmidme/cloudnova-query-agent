"""Small session-only context; never retain raw result rows or credentials."""

import json

MAX_TURNS = 3
MAX_HISTORY_BYTES = 12_000


class Conversation:
    def __init__(self):
        self.messages: list[dict] = []

    def clear(self):
        self.messages.clear()

    def remember(self, question: str, result: dict):
        # SQL carries the previous filters even when result sharing is disabled.
        # The service never puts local-only numeric results into answer text.
        text = result.get('answer', '')
        if result.get('sql'):
            text += f"\nPrevious query: {result['sql']}\nInterpretation: {result.get('explanation', '')}"
        if not text.strip():
            return
        self.messages.extend([{'role': 'user', 'content': question},
                              {'role': 'assistant', 'content': text}])
        while (len(self.messages) > MAX_TURNS * 2 or
               len(json.dumps(self.messages).encode()) > MAX_HISTORY_BYTES):
            # Remove whole turns; never leave an orphaned assistant response.
            del self.messages[:2]
