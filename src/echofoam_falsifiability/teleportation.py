import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


def ring_field(center, radius=10, thickness=2, size=100):
    y, x = np.ogrid[:size, :size]
    dist = np.sqrt((x - center[0]) ** 2 + (y - center[1]) ** 2)
    return np.exp(-((dist - radius) / thickness) ** 2)


def create_animation():
    size = 100
    steps = 150

    start_center = np.array([30.0, 50.0])
    psi_center = start_center.copy()
    psi = ring_field(psi_center, size=size)

    tau = np.zeros((size, size))
    chi = np.zeros((size, size))

    target_center = np.array([70.0, 50.0])
    teleport_start = 30
    teleport_complete = None

    fig, axes = plt.subplots(2, 2, figsize=(8, 8))
    im_tau = axes[0, 0].imshow(tau, cmap="plasma", vmin=-1, vmax=1, animated=True)
    axes[0, 0].set_title("tau")

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

    step_size = 0.4

    def update(frame):
        nonlocal psi_center, psi, tau, chi, grad_x, grad_y, grad_mag, teleport_complete

        if frame == teleport_start:
            tau -= ring_field(target_center, size=size)

        grad_x, grad_y = np.gradient(tau)
        grad_mag = np.sqrt(grad_x**2 + grad_y**2)

        g = np.array([
            grad_x[int(psi_center[1]) % size, int(psi_center[0]) % size],
            grad_y[int(psi_center[1]) % size, int(psi_center[0]) % size],
        ])
        psi_center -= step_size * g
        psi = ring_field(psi_center, size=size)

        chi[:] = np.sin(frame / 5.0) * psi

        if teleport_complete is None:
            dist = np.linalg.norm(psi_center - target_center)
            if dist < 1.0:
                teleport_complete = frame
                tau[:] = 0

        im_tau.set_data(tau)
        im_grad.set_data(grad_mag)
        im_psi.set_data(psi)
        im_chi.set_data(chi)

        return im_tau, im_grad, im_psi, im_chi

    anim = FuncAnimation(fig, update, frames=steps, interval=50, blit=True, repeat=False)
    plt.tight_layout()
    return fig, anim


if __name__ == "__main__":
    fig, _ = create_animation()
    plt.show()
