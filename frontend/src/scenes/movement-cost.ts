export function calculateMovementCost(events: unknown[]): number {
  let totalDist = 0;
  for (const raw of events) {
    const event = raw as Record<string, unknown>;
    if (event.type === "move" || event.type === "ability_movement") {
      const from = event.from as [number, number] | { x: number; y: number } | undefined;
      const to = (event.to ?? event.position) as [number, number] | { x: number; y: number } | undefined;
      if (from && to) {
        const [fx, fy] = Array.isArray(from) ? from : [from.x, from.y];
        const [tx, ty] = Array.isArray(to) ? to : [to.x, to.y];
        totalDist += Math.max(Math.abs(tx - fx), Math.abs(ty - fy));
      }
    }
  }
  return Math.ceil(totalDist / 2);
}
