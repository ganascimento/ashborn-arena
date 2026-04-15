import { describe, it, expect } from "vitest";
import { calculateMovementCost } from "../movement-cost";

describe("calculateMovementCost", () => {
  it("returns 1 PA for 1 tile move", () => {
    const events = [{ type: "move", from: [0, 0], to: [1, 0] }];
    expect(calculateMovementCost(events)).toBe(1);
  });

  it("returns 1 PA for 2 tile move", () => {
    const events = [{ type: "move", from: [0, 0], to: [2, 0] }];
    expect(calculateMovementCost(events)).toBe(1);
  });

  it("returns 2 PA for 3 tile move", () => {
    const events = [{ type: "move", from: [0, 0], to: [3, 0] }];
    expect(calculateMovementCost(events)).toBe(2);
  });

  it("returns 2 PA for 4 tile move", () => {
    const events = [{ type: "move", from: [0, 0], to: [4, 0] }];
    expect(calculateMovementCost(events)).toBe(2);
  });

  it("returns 4 PA for 8 tile move (max theoretical)", () => {
    const events = [{ type: "move", from: [0, 0], to: [8, 0] }];
    expect(calculateMovementCost(events)).toBe(4);
  });

  it("uses Chebyshev distance for diagonal move (2 tiles)", () => {
    const events = [{ type: "move", from: [0, 0], to: [2, 2] }];
    expect(calculateMovementCost(events)).toBe(1);
  });

  it("accumulates distance across multi-segment path (bug fix)", () => {
    const events = [
      { type: "move", from: [0, 0], to: [1, 0] },
      { type: "move", from: [1, 0], to: [2, 0] },
    ];
    expect(calculateMovementCost(events)).toBe(1);
  });

  it("accumulates distance across 3 segments", () => {
    const events = [
      { type: "move", from: [0, 0], to: [1, 0] },
      { type: "move", from: [1, 0], to: [2, 0] },
      { type: "move", from: [2, 0], to: [3, 0] },
    ];
    expect(calculateMovementCost(events)).toBe(2);
  });

  it("returns 0 for empty events", () => {
    expect(calculateMovementCost([])).toBe(0);
  });

  it("returns 0 for events without move type", () => {
    const events = [
      { type: "damage", entity: "warrior_p1", amount: 10 },
      { type: "effect_applied", entity: "mage_ai1", tag: "burn" },
    ];
    expect(calculateMovementCost(events)).toBe(0);
  });

  it("handles ability_movement events", () => {
    const events = [{ type: "ability_movement", from: [0, 0], to: [3, 0] }];
    expect(calculateMovementCost(events)).toBe(2);
  });

  it("handles from/to as {x, y} objects", () => {
    const events = [{ type: "move", from: { x: 0, y: 0 }, to: { x: 2, y: 0 } }];
    expect(calculateMovementCost(events)).toBe(1);
  });

  it("handles position field as alias for to", () => {
    const events = [{ type: "move", from: [0, 0], position: [4, 0] }];
    expect(calculateMovementCost(events)).toBe(2);
  });
});
