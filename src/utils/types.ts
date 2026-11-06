export type Message = {
  id: string;
  from: 'kira' | 'user';
  text: string;
  ts?: number;
  /** When true, this bubble shows a live status / thinking indicator */
  isThinking?: boolean;
};

/** Gemini conversation history entry (role/parts format required by the SDK) */
export type GeminiHistoryEntry = {
  role: 'user' | 'model';
  parts: Array<{ text: string }>;
};
