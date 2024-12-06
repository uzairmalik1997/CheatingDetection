import tkinter as tk
from tkinter import messagebox, ttk
import speech_recognition as sr
import requests
import threading

API_URL = "https://api-inference.huggingface.co/models/akshayvkt/detect-ai-text"
HEADERS = {"Authorization": "Bearer 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"}

def is_model_ready():
    try:
        response = requests.get(API_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        print(f"Model status response: {data}")  # Debugging statement
        return "error" not in data
    except requests.exceptions.RequestException as e:
        print(f"Exception during API request: {e}")  # Debugging statement
        return False

def query(payload):
    try:
        response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Exception during API request: {e}")  # Debugging statement
        return {"error": str(e)}

class CheatingDetectionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Cheating Detection in Interviews")
        self.root.geometry("600x400")
        self.root.configure(bg="#f0f0f0")

        # Create main frame
        self.main_frame = tk.Frame(root, bg="#f0f0f0")
        self.main_frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

        # Title label
        self.title_label = tk.Label(self.main_frame, text="Cheating Detection in Interviews", font=("Helvetica", 16), bg="#f0f0f0")
        self.title_label.pack(pady=10)

        # Instruction label
        self.instruction_label = tk.Label(self.main_frame, text="Press 'Start Listening' to begin capturing answers.", font=("Helvetica", 12), bg="#f0f0f0")
        self.instruction_label.pack(pady=5)

        # Text display area
        self.text_display = tk.Text(self.main_frame, wrap=tk.WORD, height=10, width=70, font=("Helvetica", 12), bg="#ffffff", bd=2, relief=tk.SUNKEN)
        self.text_display.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        # Buttons frame
        self.button_frame = tk.Frame(self.main_frame, bg="#f0f0f0")
        self.button_frame.pack(pady=10)

        self.start_button = tk.Button(self.button_frame, text="Start Listening", command=self.start_listening, width=20, bg="#4CAF50", fg="#ffffff", font=("Helvetica", 12))
        self.start_button.grid(row=0, column=0, padx=10)

        self.stop_button = tk.Button(self.button_frame, text="Stop Listening", command=self.stop_listening, width=20, bg="#f44336", fg="#ffffff", font=("Helvetica", 12), state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=10)

        self.quit_button = tk.Button(self.button_frame, text="Quit", command=self.quit_application, width=20, bg="#2196F3", fg="#ffffff", font=("Helvetica", 12))
        self.quit_button.grid(row=0, column=2, padx=10)

        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.listening = False
        self.model_ready = False
        self.full_answer = ""  # Holds the entire response

        self.update_status_label("Model is loading...")
        self.root.after(1000, self.check_model_status)

    def check_model_status(self):
        print("Checking if model is ready...")  # Debugging statement
        if is_model_ready():
            self.model_ready = True
            self.update_status_label("Model is ready. Press 'Start Listening' to begin.")
        else:
            self.update_status_label("Model is still loading... Retrying in 5 seconds.")
            self.root.after(5000, self.check_model_status)  # Check every 5 seconds

    def update_status_label(self, message):
        self.text_display.delete(1.0, tk.END)
        self.text_display.insert(tk.END, message + "\n")
        self.root.update_idletasks()

    def start_listening(self):
        if not self.model_ready:
            self.update_status_label("Model is not ready yet.")
            return

        self.listening = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.update_status_label("Listening for your answer...")

        self.listening_thread = threading.Thread(target=self.listen_for_full_answer)
        self.listening_thread.start()

    def stop_listening(self):
        self.listening = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.update_status_label("Stopped listening. Processing your answer...")

        # Analyze the full answer
        self.analyze_answer()

    def listen_for_full_answer(self):
        self.full_answer = ""
        print("Listening for full answer...")  # Debugging statement
        try:
            with self.microphone as mic:
                self.recognizer.adjust_for_ambient_noise(mic, duration=0.2)
                print("Listening...")  # Debugging statement

                while self.listening:
                    audio = self.recognizer.listen(mic)
                    try:
                        text = self.recognizer.recognize_google(audio)
                        self.full_answer += text + " "
                        print(f"Partial answer: {text}")  # Debugging statement
                        self.update_status_label(f"Recognized: {self.full_answer.strip()}")
                    except sr.UnknownValueError:
                        print("Could not understand audio.")  # Debugging statement
                    except sr.RequestError as e:
                        self.update_status_label(f"Could not request results; {e}")
                        print(f"RequestError: {e}")  # Debugging statement

        except Exception as e:
            print(f"Error during listening: {e}")  # Debugging statement

    def analyze_answer(self):
        if not self.full_answer:
            self.update_status_label("No answer detected.")
            return

        # Call the API with the full answer
        output = query({"inputs": self.full_answer.strip()})
        print(f"API Output: {output}")  # Debugging statement

        # Extract the labels and scores
        if isinstance(output, list) and len(output) > 0:
            labels_and_scores = output[0]
            human_score = None
            ai_score = None

            # Find scores for human and AI
            for item in labels_and_scores:
                if item['label'].lower() == 'human':
                    human_score = item['score']
                elif item['label'].lower() == 'ai':
                    ai_score = item['score']

            # If both scores are found, round and compare them
            if human_score is not None and ai_score is not None:
                human_score_rounded = round(human_score * 100, 2)
                ai_score_rounded = round(ai_score * 100, 2)

                if human_score > ai_score:
                    message = f"Text is mostly by a human (Human: {human_score_rounded}%, AI: {ai_score_rounded}%)"
                else:
                    message = f"Text is mostly by AI (AI: {ai_score_rounded}%, Human: {human_score_rounded}%)"
            else:
                message = "Unable to detect scores properly from API output."
        else:
            message = "Unexpected API output format."

        print(message)  # Debugging statement
        self.update_status_label(message)

    def quit_application(self):
        print("Quitting application...")  # Debugging statement
        self.listening = False
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = CheatingDetectionApp(root)
    root.mainloop()
