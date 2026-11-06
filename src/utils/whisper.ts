import * as FileSystem from 'expo-file-system';

/**
 * Uploads an audio file to OpenAI Whisper (transcriptions endpoint) and returns the transcript.
 * Notes:
 * - Requires a valid OpenAI API key.
 * - This is a minimal implementation using fetch and FormData.
 */
export async function transcribeWithWhisper(fileUri: string, openAiKey: string): Promise<string | null> {
  // Read file into binary
  const fileInfo = await FileSystem.getInfoAsync(fileUri);
  if (!fileInfo.exists) throw new Error('Audio file not found: ' + fileUri);

  // Expo FileSystem doesn't expose a Node-style file stream, but fetch with FormData supports local URIs in Expo.
  const apiUrl = 'https://api.openai.com/v1/audio/transcriptions';

  const formData = new FormData();
  // @ts-ignore: React Native FormData file object
  formData.append('file', {
    uri: fileUri,
    type: 'audio/x-wav',
    name: 'recording.wav',
  });
  formData.append('model', 'gpt-4o-transcribe');

  const res = await fetch(apiUrl, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${openAiKey}`,
      // 'Content-Type' must NOT be set explicitly when sending FormData in RN/fetch
    },
    body: formData as any,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error('Whisper API error: ' + res.status + ' ' + text);
  }

  const data = await res.json();
  // The response shape may vary; commonly { text: '...' }
  return data.text ?? data.transcription ?? JSON.stringify(data);
}
