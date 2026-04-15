import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { BattleWsClient, WS_BASE_URL } from "../ws-client";
import type { WsHandlers } from "../types";

let mockWsInstances: MockWebSocket[] = [];

class MockWebSocket {
  static readonly CONNECTING = 0;
  static readonly OPEN = 1;
  static readonly CLOSING = 2;
  static readonly CLOSED = 3;

  url: string;
  readyState = MockWebSocket.OPEN;
  onopen: (() => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: ((event: unknown) => void) | null = null;
  send = vi.fn();
  close = vi.fn();

  constructor(url: string) {
    this.url = url;
    mockWsInstances.push(this);
  }
}

function createHandlers(): WsHandlers {
  return {
    onTurnStart: vi.fn(),
    onActionResult: vi.fn(),
    onAiAction: vi.fn(),
    onTurnEnd: vi.fn(),
    onSkipEvent: vi.fn(),
    onBattleEnd: vi.fn(),
    onError: vi.fn(),
    onDisconnect: vi.fn(),
  };
}

describe("BattleWsClient", () => {
  beforeEach(() => {
    mockWsInstances = [];
    vi.stubGlobal("WebSocket", MockWebSocket);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("connect", () => {
    it("creates WebSocket with correct URL", () => {
      const handlers = createHandlers();
      const client = new BattleWsClient("session-abc", handlers);
      client.connect();

      expect(mockWsInstances).toHaveLength(1);
      expect(mockWsInstances[0].url).toBe(
        `${WS_BASE_URL}/battle/session-abc`,
      );
    });
  });

  describe("message dispatch", () => {
    it("dispatches turn_start to onTurnStart handler", () => {
      const handlers = createHandlers();
      const client = new BattleWsClient("s1", handlers);
      client.connect();

      const msg = {
        type: "turn_start",
        character: "warrior_p1",
        pa: 4,
        events: [],
      };
      mockWsInstances[0].onmessage!({ data: JSON.stringify(msg) });

      expect(handlers.onTurnStart).toHaveBeenCalledOnce();
      expect(handlers.onTurnStart).toHaveBeenCalledWith(msg);
    });

    it("dispatches action_result to onActionResult handler", () => {
      const handlers = createHandlers();
      const client = new BattleWsClient("s1", handlers);
      client.connect();

      const msg = {
        type: "action_result",
        character: "warrior_p1",
        action: "move",
        events: [{ type: "move", entity: "warrior_p1", to: [3, 4] }],
      };
      mockWsInstances[0].onmessage!({ data: JSON.stringify(msg) });

      expect(handlers.onActionResult).toHaveBeenCalledOnce();
      expect(handlers.onActionResult).toHaveBeenCalledWith(msg);
    });

    it("dispatches ai_action to onAiAction handler", () => {
      const handlers = createHandlers();
      const client = new BattleWsClient("s1", handlers);
      client.connect();

      const msg = {
        type: "ai_action",
        character: "mage_ai",
        action: "move",
        events: [],
      };
      mockWsInstances[0].onmessage!({ data: JSON.stringify(msg) });

      expect(handlers.onAiAction).toHaveBeenCalledOnce();
      expect(handlers.onAiAction).toHaveBeenCalledWith(msg);
    });

    it("dispatches turn_end to onTurnEnd handler", () => {
      const handlers = createHandlers();
      const client = new BattleWsClient("s1", handlers);
      client.connect();

      const msg = {
        type: "turn_end",
        character: "warrior_p1",
        next: "mage_ai",
      };
      mockWsInstances[0].onmessage!({ data: JSON.stringify(msg) });

      expect(handlers.onTurnEnd).toHaveBeenCalledOnce();
      expect(handlers.onTurnEnd).toHaveBeenCalledWith(msg);
    });

    it("dispatches skip_event to onSkipEvent handler", () => {
      const handlers = createHandlers();
      const client = new BattleWsClient("s1", handlers);
      client.connect();

      const msg = {
        type: "skip_event",
        character: "dead_char",
        reason: "knocked_out",
      };
      mockWsInstances[0].onmessage!({ data: JSON.stringify(msg) });

      expect(handlers.onSkipEvent).toHaveBeenCalledOnce();
      expect(handlers.onSkipEvent).toHaveBeenCalledWith(msg);
    });

    it("dispatches battle_end to onBattleEnd handler", () => {
      const handlers = createHandlers();
      const client = new BattleWsClient("s1", handlers);
      client.connect();

      const msg = { type: "battle_end", result: "victory" };
      mockWsInstances[0].onmessage!({ data: JSON.stringify(msg) });

      expect(handlers.onBattleEnd).toHaveBeenCalledOnce();
      expect(handlers.onBattleEnd).toHaveBeenCalledWith(msg);
    });

    it("dispatches error to onError handler", () => {
      const handlers = createHandlers();
      const client = new BattleWsClient("s1", handlers);
      client.connect();

      const msg = { type: "error", message: "Invalid action" };
      mockWsInstances[0].onmessage!({ data: JSON.stringify(msg) });

      expect(handlers.onError).toHaveBeenCalledOnce();
      expect(handlers.onError).toHaveBeenCalledWith(msg);
    });

    it("does not crash on malformed JSON", () => {
      const handlers = createHandlers();
      const client = new BattleWsClient("s1", handlers);
      client.connect();

      expect(() => {
        mockWsInstances[0].onmessage!({ data: "not json{{{" });
      }).not.toThrow();
    });

    it("does not crash on unknown message type", () => {
      const handlers = createHandlers();
      const client = new BattleWsClient("s1", handlers);
      client.connect();

      expect(() => {
        mockWsInstances[0].onmessage!({
          data: JSON.stringify({ type: "unknown_type", data: 123 }),
        });
      }).not.toThrow();
    });
  });

  describe("send methods", () => {
    it("sendMove sends correct JSON", () => {
      const handlers = createHandlers();
      const client = new BattleWsClient("s1", handlers);
      client.connect();

      client.sendMove("warrior_p1", [5, 3]);

      expect(mockWsInstances[0].send).toHaveBeenCalledOnce();
      const sent = JSON.parse(mockWsInstances[0].send.mock.calls[0][0]);
      expect(sent).toEqual({
        type: "action",
        character: "warrior_p1",
        action: "move",
        target: [5, 3],
      });
    });

    it("sendBasicAttack sends correct JSON", () => {
      const handlers = createHandlers();
      const client = new BattleWsClient("s1", handlers);
      client.connect();

      client.sendBasicAttack("warrior_p1", [7, 2]);

      expect(mockWsInstances[0].send).toHaveBeenCalledOnce();
      const sent = JSON.parse(mockWsInstances[0].send.mock.calls[0][0]);
      expect(sent).toEqual({
        type: "action",
        character: "warrior_p1",
        action: "basic_attack",
        target: [7, 2],
      });
    });

    it("sendAbility sends correct JSON with ability field", () => {
      const handlers = createHandlers();
      const client = new BattleWsClient("s1", handlers);
      client.connect();

      client.sendAbility("mage_p1", "nova_flamejante", [4, 4]);

      expect(mockWsInstances[0].send).toHaveBeenCalledOnce();
      const sent = JSON.parse(mockWsInstances[0].send.mock.calls[0][0]);
      expect(sent).toEqual({
        type: "action",
        character: "mage_p1",
        action: "ability",
        ability: "nova_flamejante",
        target: [4, 4],
      });
    });

    it("sendEndTurn sends correct JSON without target", () => {
      const handlers = createHandlers();
      const client = new BattleWsClient("s1", handlers);
      client.connect();

      client.sendEndTurn("warrior_p1");

      expect(mockWsInstances[0].send).toHaveBeenCalledOnce();
      const sent = JSON.parse(mockWsInstances[0].send.mock.calls[0][0]);
      expect(sent).toEqual({
        type: "action",
        character: "warrior_p1",
        action: "end_turn",
      });
    });

    it("sendReady sends ready message", () => {
      const handlers = createHandlers();
      const client = new BattleWsClient("s1", handlers);
      client.connect();

      client.sendReady();

      expect(mockWsInstances[0].send).toHaveBeenCalledOnce();
      const sent = JSON.parse(mockWsInstances[0].send.mock.calls[0][0]);
      expect(sent).toEqual({ type: "ready" });
    });

    it("does not send when readyState is not OPEN", () => {
      const handlers = createHandlers();
      const client = new BattleWsClient("s1", handlers);
      client.connect();

      mockWsInstances[0].readyState = 3; // CLOSED
      client.sendMove("warrior_p1", [5, 3]);

      expect(mockWsInstances[0].send).not.toHaveBeenCalled();
    });
  });

  describe("disconnect", () => {
    it("calls ws.close()", () => {
      const handlers = createHandlers();
      const client = new BattleWsClient("s1", handlers);
      client.connect();

      client.disconnect();

      expect(mockWsInstances[0].close).toHaveBeenCalledOnce();
    });
  });

  describe("connection events", () => {
    it("calls onDisconnect when ws closes", () => {
      const handlers = createHandlers();
      const client = new BattleWsClient("s1", handlers);
      client.connect();

      mockWsInstances[0].onclose!();

      expect(handlers.onDisconnect).toHaveBeenCalledOnce();
    });

    it("calls onDisconnect when ws errors", () => {
      const handlers = createHandlers();
      const client = new BattleWsClient("s1", handlers);
      client.connect();

      mockWsInstances[0].onerror!(new Event("error"));

      expect(handlers.onDisconnect).toHaveBeenCalledOnce();
    });
  });
});
