import React, { useState } from 'react';
import { View, StyleSheet, ScrollView, Animated } from 'react-native';
import AssistantUI from '../components/AssistantUI';
import { Appbar, TextInput, Text, Chip, useTheme, Surface } from 'react-native-paper';

type Props = {
  openAiKey: string | null;
  setOpenAiKey: (k: string | null) => void;
  geminiKey: string | null;
  setGeminiKey: (k: string | null) => void;
  tavilyKey: string | null;
  setTavilyKey: (k: string | null) => void;
};

export default function HomeScreen({
  openAiKey, setOpenAiKey,
  geminiKey, setGeminiKey,
  tavilyKey, setTavilyKey,
}: Props) {
  const theme = useTheme();
  const [showSettings, setShowSettings] = useState(false);

  return (
    <View style={styles.container}>
      {/* ── Header ─────────────────────────────────────── */}
      <Appbar.Header style={{ backgroundColor: theme.colors.primary }}>
        <Appbar.Content
          title="KIRA"
          titleStyle={{ color: '#fff', fontWeight: '700', fontSize: 20 }}
          subtitle="Agentic AI Voice Assistant"
          subtitleStyle={{ color: 'rgba(255,255,255,0.75)', fontSize: 12 }}
        />
        {/* Status chips */}
        <Chip
          compact
          style={{ marginRight: 4, backgroundColor: geminiKey ? '#10B981' : '#6B7280' }}
          textStyle={{ color: '#fff', fontSize: 10 }}
        >
          {geminiKey ? 'AI ✓' : 'AI off'}
        </Chip>
        <Appbar.Action
          icon={showSettings ? 'close' : 'cog'}
          iconColor="#fff"
          onPress={() => setShowSettings(s => !s)}
        />
      </Appbar.Header>

      {/* ── Settings panel ─────────────────────────────── */}
      {showSettings && (
        <Surface style={[styles.settingsPanel, { backgroundColor: theme.colors.surface }]} elevation={2}>
          <Text variant="labelLarge" style={{ marginBottom: 8, color: theme.colors.onSurfaceVariant }}>
            🔑 API Keys
          </Text>
          <TextInput
            label="Gemini API Key — required for AI"
            value={geminiKey ?? ''}
            onChangeText={t => setGeminiKey(t || null)}
            secureTextEntry
            mode="outlined"
            style={styles.keyInput}
            left={<TextInput.Icon icon="brain" />}
            dense
          />
          <TextInput
            label="OpenAI API Key — optional, for Whisper STT"
            value={openAiKey ?? ''}
            onChangeText={t => setOpenAiKey(t || null)}
            secureTextEntry
            mode="outlined"
            style={styles.keyInput}
            left={<TextInput.Icon icon="microphone" />}
            dense
          />
          <TextInput
            label="Tavily API Key — optional, for web search"
            value={tavilyKey ?? ''}
            onChangeText={t => setTavilyKey(t || null)}
            secureTextEntry
            mode="outlined"
            style={styles.keyInput}
            left={<TextInput.Icon icon="web-search" />}
            dense
          />
          <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant, marginTop: 4 }}>
            Get Gemini key free → aistudio.google.com
          </Text>
        </Surface>
      )}

      {/* ── Main content ───────────────────────────────── */}
      <View style={styles.content}>
        <AssistantUI
          openAiKey={openAiKey}
          geminiKey={geminiKey}
          tavilyKey={tavilyKey}
        />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F3F4F6' },
  settingsPanel: { padding: 16, margin: 8, borderRadius: 12 },
  keyInput: { marginBottom: 8 },
  content: { flex: 1 },
});

