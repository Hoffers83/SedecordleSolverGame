from tkinter import *
import tkinter as tk
import json
import random
import time
import string


SEED_CHARACTERS = string.ascii_uppercase[:22] + "0123456789"  # 32-bits A-V,0-9
SEED_LENGTH = 32  # 32-bits
SEED_FILE = "sedecordle_seeds.json"
USER_FILE = "users.json"
DEV_KEY = "+devkey"


# Load in word library
def load_word_library(filename):
    try:
        with open(filename, "r") as file:
            return [word.upper() for word in json.load(file)]
    except FileNotFoundError:
        print(f"Error: File not found at {filename}")
        return []
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {filename}")
        return []


def load_users():
    try:
        with open(USER_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_users(users):
    with open(USER_FILE, "w") as file:
        json.dump(users, file, indent=4)


def authenticate(username, password):
    users = load_users()
    return users.get(username) == password


def register_user(username, password):
    users = load_users()
    if username in users:
        return False
    users[username] = password
    save_users(users)
    return True


def generate_seed():
    return "".join(random.choice(SEED_CHARACTERS) for _ in range(SEED_LENGTH))


def save_seed(seed, words):
    try:
        with open(SEED_FILE, "r") as file:
            seed_data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        seed_data = {}

    seed_data[seed] = words

    with open(SEED_FILE, "w") as file:
        json.dump(seed_data, file, indent=4)


def load_seed(seed):
    try:
        with open(SEED_FILE, "r") as file:
            seed_data = json.load(file)
        return seed_data.get(seed, None)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def get_seeded_words(word_library, seed=None):
    if seed and (words := load_seed(seed)):
        return words, seed  # Return stored words if seed exists

    new_seed = generate_seed() if seed is None else seed
    random.seed(new_seed)  # Set random seed based on input seed
    words = random.sample(word_library, 16)  # Generate word sequence
    save_seed(new_seed, words)  # Save new seed and words
    return words, new_seed


class SedecordleSolver:
    def __init__(self, root, word_library, seed=None):
        self.root = root
        self.root.title("Sedecordle Solver")

        self.word_library = word_library
        self.logged_in = False
        self.is_developer = False
        self.create_login_screen()
        self.target_words, self.seed = get_seeded_words(word_library, seed)
        self.completed_grids = set()
        self.timer_running = False
        self.start_time = None
        self.end_time = None

    def create_login_screen(self):
        self.login_frame = tk.Frame(self.root, bg="lightgray", padx=400, pady=400)
        self.root.geometry("700x350")
        self.login_frame.place(relx=0.5, rely=0.5, anchor=CENTER)

        tk.Label(self.login_frame, text="Username:", bg="lightgray").grid(row=0, column=0, pady=5)
        self.username_entry = tk.Entry(self.login_frame, width=30)
        self.username_entry.grid(row=0, column=1, pady=5)

        tk.Label(self.login_frame, text="Password:", bg="lightgray").grid(row=1, column=0, pady=5)
        self.password_entry = tk.Entry(self.login_frame, width=30, show="*")
        self.password_entry.grid(row=1, column=1, pady=5)

        self.login_button = tk.Button(self.login_frame, text="Enter", command=self.login)
        self.login_button.grid(row=2, column=0, columnspan=2, pady=5)

        self.register_button = tk.Button(self.login_frame, text="Register", command=self.register)
        self.register_button.grid(row=3, column=0, columnspan=2, pady=5)

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if authenticate(username, password):
            self.logged_in = True
            self.is_developer = username.endswith(DEV_KEY)
            self.login_frame.destroy()
            self.init_game()
        else:
            tk.Label(self.login_frame, text="Invalid credentials!", fg="red", bg="lightgray").grid(row=4, column=0,
                                                                                                   columnspan=2)

    def register(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if register_user(username, password):
            tk.Label(self.login_frame, text="Registration successful!", fg="green", bg="lightgray").grid(row=4,
                                                                                                         column=0,
                                                                                                         columnspan=2)
        else:
            tk.Label(self.login_frame, text="User already exists!", fg="red", bg="lightgray").grid(row=4, column=0,
                                                                                                   columnspan=2)

    def init_game(self):
        self.game_frame = tk.Frame(self.root, padx=5, pady=5)
        self.game_frame.pack()

        print("Game Seed:", self.seed)
        print("Target Words: ", self.target_words)

        self.game_frame = tk.Frame(self.root, padx=5, pady=5)
        self.game_frame.pack()

        self.rows = 20
        self.cols = 5
        self.current_row = 0
        self.start_time = time.time()

        self.grids = []
        for grid_index in range(16):
            grid_frame = tk.Frame(self.game_frame, relief="solid", borderwidth=1, padx=5, pady=5)
            grid_frame.grid(row=grid_index // 8, column=grid_index % 8, padx=10, pady=10)
            grid_frame.config(bg="gray42")

            grid = []
            for row in range(self.rows):
                row_entries = []
                for col in range(self.cols):
                    box = tk.Entry(grid_frame, width=5, borderwidth=2, relief="solid", justify=tk.CENTER)
                    box.grid(row=row, column=col, padx=5, pady=5)
                    box.config(state=tk.DISABLED, disabledbackground="lightgray")
                    row_entries.append(box)
                grid.append(row_entries)
            self.grids.append(grid)

        # Ensure solver button appears correctly without conflicting with grid layout
        if self.is_developer:
            self.solver_button = tk.Button(self.game_frame, text="Solver Mode", command=self.toggle_solver)
            self.solver_button.grid(row=21, column=0, padx=10, pady=5, sticky="w")

        self.input_frame = tk.Frame(self.root, pady=5)
        self.input_frame.pack()

        # Timer label (positioned left of input box)
        self.timer_label = tk.Label(self.input_frame, text="00:00:000", font=("Courier", 12))
        self.timer_label.pack(side=tk.LEFT, padx=10)

        self.input_label = tk.Label(self.input_frame, text="Enter a 5-letter word:")
        self.input_label.pack(side=tk.LEFT, padx=5)

        self.input_box = tk.Entry(self.input_frame, width=15, justify=tk.CENTER)
        self.input_box.pack(side=tk.LEFT, padx=5)
        self.input_box.bind("<Return>", self.enter_word)

        self.submit_button = tk.Button(self.input_frame, text="Enter", command=self.enter_word)
        self.submit_button.pack(side=tk.LEFT, padx=5)

        # Display the current seed at the bottom right of the input frame
        self.seed_label = tk.Label(self.input_frame, text=f"Seed: {self.seed}", font=("Courier", 10))
        self.seed_label.pack(side=tk.RIGHT, padx=10)

        # Seed entry box
        self.seed_entry_label = tk.Label(self.input_frame, text="Enter Seed:", font=("Courier", 10))
        self.seed_entry_label.pack(side=tk.LEFT, padx=5)
        self.seed_entry = tk.Entry(self.input_frame, width=38, justify=tk.CENTER)
        self.seed_entry.pack(side=tk.LEFT, padx=5)
        self.seed_entry_button = tk.Button(self.input_frame, text="Load Seed", command=self.load_new_seed)
        self.seed_entry_button.pack(side=tk.LEFT, padx=5)

        self.dark_mode_frame = tk.Frame(self.root, pady=5)
        self.dark_mode_frame.pack()

        self.dark_mode_button = tk.Button(self.root, text="Toggle Dark Mode", command=self.toggle_dark_mode)
        self.dark_mode_button.pack(pady=5)

        self.is_dark_mode = False
        self.apply_theme()

        self.update_timer()

    def toggle_solver(self):
        print("Solver mode toggled")
        self.auto_fill_target_words()

    def auto_fill_target_words(self):
        for word in self.target_words:
            self.input_box.delete(0, tk.END)
            self.input_box.insert(0, word)
            self.enter_word()
            print(f"Word inputted: {word}")

    def enter_word(self, event=None):
        if not self.timer_running:
            self.start_timer()

        self.check_completion()
        word = self.input_box.get().strip().upper()

        if len(word) != 5 or word not in self.word_library:
            self.input_label.config(text="Invalid 5-letter word!")
            return

        if self.current_row >= self.rows:
            self.input_label.config(text="All rows are filled!")
            return

        for i, target_word in enumerate(self.target_words):
            if i not in self.completed_grids:  # Skip completed grids
                self.fill_grid(word, self.grids[i])
                self.highlight_grid(word, self.grids[i], target_word, i)

        self.input_box.delete(0, tk.END)
        self.current_row += 1

    def fill_grid(self, word, grid):
        for col in range(self.cols):
            entry = grid[self.current_row][col]
            entry.config(state=tk.NORMAL)
            entry.delete(0, tk.END)
            entry.insert(0, word[col])
            entry.config(state=tk.DISABLED)

    def highlight_grid(self, word, grid, target_word, grid_index):
        target_word = list(target_word)
        word = list(word)
        correct = True

        for i in range(self.cols):
            entry = grid[self.current_row][i]
            entry.config(state=tk.NORMAL)
            if word[i] == target_word[i]:
                entry.config(bg="darkgreen")
            elif word[i] in target_word:
                entry.config(bg="orange")
                correct = False
            else:
                correct = False

        if correct:
            self.completed_grids.add(grid_index)

    def update_timer(self):
        if self.timer_running:
            elapsed_time = time.time() - self.start_time
            minutes = int(elapsed_time // 60)
            seconds = int(elapsed_time % 60)
            milliseconds = int((elapsed_time % 1) * 1000)
            self.timer_label.config(text=f"{minutes:02}:{seconds:02}:{milliseconds:03}")
            self.root.after(1, self.update_timer)

    def start_timer(self):
        if not self.timer_running:
            self.start_time = time.time()
            self.timer_running = True
            self.update_timer()

    def stop_timer(self):
        if self.timer_running:
            self.timer_running = False
            self.end_time = time.time()
            print(f"Final Time: {self.timer_label.cget('text')}")

    def check_completion(self):
        if len(self.completed_grids) == 16:
            self.stop_timer()

    def toggle_dark_mode(self):
        self.is_dark_mode = not self.is_dark_mode
        self.apply_theme()

    def apply_theme(self):
        bg_color = "gray22" if self.is_dark_mode else "white"
        btn_bg = "gray36" if self.is_dark_mode else "lightgray"
        fg_color = "white" if self.is_dark_mode else "black"
        self.root.config(bg=bg_color)
        self.game_frame.config(bg=bg_color)
        self.input_frame.config(bg=bg_color)
        self.seed_label.config(bg=bg_color, fg=fg_color)
        self.seed_entry_label.config(bg=bg_color, fg=fg_color)
        self.seed_entry.config(bg=btn_bg, fg=fg_color, insertbackground=fg_color)
        self.seed_entry_button.config(bg=btn_bg, fg=fg_color)
        self.input_label.config(bg=bg_color, fg=fg_color)
        self.input_box.config(bg=btn_bg, fg=fg_color, insertbackground=fg_color)
        self.submit_button.config(bg=btn_bg, fg=fg_color)
        self.dark_mode_button.config(bg=btn_bg, fg=fg_color)
        self.timer_label.config(bg=bg_color, fg=fg_color)
        for grid in self.grids:
            for row in grid:
                for entry in row:
                    entry.config(bg=btn_bg, fg=fg_color, insertbackground=fg_color, disabledbackground=bg_color)

    def load_new_seed(self):
        new_seed = self.seed_entry.get().strip().upper()
        if len(new_seed) == SEED_LENGTH and all(c in SEED_CHARACTERS for c in new_seed):
            self.target_words, self.seed = get_seeded_words(self.word_library, new_seed)
            self.seed_label.config(text=f"Seed: {self.seed}")  # Update the displayed seed
            print("Loaded new seed:", self.seed)
        else:
            print("Invalid seed format.")

def game(seed=None):
        word_library = load_word_library(r"5_letter_words.json")
        if not word_library:
            print("No valid word library loaded. Exiting.")
            return
        root = tk.Tk()
        app = SedecordleSolver(root, word_library, seed)
        root.mainloop()

game()
