import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, FFMpegWriter

# Simulation parameters
size = 50
steps = 150

# 3D fields
np.random.seed(0)
tau = np.random.randn(size, size, size) * 0.1
psi = np.zeros((size, size, size))
chi = np.zeros((size, size, size))
chi_prev = np.zeros_like(chi)

# Falsifiability tracking
coherence_threshold = 0.8
coherence_fraction = 0.6
coherence_frames_required = 50
consecutive_coherent = 0
verdict = None
verdict_step = None

# Visualization setup (show central slice)
mid = size // 2
fig, axes = plt.subplots(2, 2, figsize=(8, 8))
im_tau = axes[0, 0].imshow(tau[:, :, mid], cmap='plasma', animated=True)
axes[0, 0].set_title('tau')

grad = np.gradient(tau)
grad_mag = np.sqrt(sum(g**2 for g in grad))
im_grad = axes[0, 1].imshow(grad_mag[:, :, mid], cmap='cividis', animated=True)
axes[0, 1].set_title('∇tau')

im_psi = axes[1, 0].imshow(psi[:, :, mid], cmap='viridis', animated=True)
axes[1, 0].set_title('psi')
im_chi = axes[1, 1].imshow(chi[:, :, mid], cmap='inferno', animated=True)
axes[1, 1].set_title('chi')

for row in axes:
    for ax in row:
        ax.set_xticks([])
        ax.set_yticks([])

def laplacian_3d(field):
    return (
        np.roll(field, 1, axis=0) + np.roll(field, -1, axis=0) +
        np.roll(field, 1, axis=1) + np.roll(field, -1, axis=1) +
        np.roll(field, 1, axis=2) + np.roll(field, -1, axis=2) -
        6 * field
    )

def update(frame):
    global tau, psi, chi, chi_prev, grad_mag
    global consecutive_coherent, verdict, verdict_step

    # random tension updates with damping
    tau += 0.1 * np.random.randn(size, size, size)
    tau *= 0.995

    # gradient and magnitude
    grad = np.gradient(tau)
    grad_mag = np.sqrt(sum(g**2 for g in grad))

    # psi flows toward regions of low gradient magnitude
    psi += 0.1 * (1.0 / (1.0 + grad_mag) - psi)

    # propagate chi wave
    lap = laplacian_3d(chi)
    chi_new = 2 * chi - chi_prev + 0.2 * psi * lap
    chi_prev = chi
    chi = chi_new

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

    # update visuals
    im_tau.set_data(tau[:, :, mid])
    im_grad.set_data(grad_mag[:, :, mid])
    im_psi.set_data(psi[:, :, mid])
    im_chi.set_data(chi[:, :, mid])

    if frame == steps - 1:
        plt.savefig('final_frame_3d.png')

    return im_tau, im_grad, im_psi, im_chi

ani = FuncAnimation(fig, update, frames=steps, interval=50, blit=True, repeat=False)
plt.tight_layout()
plt.show()  # show animation in real time

writer = FFMpegWriter(fps=20)
ani.save('simulation_3d.mp4', writer=writer)

if verdict is None:
    verdict = 'Hypothesis failed'
    verdict_step = steps - 1

with open('epcd_results_3d.txt', 'w') as f:
    f.write(verdict + '\n')

print(verdict)
plt.close(fig)
