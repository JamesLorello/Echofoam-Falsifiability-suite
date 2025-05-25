import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, FFMpegWriter

log_file = open("echofoam_cosmo_log.txt", "w")

# Simulation parameters
size = 100
steps = 200

# Fields
x = np.linspace(-1, 1, size)
X, Y = np.meshgrid(x, x)
r2 = X**2 + Y**2
tau = np.exp(-r2 * 25)  # Gaussian overdensity at center
psi = np.zeros((size, size))
psi_prev = np.zeros_like(psi)
psi[size // 2, size // 2] = 1.0  # initial pulse at center
chi = np.zeros((size, size))
chi_prev = np.zeros_like(chi)
tau_prev = tau.copy()
standing_counter = 0
annotated = False

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
    global tau, psi, psi_prev, chi, chi_prev, grad_mag, tau_prev
    global consecutive_coherent, verdict, verdict_step
    global standing_counter, annotated, log_file
    # small random tension updates with damping
    tau += 0.1 * np.random.randn(size, size)
    tau *= 0.995

    # detect symmetry break
    delta_tau = np.mean(np.abs(tau - tau_prev))
    if delta_tau > 0.3:
        log_file.write(f"Symmetry break at frame {frame}\n")
    tau_prev[:] = tau

    # inject small negative perturbation at frame 50
    if frame == 50:
        perturb = np.exp(-r2 * 50) * -0.5
        tau += perturb

    # gradient of tau
    grad_x, grad_y = np.gradient(tau)
    grad_mag = np.sqrt(grad_x**2 + grad_y**2)

    # propagate psi outward using a wave equation with speed depending on grad_mag
    lap_psi = (
        np.roll(psi, 1, axis=0) + np.roll(psi, -1, axis=0) +
        np.roll(psi, 1, axis=1) + np.roll(psi, -1, axis=1) - 4 * psi
    )
    speed = 0.5 / (1.0 + grad_mag)
    psi_new = 2 * psi - psi_prev + speed * lap_psi
    psi_prev[:] = psi
    psi[:] = psi_new

    # propagate chi wave influenced by psi (simple discrete wave eq.)
    laplacian = (
        np.roll(chi, 1, axis=0) + np.roll(chi, -1, axis=0) +
        np.roll(chi, 1, axis=1) + np.roll(chi, -1, axis=1) - 4 * chi
    )
    chi_new = 2 * chi - chi_prev + 0.2 * psi * laplacian
    diff_chi = np.mean(np.abs(chi_new - chi))
    chi_prev = chi
    chi = chi_new

    if diff_chi < 1e-3:
        standing_counter += 1
    else:
        standing_counter = 0

    if standing_counter > 5 and not annotated:
        axes[1, 1].annotate(
            "ψ|τ Higgs candidate",
            xy=(size // 2, size // 2),
            xycoords='data',
            color='white',
            ha='center'
        )
        annotated = True

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

writer = FFMpegWriter(fps=20)
ani.save("simulation.mp4", writer=writer)

if verdict is None:
    verdict = "Hypothesis failed"
    verdict_step = steps - 1

with open("epcd_results.txt", "w") as f:
    f.write(verdict + "\n")

print(verdict)
plt.close(fig)
log_file.close()

