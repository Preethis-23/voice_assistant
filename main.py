
import datetime
import difflib
import json
import os
import re
import smtplib
import subprocess
import time
import threading
import webbrowser as wb
from email.message import EmailMessage
from getpass import getpass

import pyautogui
import pyttsx3
import pywhatkit
import speech_recognition as sr
from num2words import num2words

class VoiceAssistant:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.recognizer = sr.Recognizer()
        self.workspace_root = os.path.dirname(os.path.abspath(__file__))
        self.contacts_path = os.path.join(self.workspace_root, "contacts.json")
        self.email_profiles_path = os.path.join(self.workspace_root, "email_profiles.json")
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
        self.contacts = self._load_contacts()
        self.email_profiles = self._load_email_profiles()
        self.configure_engine()
        self.greet_user()

    def _load_json_file(self, path, default):
        if not os.path.exists(path):
            return default
        try:
            with open(path, "r", encoding="utf-8") as file:
                return json.load(file)
        except (json.JSONDecodeError, OSError):
            return default

    def _load_contacts(self):
        raw_contacts = self._load_json_file(self.contacts_path, [])
        if isinstance(raw_contacts, dict):
            raw_contacts = [{"name": name, "phone": phone} for name, phone in raw_contacts.items()]

        contacts = []
        if not isinstance(raw_contacts, list):
            return contacts

        for item in raw_contacts:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", "")).strip()
            if not name:
                continue
            aliases = item.get("aliases", [])
            if isinstance(aliases, str):
                aliases = [aliases]
            contacts.append({
                "name": name,
                "phone": str(item.get("phone", item.get("number", ""))).strip(),
                "email": str(item.get("email", "")).strip(),
                "aliases": [str(alias).strip() for alias in aliases if str(alias).strip()],
            })
        return contacts

    def _load_email_profiles(self):
        raw_profiles = self._load_json_file(self.email_profiles_path, [])
        if isinstance(raw_profiles, dict):
            raw_profiles = [raw_profiles]

        profiles = []
        if not isinstance(raw_profiles, list):
            return profiles

        for item in raw_profiles:
            if not isinstance(item, dict):
                continue
            email_address = str(item.get("email", "")).strip()
            if not email_address:
                continue
            profiles.append({
                "label": str(item.get("label", item.get("name", email_address))).strip() or email_address,
                "email": email_address,
                "smtp_server": str(item.get("smtp_server", "smtp.gmail.com")).strip(),
                "smtp_port": int(item.get("smtp_port", 587)),
                "use_tls": bool(item.get("use_tls", True)),
                "smtp_username": str(item.get("smtp_username", email_address)).strip() or email_address,
                "password_env": str(item.get("password_env", "")).strip(),
            })
        return profiles

    def _listen_text(self, prompt, phrase_time_limit=8):
        if prompt:
            self.speak(prompt)
            print(prompt)

        with sr.Microphone() as source:
            self.recognizer.pause_threshold = 0.8
            try:
                audio = self.recognizer.listen(source, phrase_time_limit=phrase_time_limit)
                text = self.recognizer.recognize_google(audio)
                print(text)
                return text.strip()
            except sr.UnknownValueError:
                return ""
            except sr.RequestError:
                self.speak("There was an issue with the speech service.")
                return ""
            except AttributeError as e:
                print("Microphone not initialized properly:", e)
                self.speak("Microphone not initialized properly.")
                return ""

    def _normalise_text(self, text):
        return " ".join(str(text).lower().split())

    def _contact_score(self, contact, query):
        query_text = self._normalise_text(query)
        candidate_texts = [contact.get("name", ""), contact.get("phone", ""), contact.get("email", "")]
        candidate_texts.extend(contact.get("aliases", []))
        best_score = 0.0

        for candidate in candidate_texts:
            candidate_text = self._normalise_text(candidate)
            if not candidate_text:
                continue
            score = difflib.SequenceMatcher(None, query_text, candidate_text).ratio()
            if query_text in candidate_text or candidate_text in query_text:
                score = max(score, 0.95)
            best_score = max(best_score, score)

        return best_score

    def _resolve_contact(self, query, required_field=None):
        if not self.contacts:
            return None

        matches = []
        for contact in self.contacts:
            score = self._contact_score(contact, query)
            if score >= 0.45:
                matches.append((score, contact))

        if not matches:
            return None

        matches.sort(key=lambda item: item[0], reverse=True)
        top_score = matches[0][0]
        tied_matches = [contact for score, contact in matches if top_score - score <= 0.08]

        if len(tied_matches) > 1:
            names = ", ".join(contact["name"] for contact in tied_matches[:4])
            self.speak(f"I found similar contacts: {names}. Please say the exact name.")
            retry = self._listen_text("Say the exact contact name.", phrase_time_limit=6)
            if retry:
                return self._resolve_contact(retry, required_field=required_field)

        contact = matches[0][1]
        if required_field and not contact.get(required_field):
            return None
        return contact

    def _resolve_email_profile(self, query):
        if not self.email_profiles:
            return None

        matches = []
        query_text = self._normalise_text(query)
        for profile in self.email_profiles:
            label_text = self._normalise_text(profile.get("label", ""))
            email_text = self._normalise_text(profile.get("email", ""))
            score = max(
                difflib.SequenceMatcher(None, query_text, label_text).ratio(),
                difflib.SequenceMatcher(None, query_text, email_text).ratio(),
            )
            if query_text in label_text or query_text in email_text:
                score = max(score, 0.95)
            if score >= 0.45:
                matches.append((score, profile))

        if not matches:
            return None

        matches.sort(key=lambda item: item[0], reverse=True)
        top_score = matches[0][0]
        tied_matches = [profile for score, profile in matches if top_score - score <= 0.08]

        if len(tied_matches) > 1:
            names = ", ".join(profile["label"] for profile in tied_matches[:4])
            self.speak(f"I found similar email accounts: {names}. Please say the exact one.")
            retry = self._listen_text("Say the exact email account.", phrase_time_limit=6)
            if retry:
                return self._resolve_email_profile(retry)

        return matches[0][1]

    def _generate_email_content(self, recipient_name, topic, extra_details, sender_label):
        greeting = f"Hi {recipient_name}," if recipient_name else "Hello,"
        clean_topic = topic.strip() if topic else "the topic we discussed"
        subject = clean_topic[:1].upper() + clean_topic[1:] if clean_topic else "Quick note"
        body_lines = [
            greeting,
            "",
            f"I hope you're doing well. I wanted to reach out about {clean_topic}.",
        ]
        if extra_details:
            body_lines.extend(["", extra_details.strip()])
        body_lines.extend(["", "Please let me know if you need anything else.", "", "Best regards,", sender_label or ""])
        body = "\n".join(line for line in body_lines if line is not None)
        return subject, body

    def _parse_alarm_time(self, text):
        lowered = self._normalise_text(text)
        now = datetime.datetime.now()

        minute_match = re.search(r"(?:in|after)\s+(\d+)\s+(minute|minutes|hour|hours)", lowered)
        if minute_match:
            amount = int(minute_match.group(1))
            unit = minute_match.group(2)
            if "hour" in unit:
                amount *= 60
            return now + datetime.timedelta(minutes=amount)

        time_match = re.search(r"(\d{1,2})(?::(\d{1,2}))?\s*(am|pm)?", lowered)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2) or 0)
            meridiem = time_match.group(3)

            if meridiem:
                if meridiem == "pm" and hour != 12:
                    hour += 12
                if meridiem == "am" and hour == 12:
                    hour = 0

            target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if target <= now:
                target += datetime.timedelta(days=1)
            return target

        return None

    def _trigger_alarm(self, target_time, label):
        delay = (target_time - datetime.datetime.now()).total_seconds()
        if delay < 0:
            delay = 0

        def alarm_worker():
            time.sleep(delay)
            alert_text = f"Alarm ringing{': ' + label if label else ''}"
            print(alert_text)
            self.speak(alert_text)

        threading.Thread(target=alarm_worker, daemon=True).start()

    def set_alarm(self):
        when_text = self._listen_text("When should I set the alarm? Say something like in 10 minutes or at 7 30 am.", phrase_time_limit=10)
        if not when_text:
            self.speak("I did not catch the alarm time.")
            return True

        target_time = self._parse_alarm_time(when_text)
        if not target_time:
            self.speak("I could not understand the alarm time.")
            return True

        label = self._listen_text("What should I remind you about? Say no for a simple alarm.", phrase_time_limit=8)
        if label.lower() in {"no", "nope", "nothing"}:
            label = ""

        self._trigger_alarm(target_time, label)
        pretty_time = target_time.strftime("%I:%M %p on %d %B %Y").lstrip("0").replace(" 0", " ")
        self.speak(f"Alarm set for {pretty_time}")
        return True

    def create_notepad_note(self):
        note_name = self._listen_text("What file name should I use?", phrase_time_limit=8)
        if not note_name:
            self.speak("I did not catch the file name.")
            return True

        safe_name = self._normalise_text(note_name).replace(" ", "_")
        safe_name = re.sub(r"[^a-z0-9_\-]", "", safe_name)
        if not safe_name:
            safe_name = "note"
        if not safe_name.endswith(".txt"):
            safe_name += ".txt"

        note_lines = []
        self.speak("Start speaking your notes. Say stop dictation when you are finished.")
        while True:
            line = self._listen_text("Speak the next line.", phrase_time_limit=10)
            if not line:
                continue
            if self._normalise_text(line) in {"stop dictation", "stop writing", "done", "finish", "end"}:
                break
            note_lines.append(line)

        note_text = "\n".join(note_lines).strip()
        file_path = os.path.join(self.workspace_root, safe_name)
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(note_text)

        try:
            subprocess.Popen(["notepad.exe", file_path])
        except FileNotFoundError:
            pass

        self.speak(f"Saved the note as {safe_name}")
        return True

    def _safe_type(self, text, interval=0.01):
        pyautogui.write(text, interval=interval)

    def _choose_contact_by_whatsapp_name(self, contact_name):
        candidates = []
        query = self._normalise_text(contact_name)
        for contact in self.contacts:
            names_to_match = [contact.get("name", "")] + contact.get("aliases", [])
            score = 0.0
            for candidate_name in names_to_match:
                candidate_text = self._normalise_text(candidate_name)
                if not candidate_text:
                    continue
                current_score = difflib.SequenceMatcher(None, query, candidate_text).ratio()
                if query in candidate_text or candidate_text in query:
                    current_score = max(current_score, 0.95)
                score = max(score, current_score)
            if score >= 0.45:
                candidates.append((score, contact.get("name", "")))

        if not candidates:
            return contact_name

        candidates.sort(key=lambda item: item[0], reverse=True)
        top_score = candidates[0][0]
        similar_names = [name for score, name in candidates if top_score - score <= 0.08]

        if len(similar_names) > 1:
            self.speak(f"I found similar saved names: {', '.join(similar_names[:4])}. Say the exact one.")
            retry = self._listen_text("Say the exact contact name.", phrase_time_limit=6)
            if retry:
                return retry

        return candidates[0][1]

    def send_whatsapp_message(self):
        recipient_name = self._listen_text("Who should I send the WhatsApp message to?", phrase_time_limit=8)
        if not recipient_name:
            self.speak("I did not catch the contact name.")
            return True

        chosen_name = self._choose_contact_by_whatsapp_name(recipient_name)
        message = self._listen_text(f"What message should I send to {chosen_name}?", phrase_time_limit=12)
        if not message:
            self.speak("I did not catch the message.")
            return True

        self.speak(f"Opening WhatsApp and searching for {chosen_name}")
        try:
            wb.open("https://web.whatsapp.com")
            time.sleep(8)
            pyautogui.hotkey("ctrl", "l")
            self._safe_type("https://web.whatsapp.com")
            pyautogui.press("enter")
            time.sleep(5)
            pyautogui.hotkey("ctrl", "f")
            self._safe_type(chosen_name)
            time.sleep(1)
            pyautogui.press("esc")
            pyautogui.press("tab")
            pyautogui.press("enter")
            time.sleep(2)
            self._safe_type(message)
            pyautogui.press("enter")
            self.speak("The WhatsApp message was sent.")
        except Exception as exc:
            print(f"WhatsApp send failed: {exc}")
            self.speak("I could not send the WhatsApp message.")
        return True

    def send_email_message(self):
        if not self.email_profiles:
            self.speak("I could not find any email profiles. Add them in email_profiles.json first.")
            return True

        sender_query = self._listen_text("Which email account should I use?", phrase_time_limit=8)
        sender_profile = self._resolve_email_profile(sender_query) if sender_query else None
        if not sender_profile and len(self.email_profiles) == 1:
            sender_profile = self.email_profiles[0]

        if not sender_profile:
            self.speak("I could not identify that email account.")
            return True

        recipient_query = self._listen_text("Who should I send the email to?", phrase_time_limit=8)
        if not recipient_query:
            self.speak("I did not catch the recipient.")
            return True

        recipient_email = ""
        recipient_name = ""
        if "@" in recipient_query:
            recipient_email = recipient_query.replace(" ", "").strip()
        else:
            recipient_contact = self._resolve_contact(recipient_query, required_field="email")
            if recipient_contact and recipient_contact.get("email"):
                recipient_email = recipient_contact["email"]
                recipient_name = recipient_contact.get("name", "")

        if not recipient_email:
            self.speak("I could not find an email address for that recipient.")
            return True

        topic = self._listen_text("About what should I write the email?", phrase_time_limit=12)
        if not topic:
            self.speak("I did not catch the topic.")
            return True

        extra_details = self._listen_text("Any extra details to include? Say no if you want a short email.", phrase_time_limit=12)
        if extra_details.lower() in {"no", "nope", "nothing", "skip"}:
            extra_details = ""

        subject, body = self._generate_email_content(recipient_name, topic, extra_details, sender_profile["email"])
        print("Generated email subject:")
        print(subject)
        print("Generated email body:")
        print(body)

        password_env = sender_profile.get("password_env")
        password = os.environ.get(password_env, "") if password_env else ""
        if not password:
            self.speak("Enter the email app password in the terminal.")
            password = getpass(f"App password for {sender_profile['email']}: ")

        email_message = EmailMessage()
        email_message["From"] = sender_profile["email"]
        email_message["To"] = recipient_email
        email_message["Subject"] = subject
        email_message.set_content(body)

        try:
            with smtplib.SMTP(sender_profile["smtp_server"], sender_profile["smtp_port"]) as server:
                if sender_profile.get("use_tls", True):
                    server.starttls()
                server.login(sender_profile.get("smtp_username", sender_profile["email"]), password)
                server.send_message(email_message)
            self.speak("The email was sent.")
        except Exception as exc:
            print(f"Email send failed: {exc}")
            self.speak("I could not send the email.")
        return True

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
            "send whatsapp message to a saved contact",
            "send email from a saved account",
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

        if "alarm" in lowered:
            return self.set_alarm()

        if "notepad" in lowered and any(word in lowered for word in ("write", "note", "notes", "dictate", "save")):
            return self.create_notepad_note()

        if any(phrase in lowered for phrase in ("send whatsapp", "whatsapp message", "message on whatsapp")):
            return self.send_whatsapp_message()

        if any(phrase in lowered for phrase in ("send email", "send mail", "gmail message", "mail someone")):
            return self.send_email_message()

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
