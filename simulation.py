import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


def main():
    size = 50
    tau = np.zeros((size, size))
    tau[size // 2, size // 2] = 1.0

    fig, axes = plt.subplots(2, 2, figsize=(8, 8))
    ax_tau, ax_grad, ax_psi, ax_chi = axes.flatten()
    im_tau = ax_tau.imshow(tau, cmap='viridis', vmin=-1, vmax=1)
    ax_tau.set_title('τ')
    im_grad = ax_grad.imshow(np.zeros_like(tau), cmap='magma', vmin=0, vmax=1)
    ax_grad.set_title('∇τ')
    im_psi = ax_psi.imshow(np.zeros_like(tau), cmap='coolwarm', vmin=-1, vmax=1)
    ax_psi.set_title('ψ')
    im_chi = ax_chi.imshow(np.zeros_like(tau), cmap='coolwarm', vmin=-1, vmax=1)
    ax_chi.set_title('χ')

    ims = [im_tau, im_grad, im_psi, im_chi]

    def step(frame):
        nonlocal tau
        # simple diffusion process
        tau = tau + 0.1 * (
            np.roll(tau, 1, axis=0) + np.roll(tau, -1, axis=0) +
            np.roll(tau, 1, axis=1) + np.roll(tau, -1, axis=1) - 4 * tau
        )
        grad_x, grad_y = np.gradient(tau)
        grad_tau = np.sqrt(grad_x**2 + grad_y**2)
        psi = np.sin(tau)
        chi = np.cos(tau)

        im_tau.set_array(tau)
        im_grad.set_array(grad_tau)
        im_psi.set_array(psi)
        im_chi.set_array(chi)

        if frame % 100 == 0:
            plt.savefig(f'frame_{frame:04d}.png')
        return ims

    ani = FuncAnimation(fig, step, frames=500, interval=50, blit=False)
    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    main()
