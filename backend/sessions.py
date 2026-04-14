import uuid
from dataclasses import dataclass

from engine.systems.battle import BattleState


@dataclass
class BattleSession:
    session_id: str
    battle_state: BattleState
    difficulty: str
    player_entity_ids: list[str]
    ai_entity_ids: list[str]


class SessionManager:
    def __init__(self):
        self._sessions: dict[str, BattleSession] = {}

    def create(
        self,
        battle_state: BattleState,
        difficulty: str,
        player_ids: list[str],
        ai_ids: list[str],
    ) -> BattleSession:
        session_id = str(uuid.uuid4())
        session = BattleSession(
            session_id=session_id,
            battle_state=battle_state,
            difficulty=difficulty,
            player_entity_ids=player_ids,
            ai_entity_ids=ai_ids,
        )
        self._sessions[session_id] = session
        return session

    def get(self, session_id: str) -> BattleSession | None:
        return self._sessions.get(session_id)

    def remove(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)


session_manager = SessionManager()
