import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import os


def create_animation(
    grid_size: int = 128,
    timesteps: int = 400,
    alpha: float = 0.01,
    beta: float = 0.05,
    collapse_threshold: float = 2.0,
    intensity_threshold: float = 0.1,
):
    """Return animation for the laser filamentation simulation."""
    x = np.linspace(-1, 1, grid_size)
    y = np.linspace(-1, 1, grid_size)
    X, Y = np.meshgrid(x, y)
    psi = np.exp(-(X ** 2 + Y ** 2) * 20).astype(np.complex128)
    tau = np.ones((grid_size, grid_size))
    chi_history = []

    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    im0 = axes[0].imshow(np.abs(psi), origin="lower", cmap="viridis", vmin=0, vmax=1, animated=True)
    axes[0].set_title(r"$|\psi|")
    fig.colorbar(im0, ax=axes[0])

    im1 = axes[1].imshow(tau, origin="lower", cmap="plasma", vmin=1, vmax=collapse_threshold, animated=True)
    axes[1].set_title(r"$\tau$")
    fig.colorbar(im1, ax=axes[1])

    line2, = axes[2].plot([], [])
    axes[2].set_xlim(0, timesteps)
    axes[2].set_ylim(0, 1)
    axes[2].set_title(r"$\chi$")

    os.makedirs("frames", exist_ok=True)

    def update(frame):
        nonlocal psi, tau
        psi = np.roll(psi, 1, axis=1)
        intensity = np.abs(psi) ** 2
        tau += alpha * intensity
        tau += beta * (intensity > intensity_threshold) * intensity ** 2
        if np.any(tau > collapse_threshold):
            psi = (
                np.random.rand(grid_size, grid_size) + 1j * np.random.rand(grid_size, grid_size)
            ) * 0.1
            tau[:] = 1.0
            chi = 0.0
        else:
            chi = np.abs(np.mean(psi)) / (np.mean(np.abs(psi)) + 1e-8)
        chi_history.append(chi)
        psi *= 0.999

        im0.set_data(np.abs(psi))
        im1.set_data(tau)
        line2.set_data(range(len(chi_history)), chi_history)

        if frame % 50 == 0:
            fig.savefig(f"frames/frame_{frame:04d}.png")
        return im0, im1, line2

    ani = FuncAnimation(fig, update, frames=timesteps, interval=50, blit=True, repeat=False)
    fig.tight_layout()
    return fig, ani


def run(headless: bool = True):
    fig, ani = create_animation()
    if headless:
        ani.save("laser.mp4", writer="ffmpeg")
        if ani.event_source is not None:
            ani.event_source.stop()
        plt.close(fig)
    else:
        plt.show()


if __name__ == "__main__":
    run(headless=True)
