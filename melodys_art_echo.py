import json
import os
import io
from datetime import datetime
from tkinter import (
    Tk,
    Label,
    Entry,
    Button,
    Canvas,
    StringVar,
    OptionMenu,
    messagebox,
    colorchooser,
)

try:
    from PIL import Image
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

MEMORY_FILE = "melody_echo.json"
MOODS = {
    "Happy \U0001F604": "happy",
    "Sleepy \U0001F62A": "sleepy",
    "Brave \U0001F98A": "brave",
    "Silly \U0001F92A": "silly",
    "Shy \U0001F648": "shy",
    "Excited \U0001F929": "excited",
    "Curious \U0001F9D0": "curious",
    "Sad \U0001F622": "sad",
}


class MelodyArtEcho:
    def __init__(self, root: Tk):
        self.root = root
        root.title("Melody's Art Echo")
        root.geometry("500x500")
        root.configure(bg="#fbeffb")

        self.last_memory = self.load_memory()
        self.top_label = Label(
            root,
            text=self.last_memory,
            bg="#fbeffb",
            font=("Helvetica", 12, "italic"),
        )
        self.top_label.pack(pady=5)

        Label(root, text="What do you want to draw today?", bg="#fbeffb").pack()
        self.idea_entry = Entry(root, width=40)
        self.idea_entry.pack(pady=5)

        self.color = "#ff69b4"
        self.color_btn = Button(
            root,
            text="Pick a color",
            command=self.pick_color,
            bg=self.color,
        )
        self.color_btn.pack(pady=5)

        Label(root, text="What mood is your art today?", bg="#fbeffb").pack()
        self.mood_var = StringVar(value=list(MOODS.keys())[0])
        OptionMenu(root, self.mood_var, *MOODS.keys()).pack(pady=5)

        Button(root, text="Create Art", command=self.create_art).pack(pady=10)

        self.canvas = Canvas(root, width=400, height=300, bg="white")
        self.canvas.pack(pady=10)

        Button(root, text="Save My Art", command=self.save_art).pack(pady=5)

    def pick_color(self):
        color = colorchooser.askcolor(title="Pick a color", color=self.color)
        if color[1]:
            self.color = color[1]
            self.color_btn.configure(bg=self.color)

    def load_memory(self) -> str:
        if os.path.exists(MEMORY_FILE):
            try:
                with open(MEMORY_FILE) as f:
                    mem = json.load(f)
                return (
                    f"Last time, you drew a {mem['mood']} {mem['idea']} in {mem['color']}. "
                    "Want to draw something new?"
                )
            except Exception:
                return "Welcome back, Melody!"
        return "Hello Melody! Let's make some art."

    def save_memory(self, idea: str, mood: str, color: str):
        data = {"idea": idea, "mood": mood, "color": color}
        with open(MEMORY_FILE, "w") as f:
            json.dump(data, f)

    def create_art(self):
        idea = self.idea_entry.get().strip() or "mystery"
        mood_key = self.mood_var.get()
        mood = MOODS.get(mood_key, "happy")
        color = self.color
        self.canvas.delete("all")
        self.draw_shape(mood, color)
        self.canvas.create_text(
            200,
            280,
            text=f"{mood.title()} {idea}",
            fill=color,
            font=("Helvetica", 14, "bold"),
        )
        self.save_memory(idea, mood, color)

    def draw_shape(self, mood: str, color: str):
        c = self.canvas
        if mood == "happy":
            c.create_arc(50, 150, 350, 250, start=0, extent=180, fill=color, outline="")
        elif mood == "sleepy":
            c.create_oval(180, 120, 260, 200, fill=color, outline="")
            c.create_oval(200, 120, 280, 200, fill="white", outline="white")
        elif mood == "brave":
            c.create_polygon(150, 250, 200, 100, 250, 250, fill=color, outline="")
        elif mood == "silly":
            for i in range(20):
                c.create_oval(190 - i*2, 150 - i*2, 210 + i*2, 170 + i*2, outline=color)
        elif mood == "excited":
            points = [200, 100, 215, 160, 275, 160, 225, 190, 245, 250, 200, 210,
                      155, 250, 175, 190, 125, 160, 185, 160]
            c.create_polygon(points, fill=color, outline="")
        elif mood == "curious":
            c.create_arc(170, 110, 230, 190, start=0, extent=180, outline=color, width=4)
            c.create_oval(195, 200, 205, 210, fill=color, outline="")
        elif mood == "sad":
            c.create_arc(80, 180, 320, 260, start=180, extent=180, fill=color, outline="")
        else:  # shy
            c.create_oval(220, 160, 240, 180, fill=color, outline="")

    def save_art(self):
        if not PIL_AVAILABLE:
            messagebox.showinfo("Save My Art", "Pillow not available to save image.")
            return
        ps = self.canvas.postscript(colormode="color")
        img = Image.open(io.BytesIO(ps.encode("utf-8")))
        name = f"melody_art_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        img.save(name, "png")
        messagebox.showinfo("Save My Art", f"Saved as {name}")


if __name__ == "__main__":
    root = Tk()
    app = MelodyArtEcho(root)
    root.mainloop()
