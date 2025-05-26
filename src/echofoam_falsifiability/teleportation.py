import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

def main():
    # Grid size and simulation steps
    size = 100
    steps = 150

    # Ring generation helper
    def ring_field(center, radius=10, thickness=2):
        y, x = np.ogrid[:size, :size]
        dist = np.sqrt((x - center[0])**2 + (y - center[1])**2)
        return np.exp(-((dist - radius) / thickness)**2)

    # Initial psi blob at start location
    start_center = np.array([30.0, 50.0])
    psi_center = start_center.copy()
    psi = ring_field(psi_center)

    # Tau and chi fields
    tau = np.zeros((size, size))
    chi = np.zeros((size, size))

    # Teleportation target
    target_center = np.array([70.0, 50.0])
    teleport_start = 30
    teleport_complete = None

    # Visualization setup (tau, grad, psi, chi)
    fig, axes = plt.subplots(2, 2, figsize=(8, 8))
    im_tau = axes[0, 0].imshow(tau, cmap="plasma", vmin=-1, vmax=1, animated=True)
    axes[0, 0].set_title("tau")

    # placeholder gradient
    grad_x, grad_y = np.gradient(tau)
    grad_mag = np.sqrt(grad_x**2 + grad_y**2)
    im_grad = axes[0, 1].imshow(grad_mag, cmap="cividis", animated=True)
    axes[0, 1].set_title("∇tau")

    im_psi = axes[1, 0].imshow(psi, cmap="viridis", animated=True)
    axes[1, 0].set_title("psi")

    im_chi = axes[1, 1].imshow(chi, cmap="inferno", animated=True)
    axes[1, 1].set_title("chi")

    for row in axes:
        for ax in row:
            ax.set_xticks([])
            ax.set_yticks([])

    step_size = 0.4  # movement sensitivity

    def update(frame):
        nonlocal psi_center, psi, tau, chi, grad_x, grad_y, grad_mag, teleport_complete

        # Introduce negative shape at teleport_start
        if frame == teleport_start:
            tau -= ring_field(target_center)

        # Gradient of tau
        grad_x, grad_y = np.gradient(tau)
        grad_mag = np.sqrt(grad_x**2 + grad_y**2)

        # Move psi center according to gradient at its current location
        g = np.array([
            grad_x[int(psi_center[1]) % size, int(psi_center[0]) % size],
            grad_y[int(psi_center[1]) % size, int(psi_center[0]) % size],
        ])
        psi_center -= step_size * g
        psi = ring_field(psi_center)

        # Simple chi wave tied to psi
        chi[:] = np.sin(frame / 5.0) * psi

        # Check teleport completion
        if teleport_complete is None:
            dist = np.linalg.norm(psi_center - target_center)
            if dist < 1.0:
                teleport_complete = frame
                print(
                    f"Teleportation completed at frame {frame} at {tuple(target_center.astype(int))}"
                )
                tau[:] = 0  # erase original

        im_tau.set_data(tau)
        im_grad.set_data(grad_mag)
        im_psi.set_data(psi)
        im_chi.set_data(chi)

        if frame == steps - 1:
            plt.savefig("teleport.png")

        return im_tau, im_grad, im_psi, im_chi

    ani = FuncAnimation(fig, update, frames=steps, interval=50, blit=True, repeat=False)
    plt.tight_layout()
    ani.save("teleport.mp4", writer="ffmpeg")
    plt.close(fig)


if __name__ == "__main__":
    main()
