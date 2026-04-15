export interface EffectOut {
  tag: string;
  duration: number;
  target: string;
}

export interface AbilityOut {
  id: string;
  name: string;
  pa_cost: number;
  cooldown: number;
  max_range: number;
  target: string;
  damage_base: number;
  damage_type: string;
  heal_base: number;
  elemental_tag: string;
  effects: EffectOut[];
  movement_type: string;
}

export interface ClassInfo {
  class_id: string;
  base_attributes: Record<string, number>;
  hp_base: number;
  abilities: AbilityOut[];
}

export interface DefaultBuild {
  class_id: string;
  attribute_points: number[];
  ability_ids: string[];
}

export interface BuildsDefaultsResponse {
  classes: ClassInfo[];
  default_builds: DefaultBuild[];
}

export interface CharacterRequest {
  class_id: string;
  attribute_points: number[];
  ability_ids: string[];
}

export interface BattleStartRequest {
  difficulty: string;
  team: CharacterRequest[];
}

export interface PositionOut {
  x: number;
  y: number;
}

export interface CharacterOut {
  entity_id: string;
  team: string;
  class_id: string;
  attributes: Record<string, number>;
  current_hp: number;
  max_hp: number;
  position: PositionOut;
  abilities: AbilityOut[];
}

export interface MapObjectOut {
  entity_id: string;
  object_type: string;
  position: PositionOut;
  hp: number | null;
  max_hp: number | null;
  blocks_movement: boolean;
  blocks_los: boolean;
}

export interface InitialBattleState {
  grid_size: { width: number; height: number };
  map_objects: MapObjectOut[];
  characters: CharacterOut[];
  turn_order: string[];
  current_character: string;
}

export interface BattleStartResponse {
  session_id: string;
  initial_state: InitialBattleState;
}

export interface SavedBuild {
  attribute_points: number[];
  ability_ids: string[];
}

// WebSocket message types — server to client

export interface WsTurnStart {
  type: "turn_start";
  character: string;
  pa: number;
  events: unknown[];
}

export interface WsActionResult {
  type: "action_result";
  character: string;
  action: string;
  ability?: string;
  pa: number;
  events: unknown[];
}

export interface WsAiAction {
  type: "ai_action";
  character: string;
  action: string;
  events: unknown[];
}

export interface WsTurnEnd {
  type: "turn_end";
  character: string;
  next: string;
}

export interface WsSkipEvent {
  type: "skip_event";
  [key: string]: unknown;
}

export interface WsBattleEnd {
  type: "battle_end";
  result: "victory" | "defeat";
}

export interface WsError {
  type: "error";
  message: string;
}

export type ServerMessage =
  | WsTurnStart
  | WsActionResult
  | WsAiAction
  | WsTurnEnd
  | WsSkipEvent
  | WsBattleEnd
  | WsError;

// WebSocket message types — client to server

export interface PlayerMoveAction {
  type: "action";
  character: string;
  action: "move";
  target: [number, number];
}

export interface PlayerAttackAction {
  type: "action";
  character: string;
  action: "basic_attack";
  target: [number, number];
}

export interface PlayerAbilityAction {
  type: "action";
  character: string;
  action: "ability";
  ability: string;
  target: [number, number];
}

export interface PlayerEndTurnAction {
  type: "action";
  character: string;
  action: "end_turn";
}

export interface PlayerReady {
  type: "ready";
}

export type ClientMessage =
  | PlayerMoveAction
  | PlayerAttackAction
  | PlayerAbilityAction
  | PlayerEndTurnAction
  | PlayerReady;

// WebSocket handler interface

export interface WsHandlers {
  onTurnStart: (msg: WsTurnStart) => void;
  onActionResult: (msg: WsActionResult) => void;
  onAiAction: (msg: WsAiAction) => void;
  onTurnEnd: (msg: WsTurnEnd) => void;
  onSkipEvent: (msg: WsSkipEvent) => void;
  onBattleEnd: (msg: WsBattleEnd) => void;
  onError: (msg: WsError) => void;
  onDisconnect: () => void;
}
