# Copyright Sierra

from typing import Dict, List


class BaseAgent:
    def __init__(self):
        pass

    def act(self, observation, info):
        return None

    def get_messages(self) -> List[Dict[str, str]]:
        return []
