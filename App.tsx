import React, { useState } from 'react';
import { MD3LightTheme as DefaultTheme, Provider as PaperProvider, configureFonts } from 'react-native-paper';
import HomeScreen from './src/screens/HomeScreen';

const fontConfig = {
  fontFamily: 'System',
};

const theme = {
  ...DefaultTheme,
  colors: {
    ...DefaultTheme.colors,
    primary: '#4F46E5', // Indigo 600 - Professional & Modern
    onPrimary: '#FFFFFF',
    secondary: '#10B981', // Emerald 500 - Soft success/action
    onSecondary: '#FFFFFF',
    background: '#F3F4F6', // Cool Gray 100 - Mild to the eye
    surface: '#FFFFFF',
    onSurface: '#1F2937', // Gray 800 - Soft black
    surfaceVariant: '#E5E7EB', // Gray 200
    onSurfaceVariant: '#374151', // Gray 700
    outline: '#9CA3AF',
    elevation: {
      level1: '#FFFFFF',
      level2: '#F9FAFB',
      level3: '#F3F4F6',
      level4: '#E5E7EB',
      level5: '#D1D5DB',
    }
  },
  roundness: 16,
  fonts: configureFonts({ config: fontConfig }),
};

export default function App() {
  const [openAiKey, setOpenAiKey] = useState<string | null>(
    process.env.EXPO_PUBLIC_OPENAI_API_KEY || null
  );
  const [geminiKey, setGeminiKey] = useState<string | null>(
    process.env.EXPO_PUBLIC_GEMINI_API_KEY || null
  );
  const [tavilyKey, setTavilyKey] = useState<string | null>(
    process.env.EXPO_PUBLIC_TAVILY_API_KEY || null
  );

  return (
    <PaperProvider theme={theme}>
      <HomeScreen
        openAiKey={openAiKey}
        setOpenAiKey={setOpenAiKey}
        geminiKey={geminiKey}
        setGeminiKey={setGeminiKey}
        tavilyKey={tavilyKey}
        setTavilyKey={setTavilyKey}
      />
    </PaperProvider>
  );
}

