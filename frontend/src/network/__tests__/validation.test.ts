import { describe, it, expect } from "vitest";
import {
  validateAttributePoints,
  validateAbilitySelection,
  validateTeam,
} from "../validation";

describe("validateAttributePoints", () => {
  it("returns true for valid distribution: sum=10, each 0-5", () => {
    expect(validateAttributePoints([5, 2, 3, 0, 0])).toBe(true);
    expect(validateAttributePoints([2, 2, 2, 2, 2])).toBe(true);
    expect(validateAttributePoints([5, 5, 0, 0, 0])).toBe(true);
    expect(validateAttributePoints([0, 0, 0, 5, 5])).toBe(true);
    expect(validateAttributePoints([3, 3, 2, 1, 1])).toBe(true);
  });

  it("returns false when sum is not 10", () => {
    expect(validateAttributePoints([5, 5, 5, 0, 0])).toBe(false);
    expect(validateAttributePoints([1, 1, 1, 1, 1])).toBe(false);
    expect(validateAttributePoints([0, 0, 0, 0, 0])).toBe(false);
  });

  it("returns false when any value exceeds 5", () => {
    expect(validateAttributePoints([6, 1, 1, 1, 1])).toBe(false);
    expect(validateAttributePoints([0, 0, 0, 0, 10])).toBe(false);
  });

  it("returns false when any value is negative", () => {
    expect(validateAttributePoints([-1, 3, 3, 3, 2])).toBe(false);
  });

  it("returns false when array length is not 5", () => {
    expect(validateAttributePoints([5, 5])).toBe(false);
    expect(validateAttributePoints([2, 2, 2, 2, 2, 0])).toBe(false);
    expect(validateAttributePoints([])).toBe(false);
  });
});

describe("validateAbilitySelection", () => {
  const available = [
    "ability_1",
    "ability_2",
    "ability_3",
    "ability_4",
    "ability_5",
    "ability_6",
    "ability_7",
    "ability_8",
    "ability_9",
    "ability_10",
    "ability_11",
  ];

  it("returns true for valid selection: 5 unique abilities from available", () => {
    expect(
      validateAbilitySelection(
        ["ability_1", "ability_2", "ability_3", "ability_4", "ability_5"],
        available,
      ),
    ).toBe(true);
    expect(
      validateAbilitySelection(
        ["ability_7", "ability_8", "ability_9", "ability_10", "ability_11"],
        available,
      ),
    ).toBe(true);
  });

  it("returns false when not exactly 5 abilities", () => {
    expect(
      validateAbilitySelection(
        ["ability_1", "ability_2", "ability_3", "ability_4"],
        available,
      ),
    ).toBe(false);
    expect(
      validateAbilitySelection(
        [
          "ability_1",
          "ability_2",
          "ability_3",
          "ability_4",
          "ability_5",
          "ability_6",
        ],
        available,
      ),
    ).toBe(false);
    expect(validateAbilitySelection([], available)).toBe(false);
  });

  it("returns false when abilities contain duplicates", () => {
    expect(
      validateAbilitySelection(
        ["ability_1", "ability_1", "ability_2", "ability_3", "ability_4"],
        available,
      ),
    ).toBe(false);
  });

  it("returns false when ability is not in available list", () => {
    expect(
      validateAbilitySelection(
        [
          "ability_1",
          "ability_2",
          "ability_3",
          "ability_4",
          "unknown_ability",
        ],
        available,
      ),
    ).toBe(false);
  });
});

describe("validateTeam", () => {
  it("returns true for 1-3 unique classes", () => {
    expect(validateTeam(["warrior"])).toBe(true);
    expect(validateTeam(["warrior", "mage"])).toBe(true);
    expect(validateTeam(["warrior", "mage", "cleric"])).toBe(true);
  });

  it("returns false for empty team", () => {
    expect(validateTeam([])).toBe(false);
  });

  it("returns false for more than 3 classes", () => {
    expect(validateTeam(["warrior", "mage", "cleric", "archer"])).toBe(false);
  });

  it("returns false for duplicate classes", () => {
    expect(validateTeam(["warrior", "warrior"])).toBe(false);
    expect(validateTeam(["mage", "cleric", "mage"])).toBe(false);
  });
});
