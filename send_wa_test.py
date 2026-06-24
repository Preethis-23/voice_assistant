import sys
import time
import webbrowser
import pyautogui

if len(sys.argv) < 3:
    print("Usage: send_wa_test.py <contact_name> <message>")
    sys.exit(1)

name = sys.argv[1]
message = sys.argv[2]

print(f"Opening WhatsApp Web and searching for {name}")
webbrowser.open('https://web.whatsapp.com')
# wait for page and potential QR scan
time.sleep(8)

# Try to focus and search
try:
    pyautogui.hotkey('ctrl', 'f')
    time.sleep(0.3)
    pyautogui.write(name, interval=0.05)
    time.sleep(0.8)
    pyautogui.press('esc')
    time.sleep(0.3)
    pyautogui.press('tab')
    time.sleep(0.2)
    pyautogui.press('enter')
    time.sleep(1)
    pyautogui.write(message, interval=0.05)
    pyautogui.press('enter')
    print('Message sent (attempted)')
except Exception as e:
    print('Automation failed:', e)
    sys.exit(2)
