import { describe, it, expect, beforeEach } from "vitest";
import { updateStateFromEvent, CharacterStateEntry } from "../update-state";

function makeChar(
  overrides?: Partial<CharacterStateEntry["data"]> & { status?: CharacterStateEntry["status"] },
): CharacterStateEntry {
  const { status, ...dataOverrides } = overrides ?? {};
  return {
    data: { current_hp: 50, max_hp: 50, position: { x: 0, y: 0 }, ...dataOverrides },
    status: status ?? "active",
  };
}

describe("updateStateFromEvent", () => {
  let characters: Map<string, CharacterStateEntry>;
  let activeEffects: Map<string, Set<string>>;

  beforeEach(() => {
    characters = new Map();
    activeEffects = new Map();
  });

  // --- move ---

  describe("move", () => {
    it("updates position from event.to as array [3, 4]", () => {
      characters.set("c1", makeChar());
      updateStateFromEvent({ type: "move", entity: "c1", to: [3, 4] }, characters, activeEffects);
      expect(characters.get("c1")!.data.position).toEqual({ x: 3, y: 4 });
    });

    it("updates position from event.position as object { x: 5, y: 6 }", () => {
      characters.set("c1", makeChar());
      updateStateFromEvent(
        { type: "move", entity: "c1", position: { x: 5, y: 6 } },
        characters,
        activeEffects,
      );
      expect(characters.get("c1")!.data.position).toEqual({ x: 5, y: 6 });
    });

    it("uses event.entity for entity ID", () => {
      characters.set("e1", makeChar());
      updateStateFromEvent({ type: "move", entity: "e1", to: [1, 2] }, characters, activeEffects);
      expect(characters.get("e1")!.data.position).toEqual({ x: 1, y: 2 });
    });

    it("uses event.character as fallback for entity ID", () => {
      characters.set("c2", makeChar());
      updateStateFromEvent({ type: "move", character: "c2", to: [7, 3] }, characters, activeEffects);
      expect(characters.get("c2")!.data.position).toEqual({ x: 7, y: 3 });
    });

    it("handles ability_movement the same as move", () => {
      characters.set("c1", makeChar());
      updateStateFromEvent(
        { type: "ability_movement", entity: "c1", to: [9, 7] },
        characters,
        activeEffects,
      );
      expect(characters.get("c1")!.data.position).toEqual({ x: 9, y: 7 });
    });
  });

  // --- basic_attack ---

  describe("basic_attack", () => {
    it("deducts event.damage from target HP", () => {
      characters.set("t1", makeChar({ current_hp: 40, max_hp: 50 }));
      updateStateFromEvent(
        { type: "basic_attack", target: "t1", damage: 15 },
        characters,
        activeEffects,
      );
      expect(characters.get("t1")!.data.current_hp).toBe(25);
    });

    it("sets status to knocked_out when HP drops to 0", () => {
      characters.set("t1", makeChar({ current_hp: 10, max_hp: 50 }));
      updateStateFromEvent(
        { type: "basic_attack", target: "t1", damage: 10 },
        characters,
        activeEffects,
      );
      expect(characters.get("t1")!.data.current_hp).toBe(0);
      expect(characters.get("t1")!.status).toBe("knocked_out");
    });

    it("sets status to dead when HP drops below -10", () => {
      characters.set("t1", makeChar({ current_hp: 5, max_hp: 50 }));
      updateStateFromEvent(
        { type: "basic_attack", target: "t1", damage: 20 },
        characters,
        activeEffects,
      );
      expect(characters.get("t1")!.data.current_hp).toBe(-15);
      expect(characters.get("t1")!.status).toBe("dead");
    });

    it("does NOT change status from knocked_out to knocked_out again", () => {
      characters.set("t1", makeChar({ current_hp: -5, max_hp: 50, status: "knocked_out" }));
      updateStateFromEvent(
        { type: "basic_attack", target: "t1", damage: 3 },
        characters,
        activeEffects,
      );
      expect(characters.get("t1")!.data.current_hp).toBe(-8);
      expect(characters.get("t1")!.status).toBe("knocked_out");
    });

    it("transitions knocked_out to dead when HP goes below -10", () => {
      characters.set("t1", makeChar({ current_hp: -5, max_hp: 50, status: "knocked_out" }));
      updateStateFromEvent(
        { type: "basic_attack", target: "t1", damage: 10 },
        characters,
        activeEffects,
      );
      expect(characters.get("t1")!.data.current_hp).toBe(-15);
      expect(characters.get("t1")!.status).toBe("dead");
    });

    it("uses event.amount as fallback for damage", () => {
      characters.set("t1", makeChar({ current_hp: 30, max_hp: 50 }));
      updateStateFromEvent(
        { type: "basic_attack", target: "t1", amount: 7 },
        characters,
        activeEffects,
      );
      expect(characters.get("t1")!.data.current_hp).toBe(23);
    });
  });

  // --- heal ---

  describe("heal", () => {
    it("adds amount to HP, capped at max_hp", () => {
      characters.set("t1", makeChar({ current_hp: 30, max_hp: 50 }));
      updateStateFromEvent(
        { type: "heal", target: "t1", amount: 100 },
        characters,
        activeEffects,
      );
      expect(characters.get("t1")!.data.current_hp).toBe(50);
    });

    it("revives knocked_out character to active when HP > 0", () => {
      characters.set("t1", makeChar({ current_hp: -5, max_hp: 50, status: "knocked_out" }));
      updateStateFromEvent(
        { type: "heal", target: "t1", amount: 10 },
        characters,
        activeEffects,
      );
      expect(characters.get("t1")!.data.current_hp).toBe(5);
      expect(characters.get("t1")!.status).toBe("active");
    });

    it("does not revive if healed HP is still <= 0", () => {
      characters.set("t1", makeChar({ current_hp: -5, max_hp: 50, status: "knocked_out" }));
      updateStateFromEvent(
        { type: "heal", target: "t1", amount: 3 },
        characters,
        activeEffects,
      );
      expect(characters.get("t1")!.data.current_hp).toBe(-2);
      expect(characters.get("t1")!.status).toBe("knocked_out");
    });

    it("uses event.heal as fallback for amount", () => {
      characters.set("t1", makeChar({ current_hp: 40, max_hp: 50 }));
      updateStateFromEvent(
        { type: "heal", target: "t1", heal: 5 },
        characters,
        activeEffects,
      );
      expect(characters.get("t1")!.data.current_hp).toBe(45);
    });

    it("uses event.entity as fallback for target", () => {
      characters.set("t1", makeChar({ current_hp: 20, max_hp: 50 }));
      updateStateFromEvent(
        { type: "heal", entity: "t1", amount: 10 },
        characters,
        activeEffects,
      );
      expect(characters.get("t1")!.data.current_hp).toBe(30);
    });

    it("handles self_heal type", () => {
      characters.set("t1", makeChar({ current_hp: 25, max_hp: 50 }));
      updateStateFromEvent(
        { type: "self_heal", target: "t1", amount: 15 },
        characters,
        activeEffects,
      );
      expect(characters.get("t1")!.data.current_hp).toBe(40);
    });

    it("handles lifesteal type", () => {
      characters.set("t1", makeChar({ current_hp: 10, max_hp: 50 }));
      updateStateFromEvent(
        { type: "lifesteal", target: "t1", amount: 8 },
        characters,
        activeEffects,
      );
      expect(characters.get("t1")!.data.current_hp).toBe(18);
    });
  });

  // --- bleed / dot_tick ---

  describe("bleed / dot_tick", () => {
    it("deducts damage from entity HP", () => {
      characters.set("t1", makeChar({ current_hp: 30, max_hp: 50 }));
      updateStateFromEvent(
        { type: "bleed", entity: "t1", damage: 5 },
        characters,
        activeEffects,
      );
      expect(characters.get("t1")!.data.current_hp).toBe(25);
    });

    it("can cause knockout when HP drops to 0", () => {
      characters.set("t1", makeChar({ current_hp: 3, max_hp: 50 }));
      updateStateFromEvent(
        { type: "dot_tick", entity: "t1", damage: 3 },
        characters,
        activeEffects,
      );
      expect(characters.get("t1")!.data.current_hp).toBe(0);
      expect(characters.get("t1")!.status).toBe("knocked_out");
    });

    it("can cause death when HP drops below -10", () => {
      characters.set("t1", makeChar({ current_hp: 5, max_hp: 50 }));
      updateStateFromEvent(
        { type: "bleed", entity: "t1", damage: 20 },
        characters,
        activeEffects,
      );
      expect(characters.get("t1")!.data.current_hp).toBe(-15);
      expect(characters.get("t1")!.status).toBe("dead");
    });

    it("uses event.amount as fallback for damage", () => {
      characters.set("t1", makeChar({ current_hp: 20, max_hp: 50 }));
      updateStateFromEvent(
        { type: "dot_tick", entity: "t1", amount: 4 },
        characters,
        activeEffects,
      );
      expect(characters.get("t1")!.data.current_hp).toBe(16);
    });
  });

  // --- hot_tick ---

  describe("hot_tick", () => {
    it("heals entity HP, capped at max_hp", () => {
      characters.set("t1", makeChar({ current_hp: 45, max_hp: 50 }));
      updateStateFromEvent(
        { type: "hot_tick", entity: "t1", heal: 10 },
        characters,
        activeEffects,
      );
      expect(characters.get("t1")!.data.current_hp).toBe(50);
    });

    it("uses event.amount as fallback for heal", () => {
      characters.set("t1", makeChar({ current_hp: 30, max_hp: 50 }));
      updateStateFromEvent(
        { type: "hot_tick", entity: "t1", amount: 8 },
        characters,
        activeEffects,
      );
      expect(characters.get("t1")!.data.current_hp).toBe(38);
    });
  });

  // --- knocked_out event ---

  describe("knocked_out event", () => {
    it("sets status to knocked_out directly", () => {
      characters.set("t1", makeChar());
      updateStateFromEvent(
        { type: "knocked_out", entity: "t1" },
        characters,
        activeEffects,
      );
      expect(characters.get("t1")!.status).toBe("knocked_out");
    });
  });

  // --- death event ---

  describe("death event", () => {
    it("sets status to dead directly", () => {
      characters.set("t1", makeChar());
      updateStateFromEvent(
        { type: "death", entity: "t1" },
        characters,
        activeEffects,
      );
      expect(characters.get("t1")!.status).toBe("dead");
    });
  });

  // --- effect_applied ---

  describe("effect_applied", () => {
    it("adds tag to activeEffects set for the target", () => {
      updateStateFromEvent(
        { type: "effect_applied", target: "t1", tag: "burning" },
        characters,
        activeEffects,
      );
      expect(activeEffects.get("t1")?.has("burning")).toBe(true);
    });

    it("creates set if target has no effects yet", () => {
      expect(activeEffects.has("t1")).toBe(false);
      updateStateFromEvent(
        { type: "effect_applied", target: "t1", tag: "wet" },
        characters,
        activeEffects,
      );
      expect(activeEffects.get("t1")).toEqual(new Set(["wet"]));
    });

    it("accumulates multiple effects", () => {
      updateStateFromEvent(
        { type: "effect_applied", target: "t1", tag: "burning" },
        characters,
        activeEffects,
      );
      updateStateFromEvent(
        { type: "effect_applied", target: "t1", tag: "wet" },
        characters,
        activeEffects,
      );
      expect(activeEffects.get("t1")).toEqual(new Set(["burning", "wet"]));
    });
  });

  // --- effect_expired ---

  describe("effect_expired", () => {
    it("removes tag from activeEffects set", () => {
      activeEffects.set("t1", new Set(["burning", "wet"]));
      updateStateFromEvent(
        { type: "effect_expired", entity: "t1", tag: "burning" },
        characters,
        activeEffects,
      );
      expect(activeEffects.get("t1")?.has("burning")).toBe(false);
      expect(activeEffects.get("t1")?.has("wet")).toBe(true);
    });

    it("does nothing if entity has no effects", () => {
      updateStateFromEvent(
        { type: "effect_expired", entity: "t1", tag: "burning" },
        characters,
        activeEffects,
      );
      expect(activeEffects.has("t1")).toBe(false);
    });
  });

  // --- unknown event type ---

  describe("unknown event type", () => {
    it("does nothing and does not throw", () => {
      characters.set("t1", makeChar({ current_hp: 30 }));
      expect(() =>
        updateStateFromEvent(
          { type: "some_unknown_event", entity: "t1" },
          characters,
          activeEffects,
        ),
      ).not.toThrow();
      expect(characters.get("t1")!.data.current_hp).toBe(30);
    });

    it("does nothing when event has no type", () => {
      characters.set("t1", makeChar({ current_hp: 30 }));
      expect(() =>
        updateStateFromEvent({ entity: "t1" }, characters, activeEffects),
      ).not.toThrow();
      expect(characters.get("t1")!.data.current_hp).toBe(30);
    });
  });
});
