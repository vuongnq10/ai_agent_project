import { BOT_BASE_URL } from "./config";

export type AgentId = string;

export interface AIModel {
  id: AgentId;
  label: string;
  model: string;
}

export async function fetchModels(): Promise<AIModel[]> {
  const res = await fetch(`${BOT_BASE_URL}/trading/models`);
  return res.json();
}

export function streamChat(
  query: string,
  agent: AgentId,
  onCharacter: (char: string) => void,
  onEnd: () => void,
  onError: () => void
): EventSource {
  const eventSource = new EventSource(
    `${BOT_BASE_URL}/${agent}/stream?query=${encodeURIComponent(query)}`
  );

  eventSource.onmessage = (event) => {
    const { character } = JSON.parse(event.data);
    onCharacter(character);
  };

  eventSource.addEventListener("end", () => {
    eventSource.close();
    onEnd();
  });

  eventSource.onerror = () => {
    eventSource.close();
    onError();
  };

  return eventSource;
}
