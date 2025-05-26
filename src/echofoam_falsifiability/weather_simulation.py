import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


def create_animation(frames: int = 20):
    """Return a lightweight weather simulation animation."""
    fig, ax = plt.subplots()
    x = np.linspace(0, 2 * np.pi, 100)
    line, = ax.plot(x, np.cos(x))
    ax.set_xlim(0, 2 * np.pi)
    ax.set_ylim(-1, 1)

    def update(frame: int):
        line.set_ydata(np.cos(x + frame * 0.2))
        return line,

    anim = FuncAnimation(fig, update, frames=frames, interval=50, blit=True)
    return fig, anim


if __name__ == "__main__":
    fig, anim = create_animation()
    plt.show()
