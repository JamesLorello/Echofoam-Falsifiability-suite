import numpy as np
import matplotlib.pyplot as plt
import os


def run_simulation(grid_size=128, timesteps=400, save_interval=50,
                   alpha=0.01, beta=0.05, collapse_threshold=2.0,
                   intensity_threshold=0.1, realtime=False):
    """Run a simple 2D laser filamentation simulation."""
    x = np.linspace(-1, 1, grid_size)
    y = np.linspace(-1, 1, grid_size)
    X, Y = np.meshgrid(x, y)

    # Initial coherent Gaussian beam
    psi = np.exp(-(X**2 + Y**2) * 20).astype(np.complex128)
    tau = np.ones((grid_size, grid_size))
    chi_history = []

    os.makedirs("frames", exist_ok=True)

    if realtime:
        plt.ion()
        rt_fig, rt_axes = plt.subplots(1, 3, figsize=(12, 4))
        rt_im0 = rt_axes[0].imshow(np.abs(psi), origin="lower", cmap="viridis", vmin=0, vmax=1, animated=True)
        rt_axes[0].set_title(r"$|\psi|")
        rt_im1 = rt_axes[1].imshow(tau, origin="lower", cmap="plasma", vmin=1, vmax=collapse_threshold, animated=True)
        rt_axes[1].set_title(r"$\tau$")
        (rt_line,) = rt_axes[2].plot([], [])
        rt_axes[2].set_xlim(0, timesteps)
        rt_axes[2].set_ylim(0, 1)
        rt_axes[2].set_title(r"$\chi$")
        rt_fig.tight_layout()
        plt.show(block=False)

    for t in range(timesteps):
        # Propagate beam by shifting right
        psi = np.roll(psi, 1, axis=1)

        intensity = np.abs(psi) ** 2
        tau += alpha * intensity
        tau += beta * (intensity > intensity_threshold) * intensity**2

        # Collapse if refractive index becomes too high
        if np.any(tau > collapse_threshold):
            psi = (np.random.rand(grid_size, grid_size) + 1j * np.random.rand(grid_size, grid_size)) * 0.1
            tau[:] = 1.0
            chi = 0.0
        else:
            chi = np.abs(np.mean(psi)) / (np.mean(np.abs(psi)) + 1e-8)
        chi_history.append(chi)

        psi *= 0.999  # gradual decoherence

        if t % save_interval == 0:
            fig, axes = plt.subplots(1, 3, figsize=(12, 4))
            im0 = axes[0].imshow(np.abs(psi), origin="lower", cmap="viridis", vmin=0, vmax=1)
            axes[0].set_title(r"$|\psi|")
            fig.colorbar(im0, ax=axes[0])

            im1 = axes[1].imshow(tau, origin="lower", cmap="plasma", vmin=1, vmax=collapse_threshold)
            axes[1].set_title(r"$\tau$")
            fig.colorbar(im1, ax=axes[1])

            axes[2].plot(chi_history)
            axes[2].set_xlim(0, timesteps)
            axes[2].set_ylim(0, 1)
            axes[2].set_title(r"$\chi$")

            fig.tight_layout()
            fig.savefig(f"frames/frame_{t:04d}.png")
            plt.close(fig)

        if realtime:
            rt_im0.set_data(np.abs(psi))
            rt_im1.set_data(tau)
            rt_line.set_data(range(len(chi_history)), chi_history)
            plt.pause(0.001)

    if realtime:
        plt.ioff()
        plt.show()


if __name__ == "__main__":
    run_simulation(realtime=True)
