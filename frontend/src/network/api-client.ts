import type {
  BuildsDefaultsResponse,
  CharacterRequest,
  BattleStartResponse,
} from "./types";

export const API_BASE_URL = "http://localhost:8000";

export async function getDefaults(): Promise<BuildsDefaultsResponse> {
  const res = await fetch(`${API_BASE_URL}/builds/defaults`);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(
      `GET /builds/defaults failed (${res.status}): ${JSON.stringify(body)}`,
    );
  }
  return res.json();
}

export async function startBattle(
  difficulty: string,
  team: CharacterRequest[],
  autoBattle = false,
): Promise<BattleStartResponse> {
  const res = await fetch(`${API_BASE_URL}/battle/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ difficulty, team, auto_battle: autoBattle }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(
      `POST /battle/start failed (${res.status}): ${JSON.stringify(body)}`,
    );
  }
  return res.json();
}
