import speech_recognition as sr
import pyttsx3
import pywhatkit

engine = pyttsx3.init()

def talk(text):
    engine.say(text)
    engine.runAndWait()

def take_command():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        try:
            voice = recognizer.listen(source)
            command = recognizer.recognize_google(voice).lower()
            if 'play' in command:
                return command
        except:
            return ""
    return ""

def play_song():
    command = take_command()
    if command:
        song = command.replace('play', '').strip()
        talk(f"Playing {song} on YouTube")
        pywhatkit.playonyt(song)

play_song()







import speech_recognition as sr
import pyttsx3
import webbrowser as wb
import pywhatkit
import subprocess
import datetime
from num2words import num2words

inp=pyttsx3.init()
recog=sr.Recognizer()
inp.setProperty('rate', 150)  # Set speech rate & can be max of 200 ( measured in wpm)
inp.setProperty('volume', 1.0)  # Set volume to maximum

voices=inp.getProperty('voices')
inp.setProperty('voice',voices[1].id)
inp.say("Hello KIRA, How can i help you?")
print("Hello Kira, How can i help you?")
inp.runAndWait()

def youtube():
    wb.open("https://www.youtube.com")
    inp.say("Opening Youtube")
    inp.runAndWait()


def play_song(song_name):
    song_name=song_name.replace("play","")
    inp.say(f"Playing {song_name}")
    pywhatkit.playonyt(song_name)

def app_open(app_name):
    app_name=app_name.replace("open","").lower()
    if 'calculator' in app_name:
        inp.say("Opening Calculator")
        subprocess.call(["calc.exe"])
    elif 'explorer' in app_name:
        inp.say("Opening Explorer")
        subprocess.call(["explorer.exe"])
    elif 'browser' in app_name:
        #subprocess.call([r'C:\ProgramData\Microsoft\Windows\Start Menu\Programs\msedge.exe'])
        subprocess.call([r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"])
    elif 'chrome' in app_name:
        subprocess.call([r"C:\Program Files\Google\Chrome\Application\chrome.exe"])

def search(term):
    term=term.replace('search', "").lower()
    url=f"https://www.google.com/search?q={term}"
    subprocess.call([r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", url])

def timee():
    current=datetime.datetime.now()
   # print(current.strftime("%H:%M:%S")) 24-hour format
    c_time = current.strftime("%I:%M %p") # 12-hour format
    c_date = current.strftime("%d:%m:%Y") # date,month,year
    c_day = current.strftime("%A") # week day

    voice=f"Today is {c_day}, {c_date}, and time is {c_time}"
    print(voice)
    inp.say(voice)
    inp.runAndWait()

def time():
    current = datetime.datetime.now()

    # Format time for display
    c_time_display = current.strftime("%I:%M %p").lstrip('0').replace(" 0", " ")

    # Convert to a more natural way of speaking for time
    c_time_speech = current.strftime("%I %M %p").lstrip('0').replace(" 0", " ")
    c_time_speech = c_time_speech.replace("AM", "A M").replace("PM", "P M")

    # Format date for display
    day = int(current.strftime("%d"))
    month = current.strftime("%B")
    year = current.strftime("%Y")

    # Get the correct suffix for the day (1st, 2nd, 3rd, etc.)
    suffix = "th" if 11 <= day <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
    c_date_display = f"{day}{suffix} {month} {year}"

    # Convert the date to natural speech format
    c_date_speech = f"{day}{suffix} {month} {year}"
    c_date_speech = c_date_speech.replace(str(day), num2words(day))  # Use num2words for natural day conversion
    c_date_speech = c_date_speech.replace(str(year), num2words(year))  # Convert year to natural language

    # Get the current weekday
    c_day = current.strftime("%A")

    # Construct the voice output for speaking
    voice = f"Today is {c_day}, {c_date_speech}, and the time is {c_time_speech}"

    print(f"Display Format: {c_day}, {c_date_display}, and time is {c_time_display}")
   # print(f"Voice: {voice}")
    inp.say(voice)
    inp.runAndWait()





def command(text):
    text = text.lower()
    if 'display time' in text.lower() or 'current time' in text.lower() or 'time' in text.lower():
        time()
    elif "youtube" in text:
        youtube()
    elif "open" in text:
        app_open(text)
    elif 'search' in text:
        search(text)
    elif "play" in text:
          #  song_name=text.split("play")[-1].strip()
        play_song(text)

def recognition():
  print("Listening....:)")
  with sr.Microphone() as source:
      #recog.adjust_for_ambient_noise(source, duration=3)
      recog.pause_threshold=3
      try:
        rg=recog.listen(source, phrase_time_limit=17)
        print("Audio received")

        text=recog.recognize_google(rg)
        print(text)

        inp.say(text)
        inp.runAndWait()
        command(text)
      except sr.UnknownValueError:
        print("Sorry, I couldn't understand the audio.")
        inp.say("Sorry, I couldn't understand the audio.")
        inp.runAndWait()

      except sr.RequestError:ip
        print("There was an issue with the Google Speech Recognition service.")
        inp.say("There was an issue with the Google Speech Recognition service.")
        inp.runAndWait()

      except AttributeError as e:
        print("Microphone not initialized properly:", e)
        inp.say("Microphone not initialized properly.")
        inp.runAndWait()


recognition()