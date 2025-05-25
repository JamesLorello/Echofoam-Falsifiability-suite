import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


def create_animation(size: int = 50, steps: int = 200):
    """Return animation for the weather simulation."""
    np.random.seed(0)
    tau = np.random.randn(size, size) * 0.5
    psi = np.zeros((size, size))
    chi = np.zeros((size, size))

    fig, axes = plt.subplots(2, 2, figsize=(8, 8))
    im_tau = axes[0, 0].imshow(tau, cmap="coolwarm", vmin=-2, vmax=2, animated=True)
    axes[0, 0].set_title("tau")

    grad_x, grad_y = np.gradient(tau)
    grad_mag = np.sqrt(grad_x ** 2 + grad_y ** 2)
    im_grad = axes[0, 1].imshow(grad_mag, cmap="viridis", animated=True)
    axes[0, 1].set_title("∇tau")

    im_psi = axes[1, 0].imshow(psi, cmap="plasma", vmin=0, vmax=1, animated=True)
    axes[1, 0].set_title("psi")

    im_chi = axes[1, 1].imshow(chi, cmap="inferno", vmin=0, vmax=1, animated=True)
    axes[1, 1].set_title("chi")

    for ax_row in axes:
        for ax in ax_row:
            ax.set_xticks([])
            ax.set_yticks([])

    frames_to_save = []

    def update(frame):
        nonlocal tau, psi, chi, grad_x, grad_y, grad_mag
        tau += 0.05 * np.random.randn(size, size)
        tau *= 0.99
        if frame == 50:
            pulse = np.zeros_like(tau)
            cx = cy = size // 2
            pulse[cx - 2 : cx + 3, cy - 2 : cy + 3] = 5.0
            tau += pulse
        grad_x, grad_y = np.gradient(tau)
        grad_mag = np.sqrt(grad_x ** 2 + grad_y ** 2)
        psi += 0.1 * (1.0 / (1.0 + grad_mag) - psi)
        psi = np.clip(psi, 0.0, 1.0)
        stability = (psi > 0.6).astype(float)
        chi += 0.05 * stability
        chi -= 0.05 * (grad_mag > 1.5)
        chi = np.clip(chi, 0.0, 1.0)
        im_tau.set_data(tau)
        im_grad.set_data(grad_mag)
        im_psi.set_data(psi)
        im_chi.set_data(chi)
        if frame % 100 == 0:
            plt.savefig(f"frame_{frame}.png")
            frames_to_save.append(frame)
        if frame == steps - 1:
            plt.savefig("weather.png")
            stable_regions = np.argwhere(psi > 0.6)
            collapsing_regions = np.argwhere(chi < 0.2)
            summary = (
                f"Stable cells: {len(stable_regions)}\nCollapsing cells: {len(collapsing_regions)}"
            )
            print(summary)
            with open("weather_log.txt", "w") as f:
                f.write("Frames saved: " + ", ".join(map(str, frames_to_save)) + "\n")
                f.write(summary + "\n")
        return im_tau, im_grad, im_psi, im_chi

    ani = FuncAnimation(fig, update, frames=steps, interval=50, blit=True, repeat=False)
    plt.tight_layout()
    return fig, ani


def run(headless: bool = True):
    fig, ani = create_animation()
    if headless:
        ani.save("weather.mp4", writer="ffmpeg")
        if ani.event_source is not None:
            ani.event_source.stop()
        plt.close(fig)
    else:
        plt.show()


if __name__ == "__main__":
    run(headless=True)
