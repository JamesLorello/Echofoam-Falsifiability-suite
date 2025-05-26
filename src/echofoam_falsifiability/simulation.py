import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, FFMpegWriter

# Simulation parameters
size = 100
steps = 200

# Global state used during the animation
_tau = None
_psi = None
_chi = None
_chi_prev = None
_grad_mag = None
_consecutive_coherent = 0
_verdict = None
_verdict_step = None


def _init_fields():
    """Initialize the simulation fields and globals."""
    global _tau, _psi, _chi, _chi_prev, _grad_mag
    global _consecutive_coherent, _verdict, _verdict_step

    _tau = np.random.randn(size, size) * 0.1
    _psi = np.zeros((size, size))
    _chi = np.zeros((size, size))
    _chi_prev = np.zeros_like(_chi)
    _grad_mag = np.zeros_like(_tau)
    _consecutive_coherent = 0
    _verdict = None
    _verdict_step = None


def create_animation():
    """Construct the figure and animation for the simulation."""
    _init_fields()

    fig, axes = plt.subplots(2, 2, figsize=(8, 8))
    im_tau = axes[0, 0].imshow(_tau, cmap="plasma", animated=True)
    axes[0, 0].set_title("tau")

    grad_x, grad_y = np.gradient(_tau)
    global _grad_mag
    _grad_mag = np.sqrt(grad_x**2 + grad_y**2)
    im_grad = axes[0, 1].imshow(_grad_mag, cmap="cividis", animated=True)
    axes[0, 1].set_title("∇tau")

    im_psi = axes[1, 0].imshow(_psi, cmap="viridis", animated=True)
    axes[1, 0].set_title("psi")

    im_chi = axes[1, 1].imshow(_chi, cmap="inferno", animated=True)
    axes[1, 1].set_title("chi")

    for row in axes:
        for ax in row:
            ax.set_xticks([])
            ax.set_yticks([])

    def update(frame):
        global _tau, _psi, _chi, _chi_prev, _grad_mag
        global _consecutive_coherent, _verdict, _verdict_step

        _tau += 0.1 * np.random.randn(size, size)
        _tau *= 0.995

        grad_x, grad_y = np.gradient(_tau)
        _grad_mag = np.sqrt(grad_x**2 + grad_y**2)

        _psi += 0.1 * (1.0 / (1.0 + _grad_mag) - _psi)

        laplacian = (
            np.roll(_chi, 1, axis=0) + np.roll(_chi, -1, axis=0)
            + np.roll(_chi, 1, axis=1) + np.roll(_chi, -1, axis=1)
            - 4 * _chi
        )
        chi_new = 2 * _chi - _chi_prev + 0.2 * _psi * laplacian
        _chi_prev = _chi
        _chi = chi_new

        if _verdict is None:
            frac = np.mean(_psi > 0.8)
            if frac >= 0.6:
                _consecutive_coherent += 1
                if _consecutive_coherent >= 100:
                    _verdict = "Hypothesis sustained"
                    _verdict_step = frame
                    print(f"Coherence stabilized at step {frame}")
            else:
                if _consecutive_coherent > 0:
                    _verdict = "Hypothesis failed"
                    _verdict_step = frame
                    print(f"Coherence lost at step {frame}")
                _consecutive_coherent = 0

        im_tau.set_data(_tau)
        im_grad.set_data(_grad_mag)
        im_psi.set_data(_psi)
        im_chi.set_data(_chi)

        if frame == steps - 1:
            plt.savefig("final_frame.png")
        return im_tau, im_grad, im_psi, im_chi

    anim = FuncAnimation(fig, update, frames=steps, interval=50, blit=True, repeat=False)
    plt.tight_layout()
    return fig, anim


def main():
    fig, anim = create_animation()
    writer = FFMpegWriter(fps=20)
    anim.save("simulation.mp4", writer=writer)

    global _verdict, _verdict_step
    if _verdict is None:
        _verdict = "Hypothesis failed"
        _verdict_step = steps - 1

    with open("epcd_results.txt", "w") as f:
        f.write(_verdict + "\n")

    print(_verdict)
    plt.close(fig)


if __name__ == "__main__":
    main()
