import cv2
import mediapipe as mp
import time

# Initialize MediaPipe hands.
mp_hands = mp.solutions.hands # type: ignore
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.7)

# Initialize MediaPipe drawing.
mp_drawing = mp.solutions.drawing_utils # type: ignore

# List to store detected letters and form words
detected_text = []
previous_binary_number = None
previous_message = ""
previous_formed_text = ""
last_gesture_time = 0
gesture_delay = 1  # seconds
backspace_gesture_detected = False
backspace_last_time = 0
current_letter = ""  # To store the current letter to be displayed on the frame

# Function to calculate binary number from finger positions
def calculate_binary_number(hand_landmarks):
    # Tip landmarks for index, middle, ring, and little fingers
    finger_tips = [8, 12, 16, 20]
    binary_number = 0

    # Check thumb (least significant bit)
    if hand_landmarks.landmark[4].x < hand_landmarks.landmark[3].x:
        binary_number += 1

    # Check other fingers
    for idx, tip_id in enumerate(finger_tips):
        if hand_landmarks.landmark[tip_id].y < hand_landmarks.landmark[tip_id - 2].y:
            binary_number += 2 ** (idx + 1)
    
    return binary_number

# Function to map binary number to corresponding alphabet or special messages
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

# Function to check if only 4 fingers are raised (excluding thumb)
def four_fingers_except_thumb(hand_landmarks):
    finger_tips = [8, 12, 16, 20]
    if hand_landmarks.landmark[4].x > hand_landmarks.landmark[3].x:  # Thumb should not be raised
        for tip_id in finger_tips:
            if hand_landmarks.landmark[tip_id].y > hand_landmarks.landmark[tip_id - 2].y:
                return False
        return True
    return False

# Start capturing video input
cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Flip the frame horizontally for a later selfie-view display
    frame = cv2.flip(frame, 1)

    # Convert the BGR image to RGB
    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Process the image and find hands
    results = hands.process(image)

    # Convert the image back to BGR for rendering
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Draw hand landmarks
            mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Calculate binary number from finger positions
            current_time = time.time()
            if current_time - last_gesture_time > gesture_delay:
                binary_number = calculate_binary_number(hand_landmarks)
                last_gesture_time = current_time

                if binary_number != previous_binary_number:
                    previous_binary_number = binary_number

                    # Map binary number to message
                    message = binary_to_message(binary_number)

                    # Append the letter to detected_text if a valid letter is detected
                    if message and message != previous_message:
                        previous_message = message
                        if message.isalpha() or message == ' ':
                            detected_text.append(message)
                            current_letter = message  # Update the current letter to be displayed
                            print(f"\rDetected: {message}", end="")
                        elif message == "Not found!":
                            print("\rNot found!", end="")

                    # Display the current letter on the image
                    if message and message.isalpha():
                        current_letter = message  # Update the current letter to be displayed

            # Check for four fingers except thumb to remove the last character
            if four_fingers_except_thumb(hand_landmarks):
                if current_time - backspace_last_time > gesture_delay:
                    backspace_last_time = current_time
                    if detected_text:
                        detected_text.pop()
                        previous_formed_text = ''.join(detected_text)
                        print("\r" + " " * 80, end="")  # Clear the previous output by overwriting with spaces
                        print(f"\rFormed text: {previous_formed_text}", end="")
            else:
                backspace_gesture_detected = False

    # Display the current letter on the image
    if current_letter:
        cv2.putText(image, current_letter, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 5, cv2.LINE_AA)

    # Display the formed text on the terminal only if it has changed
    formed_text = ''.join(detected_text)
    if formed_text != previous_formed_text:
        print(f"\rFormed text: {formed_text}", end="")
        previous_formed_text = formed_text

    # Show the image
    cv2.imshow('Hand Tracking', image)

    # Break the loop on 'q' key press
    if cv2.waitKey(10) & 0xFF == ord('q'):
        break
    
# Release the capture
cap.release()
cv2.destroyAllWindows()
