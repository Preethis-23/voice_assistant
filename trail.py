'''import pyttsx3 as ps
import pywhatkit
import pyautogui as pg
import time

engine=ps.init()
pywhatkit.sendwhatmsg('+91 6383731247','Hello Ram',10,29)
time.sleep(2)
pg.press('enter')
engine.runAndWait()


import pyttsx3

inp = pyttsx3.init()
voices = inp.getProperty('voices')  # Retrieve available voices

for index, voice in enumerate(voices):
    print(f"Voice {index}:")
    print(f" - ID: {voice.id}")
    print(f" - Name: {voice.name}")
    print(f" - Languages: {voice.languages}")
    print(f" - Gender: {voice.gender}")
    print(f" - Age: {voice.age}")

import pyttsx3

inp = pyttsx3.init()
inp.setProperty('rate', 150)  # Set speech rate
inp.setProperty('volume', 1.0)  # Set volume to maximum

voices = inp.getProperty('voices')  # Retrieve available voices

# Set the desired voice (e.g., voices[1] for the second available voice)
inp.setProperty('voice', voices[1].id)

inp.say("Hello Muthu, I am fine")
inp.runAndWait()

import speech_recognition as sr
import pyttsx3
import whisper
import tempfile

inp = pyttsx3.init()
recog = sr.Recognizer()
inp.setProperty('rate', 150)  # Set speech rate & can be max of 200 (measured in wpm)
inp.setProperty('volume', 1.0)  # Set volume to maximum

voices = inp.getProperty('voices')
inp.setProperty('voice', voices[1].id)
inp.say("Hello Muthu, How can I help you?")
inp.runAndWait()

# Load Whisper model (can choose from 'tiny', 'base', 'small', 'medium', 'large')
model = whisper.load_model("base")


def recognition():
    print("Listening....:)")
    with sr.Microphone() as source:
        recog.adjust_for_ambient_noise(source, duration=1)
        try:
            # Record the audio
            audio = recog.listen(source, phrase_time_limit=17)
            print("Audio received")

            # Save the audio to a temporary file (Whisper requires a file input)
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(audio.get_wav_data())
                temp_filename = temp_file.name

            # Use Whisper to transcribe the audio
            result = model.transcribe(temp_filename)
            text = result['text']
            print(text)

            inp.say(text)
            inp.runAndWait()
        except sr.UnknownValueError:
            print("Sorry, I couldn't understand the audio.")
            inp.say("Sorry, I couldn't understand the audio.")
            inp.runAndWait()

        except sr.RequestError:
            print("There was an issue with the microphone.")
            inp.say("There was an issue with the microphone.")
            inp.runAndWait()

        except AttributeError as e:
            print("Microphone not initialized properly:", e)
            inp.say("Microphone not initialized properly.")
            inp.runAndWait()


recognition()


import speech_recognition as sr

recognizer = sr.Recognizer()

with sr.Microphone() as source:
    print("Say something...")
    recognizer.adjust_for_ambient_noise(source, duration=1)
    audio = recognizer.listen(source)
    print("Audio captured.")

try:
    text = recognizer.recognize_google(audio)
    print("You said:", text)
except sr.UnknownValueError:
    print("Sorry, I couldn't understand the audio.")
except sr.RequestError as e:
    print("Could not request results from Google Speech Recognition service; {0}".format(e))










import speech_recognition as sr
import pyttsx3
import pywhatkit
import datetime
import wikipedia
import pyjokes


listener = sr.Recognizer()
engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)


def talk(text):
    engine.say(text)
    engine.runAndWait()


def take_command():
    try:
        with sr.Microphone() as source:
            print("How can i assist you? ")
            voice = listener.listen(source)
            command = listener.recognize_google(voice)
            command = command.lower()
            if 'aura' in command:
                command = command.replace('mia', '')
                print(command)
    except:
        pass
    return command


def run_alexa():
    command = take_command()
    print(command)
    if 'play' in command:
        song = command.replace('play', '')
        talk('playing ' + song)
        pywhatkit.playonyt(song)
    elif ' tell me the time' in command:
        time = datetime.datetime.now().strftime('%I:%M %p')
        talk('Current time is ' + time)
    elif 'who is ' in command:
        person = command.replace('who is', '')
        info = wikipedia.summary(person, 1)
        print(info)
        talk(info)
    elif 'will you date me' in command:
        talk('sorry, I have a headache')
        print('sorry, I have a headache')
    elif 'who created you' in command:
        talk('i am created by Team Aura')
        print('i am created by Team Aura')
    elif 'How can you help me' in command:
        talk('I can help you to access the things easily by voice command')
        print('I can help you to access the things easily by voice command')
    elif 'joke' in command:
        talk(pyjokes.get_joke())
    elif 'stop' in command or 'exit' in command:
        exit()
    else:
        talk('Please say the command again.')
        print("Please say the command again.")

while True:
    run_alexa()









'''

import subprocess


def app_open(app_name, search_query=None):
    app_name = app_name.replace("open", "").lower()

    # Opening Edge if specified and performing a search
    if 'edge' in app_name and search_query:
        search_url = f"https://www.google.com/search?q={search_query}"
        subprocess.call([r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", search_url])
    # Other app cases like calculator, explorer, etc.
    elif 'calculator' in app_name:
        subprocess.call(["calc.exe"])
    elif 'explorer' in app_name:
        subprocess.call(["explorer.exe"])



# Example usage
app_open("search edge", "cricket")
