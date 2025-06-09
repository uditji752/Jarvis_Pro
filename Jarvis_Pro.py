
import cv2
from cvzone.HandTrackingModule import HandDetector
from cvzone.FaceMeshModule import FaceMeshDetector
import speech_recognition as sr
import pyttsx3
import pyautogui
import webbrowser
import subprocess
import time
import numpy as np 
import traceback
from deepface import DeepFace
import datetime
import urllib.parse
import mediapipe as mp
import keyboard  

detector_hands = HandDetector(maxHands=2, detectionCon=0.8)
detector_face = FaceMeshDetector(maxFaces=1)
engine = pyttsx3.init()

ACTIVATE_PATTERN = [1, 1, 0, 0, 1]
jarvis_active = False
EMOTION_COOLDOWN_INCREMENTS = [10, 60, 180, 250, 500]
current_cooldown_index = 1
EMOTION_COOLDOWN = EMOTION_COOLDOWN_INCREMENTS[current_cooldown_index]

last_emotion_time = datetime.datetime.now()
last_spoken_emotion = None
emotion_tracking_active = True

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
hands_detector = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
game_mode_active = False

def speak(text):
    print(f"🤖 JARVIS: {text}")
    engine.say(text)
    engine.runAndWait()

def take_command():
    try:
        r = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                print("🎙️ Listening...")
                r.pause_threshold = 1
                audio = r.listen(source, timeout=5, phrase_time_limit=5)
            
            try:
                command = r.recognize_google(audio).lower()
                print(f"🗣️ Command: {command}")
                return command
            except sr.UnknownValueError:
                print("Could not understand audio")
                return ""
            except sr.RequestError as e:
                print(f"Could not request results; {e}")
                return ""
        except (sr.WaitTimeoutError, AttributeError) as e:
            print(f"Timeout or attribute error: {e}")
            return ""
    except Exception as e:
        print(f"Error in speech recognition: {e}")
        return ""

def process_command(query):
    global jarvis_active, game_mode_active, emotion_tracking_active
    
    if 'open notepad' in query:
        subprocess.Popen('notepad.exe')
    elif 'open chrome' in query:
        subprocess.Popen('chrome.exe')
    elif 'search on google' in query:
        search = query.replace("search on google", "").strip()
        webbrowser.open(f"https://www.google.com/search?q={search}")
    elif 'minimise all windows' in query:
        pyautogui.hotkey('win', 'd')
    elif 'copy all data' in query:
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.5)
        pyautogui.hotkey('ctrl', 'c')
    elif 'paste data' in query and 'paste data' in query:
        pyautogui.hotkey('ctrl', 'n')
        time.sleep(1)
        pyautogui.hotkey('ctrl', 'v')
    elif any(phrase in query for phrase in ['shut down', 'shutdown', 'deactivate', 'turn off']):
        if 'game' in query or 'game mode' in query:
            game_mode_active = False
            speak("Game mode deactivated")
            keyboard.release('left')
            keyboard.release('right')
        elif 'jarvis' in query or 'yourself' in query or 'assistant' in query:
            jarvis_active = False
            speak("JARVIS deactivated. Show the activation gesture to reactivate me.")
        else:
            speak("Do you want to shut down game mode or JARVIS?")
            
    elif any(phrase in query for phrase in ['exit completely', 'exit program', 'close program', 'quit program']):
        speak("Shutting down completely. Goodbye!")
        time.sleep(1)
        keyboard.release('left')
        keyboard.release('right')
        cap.release()
        cv2.destroyAllWindows()
        exit(0)
    elif any(keyword in query for keyword in ['play music', 'play song', 'play', 'listen to']):
        song_query = query
        for prefix in ['play music', 'play song', 'play', 'listen to']:
            if prefix in query:
                song_query = query.replace(prefix, '').strip()
                break
                
        if song_query:
            play_music_on_youtube(song_query)
        else:
            speak("What would you like me to play?")
    elif 'youtube' in query:
        if 'open youtube' in query:
            speak("Opening YouTube")
            webbrowser.open("https://www.youtube.com")
        else:
            search_term = query.replace('youtube', '').strip()
            if search_term:
                speak(f"Searching for {search_term} on YouTube")
                encoded_query = urllib.parse.quote(search_term)
                webbrowser.open(f"https://www.youtube.com/results?search_query={encoded_query}")
            else:
                speak("Opening YouTube")
                webbrowser.open("https://www.youtube.com")
    elif 'toggle emotion tracking' in query or 'emotion tracking' in query:
        emotion_tracking_active = not emotion_tracking_active
        speak(f"Emotion tracking {'activated' if emotion_tracking_active else 'deactivated'}")
    elif 'weather' in query:
        speak("I'll check the weather for you. Opening weather information.")
        webbrowser.open("https://www.accuweather.com")
    elif 'time' in query:
        current_time = datetime.datetime.now().strftime("%I:%M %p")
        speak(f"The current time is {current_time}")
    elif 'date' in query:
        current_date = datetime.datetime.now().strftime("%A, %B %d, %Y")
        speak(f"Today is {current_date}")
    elif any(phrase in query for phrase in ['who are you', 'introduce yourself', 'what can you do']):
        introduction = """
        I am JARVIS, your personal AI assistant. I can help you with various tasks like:
        Opening applications,
        Searching the web,
        Playing music,
        Detecting your emotions,
        And much more.
        Just ask me what you need!
        """
        speak(introduction)
    elif any(keyword in query for keyword in ['play game', 'play hill climb', 'game mode', 'hill climb racing']):
        speak("Opening game mode. Show me two thumbs up to control Hill Climb Racing!")
        game_mode_active = True
    else:
        speak("Command not recognized.")

def detect_jarvis_pattern(hands):
    if hands is None or not isinstance(hands, list) or len(hands) < 1:
        return False
    
    try:
        for hand in hands:
            fingers = detector_hands.fingersUp(hand)
            if detect_finger_pattern(fingers, ACTIVATE_PATTERN):
                return True
    except Exception as e:
        print(f"Error detecting JARVIS pattern: {e}")
    
    return False

def detect_finger_pattern(fingers, pattern=None):
    if pattern is None:
        pattern = ACTIVATE_PATTERN
        
    if isinstance(fingers, list) and len(fingers) == 5:
        return fingers == pattern
    return False

def detect_game_pattern(hands):
    if hands is None or not isinstance(hands, list) or len(hands) < 2:
        return False
    
    try:
        left_fingers = detector_hands.fingersUp(hands[0])
        right_fingers = detector_hands.fingersUp(hands[1])
        
        left_thumb_only = detect_finger_pattern(left_fingers, [1,0,0,0,0])
        right_thumb_only = detect_finger_pattern(right_fingers, [1,0,0,0,0])
        
        return left_thumb_only and right_thumb_only
    except Exception as e:
        print(f"Error detecting game pattern: {e}")
    
    return False

def handle_game_control(frame, hands):
    game_frame = frame.copy()
    cv2.putText(game_frame, "GAME MODE ACTIVE - Press 'G' to exit", (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    if hands is not None and isinstance(hands, list) and len(hands) > 0:
        hand_index = min(1, len(hands) - 1)
        hand = hands[hand_index]
        
        fingers = detector_hands.fingersUp(hand)
        
        if fingers is not None and isinstance(fingers, list):
            fingers_up_count = sum(fingers)
            
            if fingers_up_count >= 4:
                cv2.putText(game_frame, "Accelerate", (50, 70), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0,255,0), 3)
                keyboard.press('right')
                keyboard.release('left')
            elif fingers_up_count <= 1:
                cv2.putText(game_frame, "Brake", (50, 70), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0,0,255), 3)
                keyboard.press('left')
                keyboard.release('right')
            else:
                keyboard.release('left')
                keyboard.release('right')
                cv2.putText(game_frame, "Neutral", (50, 70), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255,255,0), 3)
                
        finger_text = f"Control Hand: {fingers}"
        cv2.putText(game_frame, finger_text, (10, 110), 
                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
    else:
        cv2.putText(game_frame, "No hand detected", (50, 70), 
                  cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        keyboard.release('left')
        keyboard.release('right')
    
    return game_frame

def detect_emotion(img):
    global last_emotion_time, last_spoken_emotion
    
    try:
        current_time = datetime.datetime.now()
        time_diff = (current_time - last_emotion_time).total_seconds()
        
        if time_diff < EMOTION_COOLDOWN:
            try:
                result = DeepFace.analyze(
                    img,
                    actions=['emotion'],
                    detector_backend='opencv',
                    enforce_detection=False
                )
                return result[0]['dominant_emotion']
            except:
                return None
                
        result = DeepFace.analyze(
            img,
            actions=['emotion'],
            detector_backend='opencv',
            enforce_detection=False
        )
        
        dominant_emotion = result[0]['dominant_emotion']
        
        if dominant_emotion != last_spoken_emotion or time_diff > 60:
            if dominant_emotion == 'happy':
                speak("You seem happy. Would you like to listen to some music?")
            elif dominant_emotion == 'sad':
                speak("You look a bit down. How about some cheerful music to brighten your day?")
            elif dominant_emotion == 'angry':
                speak("You seem frustrated. Would you like me to play some calming music?")
            elif dominant_emotion == 'surprise':
                speak("You look surprised! Did something unexpected happen?")
            elif dominant_emotion == 'fear':
                speak("You seem anxious. Is everything alright?")
            elif dominant_emotion == 'neutral':
                if last_spoken_emotion != 'neutral' or time_diff > 120:
                    speak("You appear calm and focused.")
            
            last_spoken_emotion = dominant_emotion
            last_emotion_time = current_time
            
        return dominant_emotion
        
    except Exception as e:
        print(f"Error in emotion detection: {e}")
        return None

def check_microphone():
    try:
        print("Checking available microphones...")
        import speech_recognition as sr
        mic_list = sr.Microphone.list_microphone_names()
        for i, mic in enumerate(mic_list):
            print(f"Microphone {i}: {mic}")
        print(f"Default microphone index: {sr.Microphone.get_default_device_index()}")
        return True
    except Exception as e:
        print(f"Error checking microphones: {e}")
        return False

def play_music_on_youtube(song_name):
    try:
        speak(f"Playing {song_name} on YouTube")
        
        encoded_query = urllib.parse.quote(f"{song_name} official music video")
        
        webbrowser.open(f"https://www.youtube.com/results?search_query={encoded_query}")
        
        time.sleep(2.5)
        
        pyautogui.click(x=400, y=360)
        
        return True
    except Exception as e:
        print(f"Error playing music: {e}")
        speak("I had trouble playing that song. Please try again.")
        return False

cap = cv2.VideoCapture(0)

mic_available = check_microphone()
if not mic_available:
    print("WARNING: No microphone detected or PyAudio issue. Voice commands will not work.")

while True:
    success, img = cap.read()
    if not success or img is None:
        print("Failed to capture image from camera")
        continue
        
    img = cv2.flip(img, 1)
    
    original_img = img.copy()
    display_img = original_img.copy()

    try:
        hands, hand_img = detector_hands.findHands(img)
        if hand_img is not None and isinstance(hand_img, np.ndarray):
            display_img = hand_img.copy()

        if hands is not None and isinstance(hands, list):
            if not game_mode_active:
                if detect_jarvis_pattern(hands):
                    jarvis_active = not jarvis_active
                    speak("JARVIS Activated" if jarvis_active else "JARVIS Deactivated")
                    time.sleep(1)
                
                elif len(hands) >= 2 and detect_game_pattern(hands):
                    game_mode_active = True
                    speak("Game mode activated! Control with hand gestures: open hand to accelerate, closed fist to brake.")
                    time.sleep(1)
            
            elif detect_jarvis_pattern(hands):
                game_mode_active = False
                speak("Exiting game mode. JARVIS is back online.")
                keyboard.release('left')
                keyboard.release('right')
                time.sleep(1)

        if game_mode_active:
            display_img = handle_game_control(display_img, hands)
            cv2.putText(display_img, "GAME MODE", (display_img.shape[1] - 150, display_img.shape[0] - 20), 
                      cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        else:
            if emotion_tracking_active:
                try:
                    dominant_emotion = detect_emotion(display_img)
                    
                    if dominant_emotion:
                        emotion_text = f"Emotion: {dominant_emotion.upper()}"
                        cv2.putText(display_img, emotion_text, (display_img.shape[1] - 300, 30), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
                        
                        cooldown_time = EMOTION_COOLDOWN
                        next_feedback = last_emotion_time + datetime.timedelta(seconds=cooldown_time)
                        time_remaining = max(0, (next_feedback - datetime.datetime.now()).total_seconds())
                        cooldown_text = f"Next feedback in: {int(time_remaining)}s"
                        cv2.putText(display_img, cooldown_text, (display_img.shape[1] - 300, 60), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
                except Exception as e:
                    print(f"Error in emotion detection process: {e}")

            if jarvis_active:
                try:
                    cv2.putText(display_img, "🎙️ Listening...", (display_img.shape[1]//2 - 100, 50), 
                              cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                    cv2.imshow("JARVIS AI", display_img)
                    cv2.waitKey(1)
                    
                    command = take_command()
                    if command:
                        print(f"Processing command: {command}")
                        process_command(command)
                    else:
                        print("No command detected or empty command")
                except Exception as e:
                    print(f"Error taking command: {e}")

            status = "ACTIVE" if jarvis_active else "STANDBY"
            cv2.putText(display_img, f"JARVIS: {status}", (10, 30), 
                      cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0) if jarvis_active else (0, 0, 255), 2)

            if hands is not None and isinstance(hands, list):
                for i, hand in enumerate(hands):
                    fingers = detector_hands.fingersUp(hand)
                    finger_text = f"Hand {i+1}: {fingers}"
                    cv2.putText(display_img, finger_text, (10, 70 + i*40), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

        cv2.imshow("JARVIS AI", display_img)
            
    except Exception as e:
        print(f"Error in processing: {e}")
        cv2.imshow("JARVIS AI - Assistant", original_img)
        
    key = cv2.waitKey(1)
    if key == 27:
        break
    elif key == ord('j'):
        jarvis_active = not jarvis_active
        game_mode_active = False
        speak("JARVIS Activated" if jarvis_active else "JARVIS Deactivated")
    elif key == ord('g'):
        game_mode_active = not game_mode_active
        if game_mode_active:
            jarvis_active = False
            speak("Game mode activated. Control with hand gestures.")
        else:
            speak("Game mode deactivated.")
            keyboard.release('left')
            keyboard.release('right')
cap.release()
cv2.destroyAllWindows()
