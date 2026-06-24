import os
import sys
import time
import subprocess
import urllib.parse

try:
    import pyautogui
except Exception as e:
    print('pyautogui import failed:', e)
    raise
try:
    import pygetwindow as gw
except Exception:
    gw = None

name = sys.argv[1] if len(sys.argv) > 1 else 'Muthu DS'
message = sys.argv[2] if len(sys.argv) > 2 else 'deu'

candidates = []
local_appdata = os.environ.get('LOCALAPPDATA')
program_files = os.environ.get('ProgramFiles')
if local_appdata:
    candidates.append(os.path.join(local_appdata, 'WhatsApp', 'WhatsApp.exe'))
if program_files:
    candidates.append(os.path.join(program_files, 'WhatsApp', 'WhatsApp.exe'))

# Try to start WhatsApp Desktop
started = False
for exe in candidates:
    if exe and os.path.exists(exe):
        try:
            subprocess.Popen([exe])
            started = True
            break
        except Exception as e:
            print('Failed to start', exe, e)

if not started:
    # Try protocol handler
    try:
        # This should open WhatsApp Desktop if installed and registered
        url = 'whatsapp://'
        os.startfile(url)
        started = True
    except Exception as e:
        print('Protocol open failed:', e)

if not started:
    print('Could not open WhatsApp Desktop; will open WhatsApp Web instead')
    import webbrowser
    webbrowser.open('https://web.whatsapp.com')

# wait for app to be ready
time.sleep(6)
def focus_whatsapp_window():
    if not gw:
        return False
    try:
        for w in gw.getAllWindows():
            title = (w.title or "").lower()
            if 'whatsapp' in title:
                try:
                    w.activate()
                    time.sleep(0.5)
                    return True
                except Exception:
                    pass
    except Exception:
        pass
    return False

# Use search shortcut for WhatsApp Desktop (Ctrl+K). For WhatsApp Web, Ctrl+F then type
# Try to focus the WhatsApp window first and use Ctrl+K; otherwise fall back to web method
try:
    focused = focus_whatsapp_window()
    if not focused:
        # try a bit longer in case app is still launching
        time.sleep(2)
        focused = focus_whatsapp_window()

    if focused:
        # Use Ctrl+F to open the search bar (works for many versions)
        time.sleep(0.2)
        pyautogui.hotkey('ctrl', 'f')
        time.sleep(0.3)
        pyautogui.write(name, interval=0.05)
        time.sleep(0.8)
        # Press enter to open the first matched contact
        pyautogui.press('enter')
        time.sleep(0.6)
        # Ensure chat is focused; if not, try an extra enter
        pyautogui.press('enter')
        time.sleep(0.4)
        pyautogui.write(message, interval=0.05)
        pyautogui.press('enter')
        print('Desktop flow attempted (Ctrl+F)')
    else:
        # Try image-based click on search icon first
        templates = [
            os.path.join(os.path.dirname(__file__), 'whatsapp_search.png'),
            os.path.join(os.path.dirname(__file__), 'whatsapp_search_icon.png'),
        ]
        clicked = False
        for tpl in templates:
            if os.path.exists(tpl):
                try:
                    loc = pyautogui.locateCenterOnScreen(tpl, confidence=0.8)
                    if loc:
                        pyautogui.click(loc)
                        time.sleep(0.3)
                        pyautogui.write(name, interval=0.05)
                        time.sleep(0.6)
                        pyautogui.press('enter')
                        time.sleep(0.8)
                        pyautogui.write(message, interval=0.05)
                        pyautogui.press('enter')
                        print('Image-click flow attempted using', tpl)
                        clicked = True
                        break
                except Exception as e:
                    print('Image locate failed for', tpl, e)

        if not clicked:
            # fallback to ctrl+f web-style search
            pyautogui.hotkey('ctrl', 'f')
            time.sleep(0.3)
            pyautogui.write(name, interval=0.05)
            time.sleep(0.8)
            pyautogui.press('esc')
            pyautogui.press('tab')
            pyautogui.press('enter')
            time.sleep(1)
            pyautogui.write(message, interval=0.05)
            pyautogui.press('enter')
            print('Web fallback attempted')
except Exception as e:
    print('Send attempt failed:', e)
