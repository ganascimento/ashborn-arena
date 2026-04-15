import type { ServerMessage, WsHandlers } from "./types";

export const WS_BASE_URL = "ws://localhost:8000";

export class BattleWsClient {
  private sessionId: string;
  private handlers: WsHandlers;
  private ws: WebSocket | null = null;

  constructor(sessionId: string, handlers: WsHandlers) {
    this.sessionId = sessionId;
    this.handlers = handlers;
  }

  connect(): void {
    this.ws = new WebSocket(`${WS_BASE_URL}/battle/${this.sessionId}`);

    this.ws.onmessage = (event: MessageEvent) => {
      let msg: ServerMessage;
      try {
        msg = JSON.parse(event.data);
      } catch {
        console.warn("WS: malformed JSON received", event.data);
        return;
      }
      this.dispatch(msg);
    };

    this.ws.onclose = () => {
      this.handlers.onDisconnect();
    };

    this.ws.onerror = () => {
      this.handlers.onDisconnect();
    };
  }

  sendMove(character: string, target: [number, number]): void {
    this.send({ type: "action", character, action: "move", target });
  }

  sendBasicAttack(character: string, target: [number, number]): void {
    this.send({ type: "action", character, action: "basic_attack", target });
  }

  sendAbility(
    character: string,
    ability: string,
    target: [number, number],
  ): void {
    this.send({ type: "action", character, action: "ability", ability, target });
  }

  sendEndTurn(character: string): void {
    this.send({ type: "action", character, action: "end_turn" });
  }

  sendReady(): void {
    this.send({ type: "ready" });
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
    }
  }

  private send(data: unknown): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.warn("WS: message dropped, socket not open", data);
      return;
    }
    this.ws.send(JSON.stringify(data));
  }

  private dispatch(msg: ServerMessage): void {
    switch (msg.type) {
      case "turn_start":
        this.handlers.onTurnStart(msg);
        break;
      case "action_result":
        this.handlers.onActionResult(msg);
        break;
      case "ai_action":
        this.handlers.onAiAction(msg);
        break;
      case "turn_end":
        this.handlers.onTurnEnd(msg);
        break;
      case "skip_event":
        this.handlers.onSkipEvent(msg);
        break;
      case "battle_end":
        this.handlers.onBattleEnd(msg);
        break;
      case "error":
        this.handlers.onError(msg);
        break;
    }
  }
}
