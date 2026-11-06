import { GoogleGenerativeAI, HarmCategory, HarmBlockThreshold } from '@google/generative-ai';
import { toolDeclarations, executeTool } from './agentTools';
import { GeminiHistoryEntry } from './types';

// ─── System prompt ────────────────────────────────────────────────────────────

const SYSTEM_PROMPT = `You are KIRA, a smart voice assistant that helps users complete real-world tasks through voice commands.

Your capabilities:
- Answer any question using your knowledge or web search
- Find YouTube tutorials and educational videos
- Find free online courses and certifications
- Compare platforms and services and recommend the best one
- Provide step-by-step guidance for tasks like booking tickets (search the booking site, get details, and explain the steps)

Voice response guidelines:
- Keep responses concise — they will be spoken aloud by text-to-speech
- Use plain language without markdown symbols, bullet dashes, or asterisks (these sound weird when spoken)
- When using search tools, briefly say what you found
- Be action-oriented and always try to complete the task fully
- For booking tasks: find the relevant website, explain the process, and give the direct URL`;

// ─── Main chat function ───────────────────────────────────────────────────────

/**
 * Send a message to Gemini 1.5 Flash, automatically running tool calls
 * until the model produces a final text response.
 *
 * @param userMessage   The user's transcribed text
 * @param history       Previous conversation turns (user/model alternating)
 * @param geminiKey     Google AI Studio API key
 * @param tavilyKey     Optional Tavily API key for better web search
 * @param onToolUse     Callback fired each time a tool is invoked (for UI feedback)
 */
export async function chatWithGemini(
  userMessage: string,
  history: GeminiHistoryEntry[],
  geminiKey: string,
  tavilyKey?: string | null,
  onToolUse?: (toolName: string) => void
): Promise<string> {
  const genAI = new GoogleGenerativeAI(geminiKey);

  const model = genAI.getGenerativeModel({
    model: 'gemini-1.5-flash',
    systemInstruction: SYSTEM_PROMPT,
    tools: [{ functionDeclarations: toolDeclarations }],
    generationConfig: {
      temperature: 0.7,
      maxOutputTokens: 1024,
    },
    safetySettings: [
      {
        category: HarmCategory.HARM_CATEGORY_HARASSMENT,
        threshold: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
      },
      {
        category: HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        threshold: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
      },
    ],
  });

  const chat = model.startChat({ history });

  // Initial user message
  let response = await chat.sendMessage(userMessage);

  // ── Agentic tool-calling loop ──────────────────────────────────────────────
  const MAX_TOOL_ITERATIONS = 5;
  let iterations = 0;

  while (iterations < MAX_TOOL_ITERATIONS) {
    const functionCalls = response.response.functionCalls();
    if (!functionCalls || functionCalls.length === 0) break; // No more tool calls

    // Execute all requested tools (may be parallel)
    const toolResults = await Promise.all(
      functionCalls.map(async (call) => {
        onToolUse?.(call.name); // Notify UI
        const result = await executeTool(
          call.name,
          call.args as Record<string, any>,
          tavilyKey
        );
        return {
          functionResponse: {
            name: call.name,
            response: { result },
          },
        };
      })
    );

    // Return tool results to Gemini for its next response
    response = await chat.sendMessage(toolResults);
    iterations++;
  }

  return response.response.text();
}
