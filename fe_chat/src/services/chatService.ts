import { BOT_BASE_URL } from "./config";

export function streamChat(
  query: string,
  onCharacter: (char: string) => void,
  onEnd: () => void,
  onError: () => void
): EventSource {
  const eventSource = new EventSource(
    `${BOT_BASE_URL}/gemini/stream?query=${encodeURIComponent(query)}`
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
