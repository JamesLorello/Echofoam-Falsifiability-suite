import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, FFMpegWriter, writers

# Simulation parameters
size = 100
steps = 200

# Fields
tau = np.random.randn(size, size) * 0.1  # initial tension field
psi = np.zeros((size, size))             # coherence field
chi = np.zeros((size, size))             # wave field
chi_prev = np.zeros_like(chi)

# Falsifiability parameters
coherence_threshold = 0.8
coherence_fraction = 0.6
coherence_frames_required = 100
consecutive_coherent = 0
verdict = None
verdict_step = None

# Visualization setup for 2x2 grid
fig, axes = plt.subplots(2, 2, figsize=(8, 8))
im_tau = axes[0, 0].imshow(tau, cmap='plasma', animated=True)
axes[0, 0].set_title('tau')

grad_x, grad_y = np.gradient(tau)
grad_mag = np.sqrt(grad_x**2 + grad_y**2)
im_grad = axes[0, 1].imshow(grad_mag, cmap='cividis', animated=True)
axes[0, 1].set_title('∇tau')

im_psi = axes[1, 0].imshow(psi, cmap='viridis', animated=True)
axes[1, 0].set_title('psi')
im_chi = axes[1, 1].imshow(chi, cmap='inferno', animated=True)
axes[1, 1].set_title('chi')

for row in axes:
    for ax in row:
        ax.set_xticks([])
        ax.set_yticks([])


def update(frame):
    global tau, psi, chi, chi_prev, grad_mag
    global consecutive_coherent, verdict, verdict_step
    # small random tension updates with damping
    tau += 0.1 * np.random.randn(size, size)
    tau *= 0.995

    # gradient of tau
    grad_x, grad_y = np.gradient(tau)
    grad_mag = np.sqrt(grad_x**2 + grad_y**2)

    # psi flows toward regions of low gradient magnitude
    psi += 0.1 * (1.0 / (1.0 + grad_mag) - psi)

    # propagate chi wave influenced by psi (simple discrete wave eq.)
    laplacian = (
        np.roll(chi, 1, axis=0) + np.roll(chi, -1, axis=0) +
        np.roll(chi, 1, axis=1) + np.roll(chi, -1, axis=1) - 4 * chi
    )
    chi_new = 2 * chi - chi_prev + 0.2 * psi * laplacian
    chi_prev = chi
    chi = chi_new

    # falsifiability tracking
    if verdict is None:
        frac = np.mean(psi > coherence_threshold)
        if frac >= coherence_fraction:
            consecutive_coherent += 1
            if consecutive_coherent >= coherence_frames_required:
                verdict = "Hypothesis sustained"
                verdict_step = frame
                print(f"Coherence stabilized at step {frame}")
        else:
            if consecutive_coherent > 0:
                verdict = "Hypothesis failed"
                verdict_step = frame
                print(f"Coherence lost at step {frame}")
            consecutive_coherent = 0

    im_tau.set_data(tau)
    im_grad.set_data(grad_mag)
    im_psi.set_data(psi)
    im_chi.set_data(chi)

    # save final frame
    if frame == steps - 1:
        plt.savefig("final_frame.png")

    return im_tau, im_grad, im_psi, im_chi

ani = FuncAnimation(fig, update, frames=steps, interval=50, blit=True, repeat=False)
plt.tight_layout()

if "ffmpeg" in writers.avail:
    writer = FFMpegWriter(fps=20)
    ani.save("simulation.mp4", writer=writer)
else:
    print("ffmpeg not available; skipping video output")

if verdict is None:
    verdict = "Hypothesis failed"
    verdict_step = steps - 1

with open("epcd_results.txt", "w") as f:
    f.write(verdict + "\n")

print(verdict)
plt.close(fig)

