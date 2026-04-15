import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { getDefaults, startBattle, API_BASE_URL } from "../api-client";
import type {
  BuildsDefaultsResponse,
  BattleStartResponse,
} from "../types";

const MOCK_DEFAULTS_RESPONSE: BuildsDefaultsResponse = {
  classes: [
    {
      class_id: "warrior",
      base_attributes: { str: 8, dex: 4, con: 7, int_: 2, wis: 4 },
      hp_base: 50,
      abilities: [
        {
          id: "basic_attack_warrior",
          name: "Basic Attack",
          pa_cost: 2,
          cooldown: 0,
          max_range: 1,
          target: "single_enemy",
          damage_base: 6,
          damage_type: "physical",
          heal_base: 0,
          elemental_tag: "",
        },
      ],
    },
  ],
  default_builds: [
    {
      class_id: "warrior",
      attribute_points: [5, 2, 3, 0, 0],
      ability_ids: [
        "impacto_brutal",
        "investida",
        "corte_profundo",
        "muralha_de_ferro",
        "grito_de_guerra",
      ],
    },
  ],
};

const MOCK_BATTLE_RESPONSE: BattleStartResponse = {
  session_id: "abc-123",
  initial_state: {
    grid_size: { width: 10, height: 8 },
    map_objects: [
      {
        entity_id: "obj_1",
        object_type: "crate",
        position: { x: 3, y: 4 },
        hp: 10,
        max_hp: 10,
        blocks_movement: true,
        blocks_los: true,
      },
    ],
    characters: [
      {
        entity_id: "warrior_p1",
        team: "player",
        class_id: "warrior",
        attributes: { str: 13, dex: 6, con: 10, int_: 2, wis: 4 },
        current_hp: 85,
        max_hp: 85,
        position: { x: 1, y: 3 },
        abilities: [],
      },
    ],
    turn_order: ["warrior_p1", "mage_ai"],
    current_character: "warrior_p1",
  },
};

describe("getDefaults", () => {
  let fetchSpy: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchSpy = vi.fn();
    vi.stubGlobal("fetch", fetchSpy);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("sends GET to /builds/defaults and returns typed response", async () => {
    fetchSpy.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => MOCK_DEFAULTS_RESPONSE,
    });

    const result = await getDefaults();

    expect(fetchSpy).toHaveBeenCalledOnce();
    expect(fetchSpy).toHaveBeenCalledWith(`${API_BASE_URL}/builds/defaults`);
    expect(result).toEqual(MOCK_DEFAULTS_RESPONSE);
    expect(result.classes).toHaveLength(1);
    expect(result.classes[0].class_id).toBe("warrior");
    expect(result.default_builds[0].attribute_points).toEqual([5, 2, 3, 0, 0]);
  });

  it("throws on HTTP error with descriptive message", async () => {
    fetchSpy.mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => ({ detail: "Internal server error" }),
    });

    await expect(getDefaults()).rejects.toThrow(/500/);
  });

  it("throws on network failure", async () => {
    fetchSpy.mockRejectedValueOnce(new TypeError("Failed to fetch"));

    await expect(getDefaults()).rejects.toThrow();
  });
});

describe("startBattle", () => {
  let fetchSpy: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchSpy = vi.fn();
    vi.stubGlobal("fetch", fetchSpy);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("sends POST to /battle/start with correct body", async () => {
    fetchSpy.mockResolvedValueOnce({
      ok: true,
      status: 201,
      json: async () => MOCK_BATTLE_RESPONSE,
    });

    const team = [
      {
        class_id: "warrior",
        attribute_points: [5, 2, 3, 0, 0],
        ability_ids: [
          "impacto_brutal",
          "investida",
          "corte_profundo",
          "muralha_de_ferro",
          "grito_de_guerra",
        ],
      },
    ];

    const result = await startBattle("normal", team);

    expect(fetchSpy).toHaveBeenCalledOnce();
    const [url, options] = fetchSpy.mock.calls[0];
    expect(url).toBe(`${API_BASE_URL}/battle/start`);
    expect(options.method).toBe("POST");
    expect(options.headers["Content-Type"]).toBe("application/json");
    expect(JSON.parse(options.body)).toEqual({
      difficulty: "normal",
      team,
    });
    expect(result.session_id).toBe("abc-123");
    expect(result.initial_state.grid_size).toEqual({ width: 10, height: 8 });
  });

  it("returns full initial state with characters and map objects", async () => {
    fetchSpy.mockResolvedValueOnce({
      ok: true,
      status: 201,
      json: async () => MOCK_BATTLE_RESPONSE,
    });

    const result = await startBattle("easy", [
      {
        class_id: "warrior",
        attribute_points: [5, 2, 3, 0, 0],
        ability_ids: ["a", "b", "c", "d", "e"],
      },
    ]);

    expect(result.initial_state.characters).toHaveLength(1);
    expect(result.initial_state.characters[0].team).toBe("player");
    expect(result.initial_state.map_objects).toHaveLength(1);
    expect(result.initial_state.turn_order).toEqual([
      "warrior_p1",
      "mage_ai",
    ]);
    expect(result.initial_state.current_character).toBe("warrior_p1");
  });

  it("throws on HTTP 422 validation error", async () => {
    fetchSpy.mockResolvedValueOnce({
      ok: false,
      status: 422,
      json: async () => ({
        detail: [{ msg: "Team size must be 1-3" }],
      }),
    });

    await expect(
      startBattle("normal", []),
    ).rejects.toThrow(/422/);
  });

  it("throws on HTTP 400 error", async () => {
    fetchSpy.mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: async () => ({ detail: "Invalid difficulty" }),
    });

    await expect(
      startBattle("impossible", [
        {
          class_id: "warrior",
          attribute_points: [5, 2, 3, 0, 0],
          ability_ids: ["a", "b", "c", "d", "e"],
        },
      ]),
    ).rejects.toThrow(/400/);
  });
});
