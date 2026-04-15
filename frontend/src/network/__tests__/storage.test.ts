import { describe, it, expect, beforeEach } from "vitest";
import {
  saveBuild,
  loadBuild,
  saveDifficulty,
  loadDifficulty,
  saveLastTeam,
  loadLastTeam,
} from "../storage";

describe("build persistence", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("saves and loads a build for a class", () => {
    const build = {
      attribute_points: [5, 2, 3, 0, 0],
      ability_ids: ["impacto_brutal", "investida", "corte_profundo", "muralha_de_ferro", "grito_de_guerra"],
    };

    saveBuild("warrior", build);
    const loaded = loadBuild("warrior");

    expect(loaded).toEqual(build);
  });

  it("returns null when no build is saved for class", () => {
    const loaded = loadBuild("warrior");
    expect(loaded).toBeNull();
  });

  it("saves builds for different classes independently", () => {
    const warriorBuild = {
      attribute_points: [5, 2, 3, 0, 0],
      ability_ids: ["a", "b", "c", "d", "e"],
    };
    const mageBuild = {
      attribute_points: [0, 0, 2, 5, 3],
      ability_ids: ["f", "g", "h", "i", "j"],
    };

    saveBuild("warrior", warriorBuild);
    saveBuild("mage", mageBuild);

    expect(loadBuild("warrior")).toEqual(warriorBuild);
    expect(loadBuild("mage")).toEqual(mageBuild);
  });

  it("overwrites previous build for same class", () => {
    const build1 = {
      attribute_points: [5, 2, 3, 0, 0],
      ability_ids: ["a", "b", "c", "d", "e"],
    };
    const build2 = {
      attribute_points: [0, 5, 0, 5, 0],
      ability_ids: ["f", "g", "h", "i", "j"],
    };

    saveBuild("warrior", build1);
    saveBuild("warrior", build2);

    expect(loadBuild("warrior")).toEqual(build2);
  });

  it("uses correct localStorage key format", () => {
    const build = {
      attribute_points: [5, 2, 3, 0, 0],
      ability_ids: ["a", "b", "c", "d", "e"],
    };

    saveBuild("warrior", build);

    const raw = localStorage.getItem("build_warrior");
    expect(raw).not.toBeNull();
    expect(JSON.parse(raw!)).toEqual(build);
  });

  it("handles corrupt localStorage data gracefully", () => {
    localStorage.setItem("build_warrior", "not-valid-json{{{");
    const loaded = loadBuild("warrior");
    expect(loaded).toBeNull();
  });
});

describe("difficulty persistence", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("saves and loads difficulty", () => {
    saveDifficulty("hard");
    expect(loadDifficulty()).toBe("hard");
  });

  it("returns 'normal' as default when no difficulty saved", () => {
    expect(loadDifficulty()).toBe("normal");
  });

  it("overwrites previous difficulty", () => {
    saveDifficulty("easy");
    saveDifficulty("hard");
    expect(loadDifficulty()).toBe("hard");
  });
});

describe("last team persistence", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("saves and loads last team composition", () => {
    saveLastTeam(["warrior", "mage", "cleric"]);
    expect(loadLastTeam()).toEqual(["warrior", "mage", "cleric"]);
  });

  it("returns empty array when no team saved", () => {
    expect(loadLastTeam()).toEqual([]);
  });

  it("handles single class team", () => {
    saveLastTeam(["assassin"]);
    expect(loadLastTeam()).toEqual(["assassin"]);
  });

  it("handles corrupt localStorage data gracefully", () => {
    localStorage.setItem("last_team", "invalid-json");
    expect(loadLastTeam()).toEqual([]);
  });
});
