import React, { useEffect, useRef, useState } from 'react';
import {
  View,
  StyleSheet,
  FlatList,
  Text,
  Platform,
  Animated,
} from 'react-native';
import { Button, IconButton, Paragraph, Avatar, useTheme, Banner } from 'react-native-paper';
import * as Speech from 'expo-speech';
import { Audio } from 'expo-av';
import * as FileSystem from 'expo-file-system';
import { transcribeWithWhisper } from '../utils/whisper';
import { chatWithGemini } from '../utils/gemini';
import { Message, GeminiHistoryEntry } from '../utils/types';

// ─── Tool display labels ──────────────────────────────────────────────────────

const TOOL_LABELS: Record<string, string> = {
  search_web: '🔍 Searching the web...',
  search_youtube: '▶️ Searching YouTube...',
  find_courses: '📚 Finding free courses...',
  compare_platforms: '⚖️ Comparing platforms...',
};

// ─── Lazy-load native voice module (avoid bundling on web) ───────────────────

let VoiceModule: any = null;
if (Platform.OS !== 'web') {
  try {
    const mod = require('@react-native-voice/voice');
    VoiceModule = mod.default ?? mod;
  } catch {
    VoiceModule = null;
  }
}

type Props = {
  openAiKey?: string | null;
  geminiKey?: string | null;
  tavilyKey?: string | null;
};

export default function AssistantUI({ openAiKey, geminiKey, tavilyKey }: Props) {
  const theme = useTheme();

  // ── Core state ──────────────────────────────────────────────────────────────
  const [messages, setMessages] = useState<Message[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [listening, setListening] = useState(false);
  const [lastRecordingUri, setLastRecordingUri] = useState<string | null>(null);
  const [isThinking, setIsThinking] = useState(false);
  const [geminiHistory, setGeminiHistory] = useState<GeminiHistoryEntry[]>([]);

  // ── Refs ────────────────────────────────────────────────────────────────────
  const recordingRef = useRef<Audio.Recording | null>(null);
  const webRecognizerRef = useRef<any | null>(null);
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const pulseOpacity = useRef(new Animated.Value(0)).current;
  const pulseLoopRef = useRef<Animated.CompositeAnimation | null>(null);

  // ── Helpers ─────────────────────────────────────────────────────────────────
  const tsNow = () => Date.now();

  const addMessage = (m: Message) => setMessages(s => [m, ...s]);

  const replaceMessage = (id: string, m: Message) =>
    setMessages(s => [m, ...s.filter(x => x.id !== id)]);

  // ── Pulse animation (mic active) ────────────────────────────────────────────
  useEffect(() => {
    if (isRecording || listening) {
      const loop = Animated.loop(
        Animated.parallel([
          Animated.sequence([
            Animated.timing(pulseAnim, { toValue: 1.4, duration: 600, useNativeDriver: true }),
            Animated.timing(pulseAnim, { toValue: 1, duration: 600, useNativeDriver: true }),
          ]),
          Animated.sequence([
            Animated.timing(pulseOpacity, { toValue: 0.5, duration: 600, useNativeDriver: true }),
            Animated.timing(pulseOpacity, { toValue: 0, duration: 600, useNativeDriver: true }),
          ]),
        ])
      );
      pulseLoopRef.current = loop;
      loop.start();
    } else {
      pulseLoopRef.current?.stop();
      pulseLoopRef.current = null;
      pulseAnim.setValue(1);
      pulseOpacity.setValue(0);
    }
  }, [isRecording, listening]);

  // ── AI response via Gemini ───────────────────────────────────────────────────
  const processWithAI = async (userText: string) => {
    if (!geminiKey || !userText.trim()) return;

    const thinkingId = `thinking-${Date.now()}`;
    const thinkingMsg: Message = {
      id: thinkingId,
      from: 'kira',
      text: 'Thinking...',
      ts: tsNow(),
      isThinking: true,
    };
    setMessages(s => [thinkingMsg, ...s]);
    setIsThinking(true);

    try {
      const response = await chatWithGemini(
        userText,
        geminiHistory,
        geminiKey,
        tavilyKey,
        (toolName) => {
          const label = TOOL_LABELS[toolName] ?? `⚙️ Running ${toolName}...`;
          setMessages(s =>
            s.map(m => (m.id === thinkingId ? { ...m, text: label } : m))
          );
        }
      );

      const responseMsg: Message = {
        id: `kira-${Date.now()}`,
        from: 'kira',
        text: response,
        ts: tsNow(),
      };
      replaceMessage(thinkingId, responseMsg);

      Speech.speak(response, { rate: 0.95 });

      setGeminiHistory(prev => [
        ...prev,
        { role: 'user', parts: [{ text: userText }] },
        { role: 'model', parts: [{ text: response }] },
      ]);
    } catch (err) {
      const errMsg: Message = {
        id: `err-${Date.now()}`,
        from: 'kira',
        text: `AI error: ${String(err)}`,
        ts: tsNow(),
      };
      replaceMessage(thinkingId, errMsg);
    } finally {
      setIsThinking(false);
    }
  };

  // ─── Audio recording (Whisper path) ─────────────────────────────────────────

  const startRecording = async () => {
    try {
      const { granted } = await Audio.requestPermissionsAsync();
      if (!granted) {
        addMessage({ id: Date.now().toString(), from: 'kira', text: 'Microphone permission denied.', ts: tsNow() });
        return;
      }
      await Audio.setAudioModeAsync({ allowsRecordingIOS: true, playsInSilentModeIOS: true });
      const RECORDING_OPTIONS: any = {
        android: { extension: '.m4a', sampleRate: 44100, numberOfChannels: 2, bitRate: 128000 },
        ios: { extension: '.caf', sampleRate: 44100, numberOfChannels: 2, bitRate: 128000 },
        web: { mimeType: 'audio/webm' },
      };
      const recording = new Audio.Recording();
      await recording.prepareToRecordAsync(RECORDING_OPTIONS);
      await recording.startAsync();

      recordingRef.current = recording;
      setIsRecording(true);
      addMessage({ id: Date.now().toString(), from: 'kira', text: '🎙️ Recording...', ts: tsNow() });
    } catch (err) {
      console.error(err);
      addMessage({ id: Date.now().toString(), from: 'kira', text: 'Failed to start recording.', ts: tsNow() });
    }
  };

  const stopRecording = async () => {
    try {
      setIsRecording(false);
      const recording = recordingRef.current;
      if (!recording) return;
      await recording.stopAndUnloadAsync();
      const uri = recording.getURI();
      recordingRef.current = null;
      setLastRecordingUri(uri ?? null);

      if (!uri) {
        addMessage({ id: Date.now().toString(), from: 'kira', text: 'No recording file found.', ts: tsNow() });
        return;
      }

      if (openAiKey) {
        addMessage({ id: `kira-${Date.now()}`, from: 'kira', text: '⏳ Transcribing voice...', ts: tsNow() });
        try {
          const transcript = await transcribeWithWhisper(uri, openAiKey);
          const userText = transcript ?? '';
          if (userText.trim()) {
            addMessage({ id: `user-${Date.now()}`, from: 'user', text: userText, ts: tsNow() });
            if (geminiKey) {
              await processWithAI(userText);
            } else {
              Speech.speak(userText);
            }
          } else {
            addMessage({ id: `kira-${Date.now()}`, from: 'kira', text: 'No speech detected.', ts: tsNow() });
          }
        } catch (err) {
          console.error(err);
          addMessage({ id: `err-${Date.now()}`, from: 'kira', text: 'Whisper transcription failed.', ts: tsNow() });
        }
      }
    } catch (err) {
      console.error(err);
      addMessage({ id: Date.now().toString(), from: 'kira', text: 'Failed to stop recording.', ts: tsNow() });
    }
  };

  // ─── Web Speech API ──────────────────────────────────────────────────────────

  const startWebRecognition = () => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      addMessage({ id: `err-${Date.now()}`, from: 'kira', text: 'Speech recognition not supported in this browser.', ts: tsNow() });
      return;
    }
    if (webRecognizerRef.current) return;

    const recog = new SpeechRecognition();
    recog.lang = 'en-US';
    recog.interimResults = false;
    recog.maxAlternatives = 1;

    recog.onresult = (ev: any) => {
      const last = ev.results[ev.results.length - 1];
      const text = last[0].transcript;
      if (text.trim()) {
        addMessage({ id: `user-${Date.now()}`, from: 'user', text, ts: tsNow() });
        if (geminiKey) {
          processWithAI(text);
        }
      }
    };

    recog.onerror = (e: any) => {
      console.error('Speech recognition error', e);
      if (e.error === 'no-speech') {
        addMessage({ id: `err-${Date.now()}`, from: 'kira', text: 'No speech detected. Please try again.', ts: tsNow() });
      } else {
        addMessage({ id: `err-${Date.now()}`, from: 'kira', text: `Mic error: ${e.error}`, ts: tsNow() });
      }
      stopWebRecognition();
    };

    recog.onend = () => {
      webRecognizerRef.current = null;
      setListening(false);
    };

    webRecognizerRef.current = recog;
    setListening(true);
    addMessage({ id: `kira-${Date.now()}`, from: 'kira', text: '👂 Listening (say something)...', ts: tsNow() });
    recog.start();
  };

  const stopWebRecognition = () => {
    const recog = webRecognizerRef.current;
    if (recog) {
      try { recog.stop(); } catch (e) { console.warn(e); }
      webRecognizerRef.current = null;
      setListening(false);
    }
  };

  // ─── Native on-device STT ────────────────────────────────────────────────────

  const startNativeVoice = async () => {
    if (!VoiceModule || typeof VoiceModule.start !== 'function') {
      throw new Error('Native voice module not configured.');
    }
    const Voice = VoiceModule;

    Voice.onSpeechResults = (e: any) => {
      const text = (e.value && e.value[0]) || '';
      if (text.trim()) {
        addMessage({ id: `user-${Date.now()}`, from: 'user', text, ts: tsNow() });
        if (geminiKey) processWithAI(text);
      }
    };

    Voice.onSpeechError = (e: any) => {
      console.error('Voice error', e);
      addMessage({ id: `err-${Date.now()}`, from: 'kira', text: 'Device speech recognition error.', ts: tsNow() });
      setListening(false);
    };

    Voice.onSpeechEnd = () => {
      setListening(false);
    };

    try {
      setListening(true);
      addMessage({ id: `kira-${Date.now()}`, from: 'kira', text: '👂 Listening...', ts: tsNow() });
      await Voice.start('en-US');
    } catch (err) {
      setListening(false);
      throw err;
    }
  };

  const stopNativeVoice = async () => {
    if (!VoiceModule || typeof VoiceModule.stop !== 'function') return;
    const Voice = VoiceModule;
    try { await Voice.stop(); } catch {}
    try { await Voice.destroy(); } catch {}
    setListening(false);
  };

  useEffect(() => {
    return () => {
      stopWebRecognition();
      stopNativeVoice();
    };
  }, []);

  const downloadLastRecording = async () => {
    if (!lastRecordingUri) {
      addMessage({ id: `err-${Date.now()}`, from: 'kira', text: 'No recording file available.', ts: tsNow() });
      return;
    }

    if (Platform.OS === 'web') {
      try {
        const res = await fetch(lastRecordingUri);
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'recording.webm';
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
        addMessage({ id: `kira-${Date.now()}`, from: 'kira', text: 'Recording downloaded successfully.', ts: tsNow() });
      } catch (err) {
        addMessage({ id: `err-${Date.now()}`, from: 'kira', text: 'Download failed.', ts: tsNow() });
      }
    } else {
      try {
        await FileSystem.getInfoAsync(lastRecordingUri);
        addMessage({ id: `kira-${Date.now()}`, from: 'kira', text: `File saved: ${lastRecordingUri}`, ts: tsNow() });
      } catch {
        addMessage({ id: `err-${Date.now()}`, from: 'kira', text: 'Could not access file.', ts: tsNow() });
      }
    }
  };

  const clearChat = () => {
    setMessages([]);
    setGeminiHistory([]);
    setIsThinking(false);
  };

  const renderMessage = ({ item }: { item: Message }) => {
    const isUser = item.from === 'user';
    const bubbleStyle = isUser
      ? [styles.userBubble, { backgroundColor: theme.colors.primary }]
      : item.isThinking
      ? [styles.kiraBubble, { backgroundColor: theme.colors.surfaceVariant, borderWidth: 1, borderColor: theme.colors.outline }]
      : [styles.kiraBubble, { backgroundColor: theme.colors.surface }];
    const textColor = isUser ? theme.colors.onPrimary : theme.colors.onSurface;
    const timeColor = isUser ? 'rgba(255,255,255,0.7)' : theme.colors.onSurfaceVariant;
    const alignStyle = isUser ? styles.alignRight : styles.alignLeft;
    const time = item.ts
      ? new Date(item.ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      : '';

    return (
      <View style={[styles.messageRow, alignStyle]}>
        {!isUser && (
          <Avatar.Text
            size={32}
            label="K"
            style={{ marginRight: 8, backgroundColor: theme.colors.secondary }}
            labelStyle={{ color: 'white', fontWeight: 'bold' }}
          />
        )}
        <View style={[bubbleStyle, styles.shadow]}>
          {item.isThinking ? (
            <ThinkingDots color={theme.colors.onSurfaceVariant} label={item.text} />
          ) : (
            <Paragraph style={{ color: textColor, fontSize: 15, lineHeight: 22 }}>
              {item.text}
            </Paragraph>
          )}
          <Text style={[styles.timestamp, { color: timeColor }]}>{time}</Text>
        </View>
        {isUser && (
          <Avatar.Text
            size={32}
            label="U"
            style={{ marginLeft: 8, backgroundColor: theme.colors.surfaceVariant }}
            labelStyle={{ color: theme.colors.onSurfaceVariant }}
          />
        )}
      </View>
    );
  };

  const handleMicPress = async () => {
    if (openAiKey) {
      if (isRecording) {
        await stopRecording();
      } else {
        await startRecording();
      }
      return;
    }

    if (Platform.OS === 'web') {
      if (listening) stopWebRecognition(); else startWebRecognition();
    } else {
      if (listening) {
        await stopNativeVoice();
      } else {
        try {
          await startNativeVoice();
        } catch (err) {
          addMessage({ id: `err-${Date.now()}`, from: 'kira', text: 'No Whisper API key entered and native mic failed.', ts: tsNow() });
        }
      }
    }
  };

  const micIcon = listening ? 'ear-hearing' : isRecording ? 'stop-circle' : 'microphone';
  const micColor = isRecording
    ? theme.colors.error
    : listening
    ? '#F59E0B'
    : theme.colors.primary;

  return (
    <View style={styles.container}>
      {!geminiKey && (
        <Banner
          visible
          icon="information"
          style={{ backgroundColor: '#EEF2FF' }}
          actions={[]}
        >
          To enable AI responses, enter your Gemini API key in settings (⚙️).
        </Banner>
      )}

      {messages.length === 0 ? (
        <View style={styles.emptyState}>
          <View style={[styles.emptyIconRing, { borderColor: theme.colors.primary + '33' }]}>
            <Avatar.Icon
              size={72}
              icon="microphone"
              style={{ backgroundColor: theme.colors.primary + '18' }}
              color={theme.colors.primary}
            />
          </View>
          <Text style={{ marginTop: 18, fontSize: 20, fontWeight: '700', color: theme.colors.onSurface }}>
            How can I help you?
          </Text>
          <Text style={{ marginTop: 8, color: theme.colors.onSurfaceVariant, textAlign: 'center', lineHeight: 20 }}>
            Tap the mic to search the web, find online courses, compare platforms, or get ticket details!
          </Text>
          {geminiKey && (
            <Text style={{ marginTop: 10, color: theme.colors.secondary, fontWeight: '600', fontSize: 13 }}>
              ✨ Powered by Gemini 1.5 Flash
            </Text>
          )}
        </View>
      ) : (
        <FlatList
          data={messages}
          keyExtractor={item => item.id}
          inverted
          renderItem={renderMessage}
          contentContainerStyle={{ paddingVertical: 16, paddingHorizontal: 12 }}
        />
      )}

      <View style={[styles.controlsContainer, { backgroundColor: theme.colors.surface }]}>
        <View style={styles.controls}>
          <IconButton
            icon={Platform.OS === 'web' ? 'download' : 'folder'}
            size={22}
            onPress={downloadLastRecording}
            iconColor={theme.colors.onSurfaceVariant}
          />

          <View style={styles.micWrapper}>
            <Animated.View
              style={[
                styles.pulseRing,
                {
                  transform: [{ scale: pulseAnim }],
                  opacity: pulseOpacity,
                  backgroundColor: micColor,
                },
              ]}
            />
            <IconButton
              icon={micIcon}
              size={34}
              mode="contained"
              containerColor={micColor}
              iconColor={theme.colors.onPrimary}
              onPress={handleMicPress}
              disabled={isThinking}
              style={styles.mainButton}
            />
          </View>

          {messages.length > 0 ? (
            <IconButton
              icon="trash-can-outline"
              size={22}
              onPress={clearChat}
              iconColor={theme.colors.onSurfaceVariant}
            />
          ) : (
            <Button
              mode="text"
              compact
              onPress={() => {
                const reply = 'Hi, I am KIRA â€” your agentic AI voice assistant. Ask me anything!';
                addMessage({ id: `kira-${Date.now()}`, from: 'kira', text: reply, ts: tsNow() });
                Speech.speak(reply);
              }}
              textColor={theme.colors.primary}
            >
              Intro
            </Button>
          )}
        </View>

        {/* Status text */}
        <Text style={[styles.statusText, { color: theme.colors.onSurfaceVariant }]}>
          {isThinking
            ? 'KIRA is thinkingâ€¦'
            : isRecording
            ? 'Recording â€” tap to stop'
            : listening
            ? 'Listening â€” speak now'
            : 'Tap mic to speak'}
        </Text>
      </View>
    </View>
  );
}

// â”€â”€â”€ Thinking dots sub-component â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function ThinkingDots({ color, label }: { color: string; label: string }) {
  const dot1 = useRef(new Animated.Value(0.3)).current;
  const dot2 = useRef(new Animated.Value(0.3)).current;
  const dot3 = useRef(new Animated.Value(0.3)).current;

  useEffect(() => {
    const seq = (dot: Animated.Value, delay: number) =>
      Animated.loop(
        Animated.sequence([
          Animated.delay(delay),
          Animated.timing(dot, { toValue: 1, duration: 350, useNativeDriver: true }),
          Animated.timing(dot, { toValue: 0.3, duration: 350, useNativeDriver: true }),
        ])
      );
    const a1 = seq(dot1, 0);
    const a2 = seq(dot2, 180);
    const a3 = seq(dot3, 360);
    a1.start(); a2.start(); a3.start();
    return () => { a1.stop(); a2.stop(); a3.stop(); };
  }, []);

  return (
    <View>
      <Text style={{ color, fontSize: 13, marginBottom: 4 }}>{label}</Text>
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
        {[dot1, dot2, dot3].map((d, i) => (
          <Animated.View
            key={i}
            style={{
              width: 7, height: 7, borderRadius: 3.5,
              backgroundColor: color,
              opacity: d,
            }}
          />
        ))}
      </View>
    </View>
  );
}

// â”€â”€â”€ Styles â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

const styles = StyleSheet.create({
  container: { flex: 1 },

  // Empty state
  emptyState: {
    flex: 1, justifyContent: 'center', alignItems: 'center',
    padding: 32,
  },
  emptyIconRing: {
    width: 100, height: 100, borderRadius: 50,
    borderWidth: 2, alignItems: 'center', justifyContent: 'center',
  },

  // Message rows
  messageRow: { flexDirection: 'row', alignItems: 'flex-end', marginVertical: 6 },
  alignLeft: { justifyContent: 'flex-start' },
  alignRight: { justifyContent: 'flex-end' },
  kiraBubble: {
    maxWidth: '75%', padding: 14,
    borderTopLeftRadius: 4, borderTopRightRadius: 20,
    borderBottomLeftRadius: 20, borderBottomRightRadius: 20,
  },
  userBubble: {
    maxWidth: '75%', padding: 14,
    borderTopLeftRadius: 20, borderTopRightRadius: 20,
    borderBottomLeftRadius: 20, borderBottomRightRadius: 4,
  },
  shadow: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.08,
    shadowRadius: 3,
    elevation: 2,
  },
  timestamp: { fontSize: 10, alignSelf: 'flex-end', marginTop: 4 },

  // Controls
  controlsContainer: {
    paddingHorizontal: 16, paddingTop: 12, paddingBottom: 16,
    borderTopWidth: 1, borderTopColor: 'rgba(0,0,0,0.06)',
  },
  controls: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
  },
  micWrapper: { position: 'relative', alignItems: 'center', justifyContent: 'center' },
  pulseRing: {
    position: 'absolute',
    width: 72, height: 72, borderRadius: 36,
  },
  mainButton: { width: 68, height: 68, borderRadius: 34, margin: 0 },
  statusText: {
    fontSize: 11, textAlign: 'center', marginTop: 6,
    letterSpacing: 0.3,
  },
});

