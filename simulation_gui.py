import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import simulation
import teleportation
import weather_simulation
import laser_filamentation


SIMULATIONS = {
    "Base": simulation.create_animation,
    "Teleportation": teleportation.create_animation,
    "Weather": weather_simulation.create_animation,
    "Laser": laser_filamentation.create_animation,
}


class SimulationGUI(tk.Tk):
    """GUI to select and display Echofoam simulations."""

    def __init__(self):
        super().__init__()
        self.title("Echofoam Simulation Viewer")
        self.geometry("850x850")
        self.option = tk.StringVar(value="Base")
        self.selector = ttk.Combobox(self, textvariable=self.option, values=list(SIMULATIONS.keys()))
        self.selector.pack(fill="x", padx=5, pady=5)
        self.run_btn = ttk.Button(self, text="Run", command=self.start)
        self.run_btn.pack(padx=5, pady=5)
        self.view = tk.Frame(self)
        self.view.pack(expand=True, fill="both")
        self.canvas = None
        self.anim = None

    def start(self):
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
        create_func = SIMULATIONS[self.option.get()]
        fig, self.anim = create_func()
        self.canvas = FigureCanvasTkAgg(fig, master=self.view)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(expand=True, fill="both")


if __name__ == "__main__":
    SimulationGUI().mainloop()
