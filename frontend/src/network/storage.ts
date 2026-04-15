import type { SavedBuild } from "./types";

export function saveBuild(classId: string, build: SavedBuild): void {
  localStorage.setItem(`build_${classId}`, JSON.stringify(build));
}

export function loadBuild(classId: string): SavedBuild | null {
  const raw = localStorage.getItem(`build_${classId}`);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function saveDifficulty(difficulty: string): void {
  localStorage.setItem("difficulty", difficulty);
}

export function loadDifficulty(): string {
  return localStorage.getItem("difficulty") ?? "normal";
}

export function saveLastTeam(classIds: string[]): void {
  localStorage.setItem("last_team", JSON.stringify(classIds));
}

export function loadLastTeam(): string[] {
  const raw = localStorage.getItem("last_team");
  if (!raw) return [];
  try {
    return JSON.parse(raw);
  } catch {
    return [];
  }
}
