export interface CharacterStateEntry {
  data: {
    current_hp: number;
    max_hp: number;
    position: { x: number; y: number };
  };
  status: "active" | "knocked_out" | "dead";
}

export interface MapObjectStateEntry {
  data: {
    hp: number | null;
    max_hp: number | null;
    position: { x: number; y: number };
  };
}

export function updateStateFromEvent<T extends CharacterStateEntry>(
  event: Record<string, unknown>,
  characters: Map<string, T>,
  activeEffects: Map<string, Set<string>>,
  mapObjects?: Map<string, MapObjectStateEntry>,
): void {
  const type = event.type as string | undefined;
  if (!type) return;

  switch (type) {
    case "move":
    case "ability_movement": {
      const entityId = (event.entity ?? event.character) as string | undefined;
      if (!entityId) return;
      const dest = (event.to ?? event.position) as
        | [number, number]
        | { x: number; y: number }
        | undefined;
      if (!dest) return;
      const [dx, dy] = Array.isArray(dest) ? dest : [dest.x, dest.y];
      const entry = characters.get(entityId);
      if (entry) {
        entry.data.position = { x: dx, y: dy };
      }
      break;
    }
    case "basic_attack":
    case "ability":
    case "aoe_hit":
    case "opportunity_attack":
    case "chain_primary":
    case "chain_secondary": {
      const targetId = event.target as string | undefined;
      if (!targetId) return;
      const amount = (event.damage ?? event.amount) as number | undefined;
      if (amount === undefined) return;
      const entry = characters.get(targetId);
      if (!entry) return;
      entry.data.current_hp -= amount;
      if (entry.data.current_hp < -10) {
        entry.status = "dead";
      } else if (entry.data.current_hp <= 0 && entry.status === "active") {
        entry.status = "knocked_out";
      }
      break;
    }
    case "heal":
    case "self_heal":
    case "lifesteal": {
      const targetId = (event.target ?? event.entity) as string | undefined;
      if (!targetId) return;
      const amount = (event.amount ?? event.heal) as number | undefined;
      if (amount === undefined) return;
      const entry = characters.get(targetId);
      if (!entry) return;
      const wasKnockedOut = entry.status === "knocked_out";
      entry.data.current_hp = Math.min(
        entry.data.current_hp + amount,
        entry.data.max_hp,
      );
      if (wasKnockedOut && entry.data.current_hp > 0) {
        entry.status = "active";
      }
      break;
    }
    case "hot_tick": {
      const entityId = event.entity as string | undefined;
      if (!entityId) return;
      const amount = (event.heal ?? event.amount) as number | undefined;
      if (amount === undefined) return;
      const entry = characters.get(entityId);
      if (!entry) return;
      entry.data.current_hp = Math.min(
        entry.data.current_hp + amount,
        entry.data.max_hp,
      );
      break;
    }
    case "bleed":
    case "dot_tick": {
      const entityId = event.entity as string | undefined;
      if (!entityId) return;
      const amount = (event.damage ?? event.amount) as number | undefined;
      if (amount === undefined) return;
      const entry = characters.get(entityId);
      if (!entry) return;
      entry.data.current_hp -= amount;
      if (entry.data.current_hp < -10) {
        entry.status = "dead";
      } else if (entry.data.current_hp <= 0 && entry.status === "active") {
        entry.status = "knocked_out";
      }
      break;
    }
    case "knocked_out": {
      const entityId = event.entity as string | undefined;
      if (!entityId) return;
      const entry = characters.get(entityId);
      if (entry) entry.status = "knocked_out";
      break;
    }
    case "death": {
      const entityId = event.entity as string | undefined;
      if (!entityId) return;
      const entry = characters.get(entityId);
      if (entry) entry.status = "dead";
      break;
    }
    case "object_hit": {
      const objId = event.object as string | undefined;
      if (!objId || !mapObjects) break;
      const obj = mapObjects.get(objId);
      if (!obj || obj.data.hp === null) break;
      const damage = event.damage as number | undefined;
      if (damage !== undefined) {
        obj.data.hp = Math.max(0, obj.data.hp - damage);
      }
      break;
    }
    case "object_destroyed": {
      break;
    }
    case "effect_applied": {
      const targetId = event.target as string | undefined;
      const tag = event.tag as string | undefined;
      if (targetId && tag) {
        if (!activeEffects.has(targetId))
          activeEffects.set(targetId, new Set());
        activeEffects.get(targetId)!.add(tag);
      }
      break;
    }
    case "effect_expired": {
      const entityId = event.entity as string | undefined;
      const tag = event.tag as string | undefined;
      if (entityId && tag) {
        activeEffects.get(entityId)?.delete(tag);
      }
      break;
    }
  }
}
