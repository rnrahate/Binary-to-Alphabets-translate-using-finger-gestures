import cv2
import mediapipe as mp
import time

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.7)

mp_drawing = mp.solutions.drawing_utils

detected_text = []
previous_binary_number = None
previous_message = ""
previous_formed_text = ""
last_gesture_time = 0
gesture_delay = 1
backspace_gesture_detected = False
backspace_last_time = 0
current_letter = ""

def calculate_binary_number(hand_landmarks):
    finger_tips = [8, 12, 16, 20]
    binary_number = 0

    if hand_landmarks.landmark[4].x < hand_landmarks.landmark[3].x:
        binary_number += 1

    for idx, tip_id in enumerate(finger_tips):
        if hand_landmarks.landmark[tip_id].y < hand_landmarks.landmark[tip_id - 2].y:
            binary_number += 2 ** (idx + 1)
    
    return binary_number

def binary_to_message(binary_number):
    if binary_number == 0:
        return None
    elif 1 <= binary_number <= 26:
        return chr(64 + binary_number)
    elif 27 <= binary_number <= 30:
        return "Not found!"
    elif binary_number == 31:
        return ' '
    return None

def four_fingers_except_thumb(hand_landmarks):
    finger_tips = [8, 12, 16, 20]
    if hand_landmarks.landmark[4].x > hand_landmarks.landmark[3].x:
        for tip_id in finger_tips:
            if hand_landmarks.landmark[tip_id].y > hand_landmarks.landmark[tip_id - 2].y:
                return False
        return True
    return False

cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(image)
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            current_time = time.time()
            if current_time - last_gesture_time > gesture_delay:
                binary_number = calculate_binary_number(hand_landmarks)
                last_gesture_time = current_time

                if binary_number != previous_binary_number:
                    previous_binary_number = binary_number
                    message = binary_to_message(binary_number)

                    if message and message != previous_message:
                        previous_message = message
                        if message.isalpha() or message == ' ':
                            detected_text.append(message)
                            current_letter = message
                            print(f"\rDetected: {message}", end="")
                        elif message == "Not found!":
                            print("\rNot found!", end="")

                    if message and message.isalpha():
                        current_letter = message

            if four_fingers_except_thumb(hand_landmarks):
                if current_time - backspace_last_time > gesture_delay:
                    backspace_last_time = current_time
                    if detected_text:
                        detected_text.pop()
                        previous_formed_text = ''.join(detected_text)
                        print("\r" + " " * 80, end="")
                        print(f"\rFormed text: {previous_formed_text}", end="")
            else:
                backspace_gesture_detected = False

    if current_letter:
        cv2.putText(image, current_letter, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 5, cv2.LINE_AA)

    formed_text = ''.join(detected_text)
    if formed_text != previous_formed_text:
        print(f"\rFormed text: {formed_text}", end="")
        previous_formed_text = formed_text

    cv2.imshow('Hand Tracking', image)

    if cv2.waitKey(10) & 0xFF == ord('q'):
        break
    
cap.release()
cv2.destroyAllWindows()