import { describe, it, expect } from "vitest";
import { calculateMovementCost, calculateMovementDistance } from "../movement-cost";

describe("calculateMovementDistance", () => {
  it("returns 1 for 1 tile move", () => {
    const events = [{ type: "move", from: [0, 0], to: [1, 0] }];
    expect(calculateMovementDistance(events)).toBe(1);
  });

  it("returns 2 for 2 tile move", () => {
    const events = [{ type: "move", from: [0, 0], to: [2, 0] }];
    expect(calculateMovementDistance(events)).toBe(2);
  });

  it("accumulates distance across multi-segment path", () => {
    const events = [
      { type: "move", from: [0, 0], to: [1, 0] },
      { type: "move", from: [1, 0], to: [2, 0] },
    ];
    expect(calculateMovementDistance(events)).toBe(2);
  });

  it("uses Chebyshev distance for diagonal", () => {
    const events = [{ type: "move", from: [0, 0], to: [2, 2] }];
    expect(calculateMovementDistance(events)).toBe(2);
  });

  it("returns 0 for empty events", () => {
    expect(calculateMovementDistance([])).toBe(0);
  });

  it("returns 0 for non-move events", () => {
    const events = [{ type: "damage", entity: "warrior_p1", amount: 10 }];
    expect(calculateMovementDistance(events)).toBe(0);
  });

  it("handles ability_movement events", () => {
    const events = [{ type: "ability_movement", from: [0, 0], to: [3, 0] }];
    expect(calculateMovementDistance(events)).toBe(3);
  });

  it("handles from/to as {x, y} objects", () => {
    const events = [{ type: "move", from: { x: 0, y: 0 }, to: { x: 2, y: 0 } }];
    expect(calculateMovementDistance(events)).toBe(2);
  });

  it("handles position field as alias for to", () => {
    const events = [{ type: "move", from: [0, 0], position: [4, 0] }];
    expect(calculateMovementDistance(events)).toBe(4);
  });
});

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

  it("returns 0 for empty events", () => {
    expect(calculateMovementCost([])).toBe(0);
  });

  it("accumulates distance across multi-segment path", () => {
    const events = [
      { type: "move", from: [0, 0], to: [1, 0] },
      { type: "move", from: [1, 0], to: [2, 0] },
    ];
    expect(calculateMovementCost(events)).toBe(1);
  });
});

describe("cumulative PA cost across separate moves in a turn", () => {
  it("move 1 tile costs 1, then move 1 more tile costs 0 (total 2 tiles = 1 PA)", () => {
    let cumDist = 0;

    const move1 = [{ type: "move", from: [0, 0], to: [1, 0] }];
    const dist1 = calculateMovementDistance(move1);
    const oldCost1 = Math.ceil(cumDist / 2);
    cumDist += dist1;
    const cost1 = Math.ceil(cumDist / 2) - oldCost1;
    expect(cost1).toBe(1);

    const move2 = [{ type: "move", from: [1, 0], to: [2, 0] }];
    const dist2 = calculateMovementDistance(move2);
    const oldCost2 = Math.ceil(cumDist / 2);
    cumDist += dist2;
    const cost2 = Math.ceil(cumDist / 2) - oldCost2;
    expect(cost2).toBe(0);
  });

  it("move 1+1+1 tiles costs 1, 0, 1 PA (total 3 tiles = 2 PA)", () => {
    let cumDist = 0;

    const costs: number[] = [];
    const moves = [
      [{ type: "move", from: [0, 0], to: [1, 0] }],
      [{ type: "move", from: [1, 0], to: [2, 0] }],
      [{ type: "move", from: [2, 0], to: [3, 0] }],
    ];

    for (const move of moves) {
      const dist = calculateMovementDistance(move);
      const oldCost = Math.ceil(cumDist / 2);
      cumDist += dist;
      costs.push(Math.ceil(cumDist / 2) - oldCost);
    }

    expect(costs).toEqual([1, 0, 1]);
  });

  it("move 2 tiles then 2 more costs 1, 1 PA (total 4 tiles = 2 PA)", () => {
    let cumDist = 0;

    const move1 = [{ type: "move", from: [0, 0], to: [2, 0] }];
    const dist1 = calculateMovementDistance(move1);
    const oldCost1 = Math.ceil(cumDist / 2);
    cumDist += dist1;
    const cost1 = Math.ceil(cumDist / 2) - oldCost1;
    expect(cost1).toBe(1);

    const move2 = [{ type: "move", from: [2, 0], to: [4, 0] }];
    const dist2 = calculateMovementDistance(move2);
    const oldCost2 = Math.ceil(cumDist / 2);
    cumDist += dist2;
    const cost2 = Math.ceil(cumDist / 2) - oldCost2;
    expect(cost2).toBe(1);
  });
});
