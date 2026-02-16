import { z } from "zod";
import {
  RunStartEvent,
  StepStartEvent,
  StepResultEvent,
  CompileIterEvent,
  ReconResultEvent,
  CriticResultEvent,
  FailureEvent,
  RepairStartEvent,
  RunEndEvent,
} from "./schemas";

const SSE_EVENT_TYPES = [
  "connected",
  "run_start",
  "step_start",
  "step_result",
  "compile_iter",
  "recon_result",
  "critic_result",
  "failure",
  "repair_start",
  "run_end",
] as const;

export type SSEEventType = (typeof SSE_EVENT_TYPES)[number];

/** Strongly typed map: each SSE event type → its Zod-inferred TypeScript type. */
export interface SSEEventMap {
  connected: Record<string, never>;
  run_start: z.infer<typeof RunStartEvent>;
  step_start: z.infer<typeof StepStartEvent>;
  step_result: z.infer<typeof StepResultEvent>;
  compile_iter: z.infer<typeof CompileIterEvent>;
  recon_result: z.infer<typeof ReconResultEvent>;
  critic_result: z.infer<typeof CriticResultEvent>;
  failure: z.infer<typeof FailureEvent>;
  repair_start: z.infer<typeof RepairStartEvent>;
  run_end: z.infer<typeof RunEndEvent>;
}

/** Union of all SSE event payloads. */
export type SSEEventData = SSEEventMap[SSEEventType];

/** Handler receives event type + its typed payload. */
export type SSEHandler = (eventType: SSEEventType, data: SSEEventData) => void;

const EVENT_SCHEMAS: Partial<Record<SSEEventType, z.ZodType>> = {
  run_start: RunStartEvent,
  step_start: StepStartEvent,
  step_result: StepResultEvent,
  compile_iter: CompileIterEvent,
  recon_result: ReconResultEvent,
  critic_result: CriticResultEvent,
  failure: FailureEvent,
  repair_start: RepairStartEvent,
  run_end: RunEndEvent,
};

export function createSSEClient(url: string, onEvent: SSEHandler): () => void {
  const es = new EventSource(url);

  for (const eventType of SSE_EVENT_TYPES) {
    es.addEventListener(eventType, (e: MessageEvent) => {
      try {
        const raw = JSON.parse(e.data);
        const schema = EVENT_SCHEMAS[eventType];
        if (schema) {
          const result = schema.safeParse(raw);
          if (!result.success) {
            console.error(`SSE ${eventType} validation failed:`, result.error.format());
            return;
          }
          onEvent(eventType, result.data as SSEEventData);
        } else {
          onEvent(eventType, raw as SSEEventData);
        }
      } catch {
        console.warn(`Failed to parse SSE data for ${eventType}:`, e.data);
      }
    });
  }

  es.onerror = () => {
    console.warn("SSE connection error — EventSource will auto-reconnect");
  };

  return () => es.close();
}
