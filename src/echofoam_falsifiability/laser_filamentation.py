import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


def create_animation(frames: int = 20):
    """Return a simple laser filamentation animation."""
    fig, ax = plt.subplots()
    im = ax.imshow(np.zeros((10, 10)), vmin=0, vmax=1, cmap="viridis")

    def update(frame: int):
        im.set_data(np.random.rand(10, 10))
        return im,

    anim = FuncAnimation(fig, update, frames=frames, interval=50, blit=True)
    return fig, anim


if __name__ == "__main__":
    fig, anim = create_animation()
    plt.show()
