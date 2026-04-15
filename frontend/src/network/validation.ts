export function validateAttributePoints(points: number[]): boolean {
  if (points.length !== 5) return false;
  if (points.some((p) => p < 0 || p > 5)) return false;
  const sum = points.reduce((a, b) => a + b, 0);
  return sum === 10;
}

export function validateAbilitySelection(
  abilityIds: string[],
  availableIds: string[],
): boolean {
  if (abilityIds.length !== 5) return false;
  if (new Set(abilityIds).size !== 5) return false;
  return abilityIds.every((id) => availableIds.includes(id));
}

export function validateTeam(classIds: string[]): boolean {
  if (classIds.length < 1 || classIds.length > 3) return false;
  return new Set(classIds).size === classIds.length;
}
