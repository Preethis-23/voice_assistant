
import datetime
import os
import subprocess
import webbrowser as wb

import pyttsx3
import pywhatkit
import speech_recognition as sr
from num2words import num2words

class VoiceAssistant:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.recognizer = sr.Recognizer()
        self.workspace_root = os.path.dirname(os.path.abspath(__file__))
        self.app_paths = {
            'calculator': "calc.exe",
            'explorer': "explorer.exe",
            'browser': r"C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
            'edge': r"C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
            'chrome': r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
            'code': "code",
            'vscode': "code",
            'notepad': "notepad.exe"
        }
        self.website_shortcuts = {
            'gmail': "https://mail.google.com",
            'whatsapp': "https://web.whatsapp.com",
            'stackoverflow': "https://stackoverflow.com",
            'github': "https://github.com",
            'linkedin': "https://www.linkedin.com",
            'news': "https://news.google.com",
            'google': "https://www.google.com",
            'youtube': "https://www.youtube.com"
        }
        self.configure_engine()
        self.greet_user()

    def configure_engine(self):
        self.engine.setProperty('rate', 150)
        self.engine.setProperty('volume', 1.0)
        voices = self.engine.getProperty('voices')
        target_voice = voices[1] if len(voices) > 1 else voices[0]
        self.engine.setProperty('voice', target_voice.id)

    def greet_user(self):
        self.speak("Hello KIRA, How can I help you?")
        print("Hello KIRA, How can I help you?")

    def speak(self, text):
        self.engine.say(text)
        self.engine.runAndWait()

    def _recognize_audio(self, source, phrase_time_limit=6):
        audio = self.recognizer.listen(source, phrase_time_limit=phrase_time_limit)
        return self.recognizer.recognize_google(audio)

    def open_youtube(self):
        wb.open("https://www.youtube.com")
        self.speak("Opening YouTube")

    def play_song(self, song_name):
        song_name = song_name.replace("play", "").strip()
        if not song_name:
            self.speak("Tell me the song name to play.")
            return
        self.speak(f"Playing {song_name}")
        try:
            pywhatkit.playonyt(song_name)
        except Exception:
            self.speak("I couldn't start YouTube. Check your internet connection.")

    def open_app(self, app_name):
        app_name = app_name.replace("open", "").lower().strip()
        for key, path in self.app_paths.items():
            if key in app_name:
                self.speak(f"Opening {key}")
                try:
                    if os.path.exists(path):
                        subprocess.Popen([path])
                    else:
                        subprocess.Popen([path], shell=True)
                except FileNotFoundError:
                    self.speak("I couldn't find that application on this PC.")
                return True
        return False

    def open_website(self, text):
        lowered = text.lower()
        for keyword, url in self.website_shortcuts.items():
            if keyword in lowered:
                self.speak(f"Opening {keyword}")
                if not self._open_with_edge(url, prefer_edge=True):
                    wb.open(url)
                return True
        return False

    def search_web(self, term):
        term = term.replace('search', "").strip()
        if not term:
            self.speak("Tell me what to search for.")
            return
        url = f"https://www.google.com/search?q={term}"
        if not self._open_with_edge(url):
            wb.open(url)

    def tell_time(self):
        now = datetime.datetime.now()
        c_time_display = now.strftime("%I:%M %p").lstrip('0').replace(" 0", " ")
        day = int(now.strftime("%d"))
        month = now.strftime("%B")
        year = now.strftime("%Y")
        suffix = "th" if 11 <= day <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
        c_date_speech = f"{num2words(day)}{suffix} {month} {num2words(int(year))}"
        weekday = now.strftime("%A")
        voice = f"Today is {weekday}, {c_date_speech}, and the time is {c_time_display}"
        print(voice)
        self.speak(voice)

    def describe_commands(self):
        supported = [
            "say hey bluffy to wake",
            "say time or date",
            "search for <topic>",
            "play <song> on youtube",
            "open calculator, explorer, notepad, edge, chrome",
            "open gmail, whatsapp web (edge), stackoverflow, github, news",
            "open project or s1 in vs code",
            "say stop or exit to quit"
        ]
        help_text = "; ".join(supported)
        print("Commands:")
        for item in supported:
            print(f"- {item}")
        self.speak(f"You can say: {help_text}")

    def _open_with_edge(self, url, prefer_edge=False):
        edge_path = self.app_paths.get('edge')
        if edge_path and os.path.exists(edge_path):
            subprocess.Popen([edge_path, url])
            return True
        if prefer_edge:
            return False
        wb.open(url)
        return True

    def open_in_vscode(self, text):
        lowered = text.lower()
        keywords = [
            "in vscode",
            "in vs code",
            "with vscode",
            "with vs code",
            "in code",
            "code editor",
            "file name",
        ]
        for k in keywords:
            lowered = lowered.replace(k, "")
        lowered = lowered.replace("open", "").strip()

        shortcuts = {
            "project": self.workspace_root,
            "voice assistant": self.workspace_root,
            "voice assistant project": self.workspace_root,
            "s1": os.path.join(self.workspace_root, "s1.py"),
            "s2": os.path.join(self.workspace_root, "s2.py"),
            "trail": os.path.join(self.workspace_root, "trail.py"),
        }

        target_path = shortcuts.get(lowered, None)
        if not target_path:
            candidate = os.path.join(self.workspace_root, lowered)
            target_path = candidate if os.path.exists(candidate) else self.workspace_root

        self.speak("Opening in Visual Studio Code")
        try:
            subprocess.Popen(["code", target_path])
        except FileNotFoundError:
            subprocess.Popen(["code", target_path], shell=True)
        return True

    def handle_command(self, text):
        lowered = text.lower()

        if any(quit_word in lowered for quit_word in ("stop", "exit", "quit", "goodbye")):
            self.speak("Stopping now. Goodbye!")
            return False

        if any(help_word in lowered for help_word in ("help", "commands", "what can you do")):
            self.describe_commands()
            return True

        if "time" in lowered or "date" in lowered:
            self.tell_time()
            return True

        if "youtube" in lowered and "play" not in lowered:
            self.open_youtube()
            return True

        if "search" in lowered:
            self.search_web(lowered)
            return True

        if "play" in lowered:
            self.play_song(lowered)
            return True

        if "open" in lowered:
            if "code" in lowered or "vscode" in lowered or "vs code" in lowered:
                return self.open_in_vscode(lowered)
            if self.open_app(lowered):
                return True
            if self.open_website(lowered):
                return True

        self.speak("I didn't catch that. Say help to hear supported commands.")
        return True

    def listen_for_wake_word(self):
        print("Waiting for wake word: 'hey bluffy'")
        with sr.Microphone() as source:
            self.recognizer.pause_threshold = 0.8
            try:
                text = self._recognize_audio(source, phrase_time_limit=4)
                lowered = text.lower()
                print(f"Heard: {text}")
                if "hey bluffy" in lowered or "hey fluffy" in lowered:
                    self.speak("Yes, listening.")
                    return True
            except sr.UnknownValueError:
                pass
            except sr.RequestError:
                print("Speech service error while waiting for wake word.")
        return False

    def listen_for_command(self):
        print("Listening for command...")
        with sr.Microphone() as source:
            self.recognizer.pause_threshold = 0.8
            try:
                text = self._recognize_audio(source, phrase_time_limit=10)
                print(f"Command: {text}")
                self.speak(text)
                return self.handle_command(text)
            except sr.UnknownValueError:
                print("Sorry, I couldn't understand the audio.")
                self.speak("Sorry, I couldn't understand the audio.")
            except sr.RequestError:
                print("There was an issue with the Google Speech Recognition service.")
                self.speak("There was an issue with the Google Speech Recognition service.")
            except AttributeError as e:
                print("Microphone not initialized properly:", e)
                self.speak("Microphone not initialized properly.")
        return True

    def run(self):
        keep_running = True
        while keep_running:
            if not self.listen_for_wake_word():
                continue
            keep_running = self.listen_for_command()

if __name__ == "__main__":
    assistant = VoiceAssistant()
    assistant.run()
