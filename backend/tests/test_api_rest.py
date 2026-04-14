import uuid

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


VALID_WARRIOR_REQUEST = {
    "class_id": "warrior",
    "attribute_points": [5, 2, 3, 0, 0],
    "ability_ids": [
        "impacto_brutal",
        "muralha_de_ferro",
        "investida",
        "corte_profundo",
        "sentenca_do_carrasco",
    ],
}

VALID_MAGE_REQUEST = {
    "class_id": "mage",
    "attribute_points": [0, 0, 2, 5, 3],
    "ability_ids": [
        "estilhaco_arcano",
        "nova_flamejante",
        "toque_do_inverno",
        "barreira_arcana",
        "sifao_vital",
    ],
}

VALID_ARCHER_REQUEST = {
    "class_id": "archer",
    "attribute_points": [2, 5, 3, 0, 0],
    "ability_ids": [
        "tiro_perfurante",
        "chuva_de_flechas",
        "ponta_envenenada",
        "flecha_glacial",
        "tiro_certeiro",
    ],
}


# ---------------------------------------------------------------------------
# GET /builds/defaults
# ---------------------------------------------------------------------------


class TestBuildsDefaults:
    def test_returns_200(self):
        r = client.get("/builds/defaults")
        assert r.status_code == 200

    def test_response_has_classes_and_default_builds(self):
        data = client.get("/builds/defaults").json()
        assert "classes" in data
        assert "default_builds" in data
        assert len(data["classes"]) == 5
        assert len(data["default_builds"]) == 5

    def test_classes_have_correct_attributes(self):
        data = client.get("/builds/defaults").json()
        for cls_info in data["classes"]:
            assert "class_id" in cls_info
            assert "base_attributes" in cls_info
            assert "hp_base" in cls_info
            assert "abilities" in cls_info
            assert len(cls_info["abilities"]) == 11

    def test_warrior_base_values(self):
        data = client.get("/builds/defaults").json()
        warrior = next(c for c in data["classes"] if c["class_id"] == "warrior")
        attrs = warrior["base_attributes"]
        assert attrs["str"] == 8
        assert attrs["dex"] == 4
        assert attrs["con"] == 7
        assert attrs["int_"] == 2
        assert attrs["wis"] == 4
        assert warrior["hp_base"] == 50

    def test_mage_base_values(self):
        data = client.get("/builds/defaults").json()
        mage = next(c for c in data["classes"] if c["class_id"] == "mage")
        assert mage["base_attributes"]["int_"] == 9
        assert mage["hp_base"] == 30

    def test_cleric_base_values(self):
        data = client.get("/builds/defaults").json()
        cleric = next(c for c in data["classes"] if c["class_id"] == "cleric")
        assert cleric["base_attributes"]["wis"] == 8
        assert cleric["base_attributes"]["con"] == 6
        assert cleric["hp_base"] == 45

    def test_archer_base_values(self):
        data = client.get("/builds/defaults").json()
        archer = next(c for c in data["classes"] if c["class_id"] == "archer")
        assert archer["base_attributes"]["dex"] == 9
        assert archer["hp_base"] == 35

    def test_assassin_base_values(self):
        data = client.get("/builds/defaults").json()
        assassin = next(c for c in data["classes"] if c["class_id"] == "assassin")
        assert assassin["base_attributes"]["dex"] == 8
        assert assassin["base_attributes"]["str"] == 5
        assert assassin["hp_base"] == 35

    def test_ability_fields(self):
        data = client.get("/builds/defaults").json()
        ability = data["classes"][0]["abilities"][0]
        for field in ("id", "name", "pa_cost", "cooldown", "max_range", "target"):
            assert field in ability, f"Missing field: {field}"

    def test_default_build_points_sum_10(self):
        data = client.get("/builds/defaults").json()
        for build in data["default_builds"]:
            assert sum(build["attribute_points"]) == 10
            assert all(0 <= v <= 5 for v in build["attribute_points"])

    def test_default_warrior_build(self):
        data = client.get("/builds/defaults").json()
        warrior_build = next(
            b for b in data["default_builds"] if b["class_id"] == "warrior"
        )
        assert warrior_build["attribute_points"] == [5, 2, 3, 0, 0]

    def test_default_mage_build(self):
        data = client.get("/builds/defaults").json()
        mage_build = next(b for b in data["default_builds"] if b["class_id"] == "mage")
        assert mage_build["attribute_points"] == [0, 0, 2, 5, 3]

    def test_default_cleric_build(self):
        data = client.get("/builds/defaults").json()
        cleric_build = next(
            b for b in data["default_builds"] if b["class_id"] == "cleric"
        )
        assert cleric_build["attribute_points"] == [0, 0, 5, 0, 5]

    def test_default_archer_build(self):
        data = client.get("/builds/defaults").json()
        archer_build = next(
            b for b in data["default_builds"] if b["class_id"] == "archer"
        )
        assert archer_build["attribute_points"] == [2, 5, 3, 0, 0]

    def test_default_assassin_build(self):
        data = client.get("/builds/defaults").json()
        assassin_build = next(
            b for b in data["default_builds"] if b["class_id"] == "assassin"
        )
        assert assassin_build["attribute_points"] == [3, 5, 2, 0, 0]

    def test_default_build_ability_ids_valid(self):
        data = client.get("/builds/defaults").json()
        for build in data["default_builds"]:
            assert len(build["ability_ids"]) == 5
            cls_info = next(
                c for c in data["classes"] if c["class_id"] == build["class_id"]
            )
            available_ids = {a["id"] for a in cls_info["abilities"]}
            for aid in build["ability_ids"]:
                assert aid in available_ids, (
                    f"Ability {aid} not in {build['class_id']} class"
                )

    def test_all_class_ids_present(self):
        data = client.get("/builds/defaults").json()
        class_ids = {c["class_id"] for c in data["classes"]}
        assert class_ids == {"warrior", "mage", "cleric", "archer", "assassin"}


# ---------------------------------------------------------------------------
# POST /battle/start — success
# ---------------------------------------------------------------------------


class TestBattleStartSuccess:
    def _start_battle(self, team, difficulty="normal"):
        return client.post(
            "/battle/start",
            json={"difficulty": difficulty, "team": team},
        )

    def test_valid_1v1(self):
        r = self._start_battle([VALID_WARRIOR_REQUEST])
        assert r.status_code == 201
        data = r.json()
        assert "session_id" in data
        assert "initial_state" in data
        uuid.UUID(data["session_id"])

    def test_valid_3v3(self):
        r = self._start_battle(
            [VALID_WARRIOR_REQUEST, VALID_MAGE_REQUEST, VALID_ARCHER_REQUEST]
        )
        assert r.status_code == 201
        chars = r.json()["initial_state"]["characters"]
        assert len(chars) == 6
        player_chars = [c for c in chars if c["team"] == "player"]
        ai_chars = [c for c in chars if c["team"] == "ai"]
        assert len(player_chars) == 3
        assert len(ai_chars) == 3

    def test_initial_state_structure(self):
        r = self._start_battle([VALID_WARRIOR_REQUEST])
        state = r.json()["initial_state"]
        assert "grid_size" in state
        assert state["grid_size"]["width"] == 10
        assert state["grid_size"]["height"] == 8
        assert "map_objects" in state
        assert "characters" in state
        assert "turn_order" in state
        assert "current_character" in state

    def test_character_fields(self):
        r = self._start_battle([VALID_WARRIOR_REQUEST])
        chars = r.json()["initial_state"]["characters"]
        for char in chars:
            assert "entity_id" in char
            assert "team" in char
            assert char["team"] in ("player", "ai")
            assert "class_id" in char
            assert "attributes" in char
            assert "current_hp" in char
            assert "max_hp" in char
            assert "position" in char
            assert "x" in char["position"]
            assert "y" in char["position"]
            assert "abilities" in char

    def test_player_character_has_correct_attributes(self):
        r = self._start_battle([VALID_WARRIOR_REQUEST])
        chars = r.json()["initial_state"]["characters"]
        player_warrior = next(c for c in chars if c["team"] == "player")
        assert player_warrior["class_id"] == "warrior"
        attrs = player_warrior["attributes"]
        assert attrs["str"] == 8 + 5  # base 8 + build 5 = 13
        assert attrs["dex"] == 4 + 2  # base 4 + build 2 = 6
        assert attrs["con"] == 7 + 3  # base 7 + build 3 = 10

    def test_player_character_hp(self):
        r = self._start_battle([VALID_WARRIOR_REQUEST])
        chars = r.json()["initial_state"]["characters"]
        player_warrior = next(c for c in chars if c["team"] == "player")
        # HP = hp_base + (mod_CON * 5) = 50 + ((10 - 5) * 5) = 50 + 25 = 75
        assert player_warrior["max_hp"] == 75
        assert player_warrior["current_hp"] == 75

    def test_turn_order_includes_all(self):
        r = self._start_battle([VALID_WARRIOR_REQUEST])
        state = r.json()["initial_state"]
        entity_ids = {c["entity_id"] for c in state["characters"]}
        turn_order_set = set(state["turn_order"])
        assert entity_ids == turn_order_set

    def test_current_character_in_turn_order(self):
        r = self._start_battle([VALID_WARRIOR_REQUEST])
        state = r.json()["initial_state"]
        assert state["current_character"] in state["turn_order"]
        assert state["current_character"] == state["turn_order"][0]

    def test_map_objects_have_correct_fields(self):
        r = self._start_battle([VALID_WARRIOR_REQUEST])
        objects = r.json()["initial_state"]["map_objects"]
        assert len(objects) > 0
        for obj in objects:
            assert "entity_id" in obj
            assert "object_type" in obj
            assert "position" in obj
            assert "x" in obj["position"]
            assert "y" in obj["position"]
            assert "blocks_movement" in obj
            assert "blocks_los" in obj
            assert "hp" in obj

    def test_all_difficulty_levels(self):
        for difficulty in ("easy", "normal", "hard"):
            r = self._start_battle([VALID_WARRIOR_REQUEST], difficulty=difficulty)
            assert r.status_code == 201

    def test_ai_team_no_duplicate_classes(self):
        r = self._start_battle(
            [VALID_WARRIOR_REQUEST, VALID_MAGE_REQUEST, VALID_ARCHER_REQUEST]
        )
        chars = r.json()["initial_state"]["characters"]
        ai_classes = [c["class_id"] for c in chars if c["team"] == "ai"]
        assert len(ai_classes) == len(set(ai_classes))

    def test_player_abilities_match_request(self):
        r = self._start_battle([VALID_WARRIOR_REQUEST])
        chars = r.json()["initial_state"]["characters"]
        player = next(c for c in chars if c["team"] == "player")
        ability_ids = {a["id"] for a in player["abilities"]}
        for aid in VALID_WARRIOR_REQUEST["ability_ids"]:
            assert aid in ability_ids


# ---------------------------------------------------------------------------
# POST /battle/start — validation errors
# ---------------------------------------------------------------------------


class TestBattleStartValidation:
    def _start_battle(self, team=None, difficulty="normal"):
        payload = {"difficulty": difficulty, "team": team or []}
        return client.post("/battle/start", json=payload)

    def test_empty_team(self):
        r = self._start_battle(team=[])
        assert r.status_code == 422

    def test_team_too_large(self):
        chars = []
        for cls_id, build in [
            ("warrior", [5, 2, 3, 0, 0]),
            ("mage", [0, 0, 2, 5, 3]),
            ("archer", [2, 5, 3, 0, 0]),
            ("assassin", [3, 5, 2, 0, 0]),
        ]:
            chars.append(
                {
                    "class_id": cls_id,
                    "attribute_points": build,
                    "ability_ids": VALID_WARRIOR_REQUEST["ability_ids"]
                    if cls_id == "warrior"
                    else VALID_MAGE_REQUEST["ability_ids"]
                    if cls_id == "mage"
                    else VALID_ARCHER_REQUEST["ability_ids"]
                    if cls_id == "archer"
                    else [
                        "lamina_oculta",
                        "passo_sombrio",
                        "danca_das_laminas",
                        "tiro_certeiro",
                        "corte_profundo",
                    ],
                }
            )
        r = self._start_battle(team=chars)
        assert r.status_code == 422

    def test_duplicate_classes(self):
        r = self._start_battle(team=[VALID_WARRIOR_REQUEST, VALID_WARRIOR_REQUEST])
        assert r.status_code == 422

    def test_invalid_build_sum_too_high(self):
        bad_char = {
            **VALID_WARRIOR_REQUEST,
            "attribute_points": [5, 2, 3, 1, 0],  # sum = 11
        }
        r = self._start_battle(team=[bad_char])
        assert r.status_code == 422

    def test_invalid_build_sum_too_low(self):
        bad_char = {
            **VALID_WARRIOR_REQUEST,
            "attribute_points": [5, 2, 2, 0, 0],  # sum = 9
        }
        r = self._start_battle(team=[bad_char])
        assert r.status_code == 422

    def test_invalid_build_cap_exceeded(self):
        bad_char = {
            **VALID_WARRIOR_REQUEST,
            "attribute_points": [6, 2, 2, 0, 0],  # cap exceeded
        }
        r = self._start_battle(team=[bad_char])
        assert r.status_code == 422

    def test_invalid_build_negative(self):
        bad_char = {
            **VALID_WARRIOR_REQUEST,
            "attribute_points": [-1, 5, 3, 3, 0],
        }
        r = self._start_battle(team=[bad_char])
        assert r.status_code == 422

    def test_invalid_ability_for_class(self):
        bad_char = {
            **VALID_WARRIOR_REQUEST,
            "ability_ids": [
                "impacto_brutal",
                "muralha_de_ferro",
                "investida",
                "corte_profundo",
                "estilhaco_arcano",  # mage-only ability
            ],
        }
        r = self._start_battle(team=[bad_char])
        assert r.status_code == 422

    def test_duplicate_abilities(self):
        bad_char = {
            **VALID_WARRIOR_REQUEST,
            "ability_ids": [
                "impacto_brutal",
                "impacto_brutal",
                "investida",
                "corte_profundo",
                "sentenca_do_carrasco",
            ],
        }
        r = self._start_battle(team=[bad_char])
        assert r.status_code == 422

    def test_wrong_ability_count_too_few(self):
        bad_char = {
            **VALID_WARRIOR_REQUEST,
            "ability_ids": ["impacto_brutal", "muralha_de_ferro"],
        }
        r = self._start_battle(team=[bad_char])
        assert r.status_code == 422

    def test_wrong_ability_count_too_many(self):
        bad_char = {
            **VALID_WARRIOR_REQUEST,
            "ability_ids": [
                "impacto_brutal",
                "muralha_de_ferro",
                "investida",
                "corte_profundo",
                "sentenca_do_carrasco",
                "grito_de_guerra",
            ],
        }
        r = self._start_battle(team=[bad_char])
        assert r.status_code == 422

    def test_invalid_difficulty(self):
        r = self._start_battle(team=[VALID_WARRIOR_REQUEST], difficulty="impossible")
        assert r.status_code == 422

    def test_invalid_class_id(self):
        bad_char = {
            **VALID_WARRIOR_REQUEST,
            "class_id": "necromancer",
        }
        r = self._start_battle(team=[bad_char])
        assert r.status_code == 422

    def test_wrong_attribute_points_length(self):
        bad_char = {
            **VALID_WARRIOR_REQUEST,
            "attribute_points": [5, 2, 3],  # only 3 values
        }
        r = self._start_battle(team=[bad_char])
        assert r.status_code == 422
