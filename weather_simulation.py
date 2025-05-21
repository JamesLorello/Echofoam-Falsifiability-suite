import numpy as np
import matplotlib.pyplot as plt

# Simulation parameters
size = 50
steps = 200

# Fields
# tau: temperature-pressure memory field
np.random.seed(0)
tau = np.random.randn(size, size) * 0.5
# psi: coherent weather structures
psi = np.zeros((size, size))
# chi: reinforcement tracker
chi = np.zeros((size, size))

# for visualization
fig, axes = plt.subplots(2, 2, figsize=(8, 8))
im_tau = axes[0, 0].imshow(tau, cmap='coolwarm', vmin=-2, vmax=2)
axes[0, 0].set_title('tau')

# initial gradient
grad_x, grad_y = np.gradient(tau)
grad_mag = np.sqrt(grad_x**2 + grad_y**2)
im_grad = axes[0, 1].imshow(grad_mag, cmap='viridis')
axes[0, 1].set_title('∇tau')

im_psi = axes[1, 0].imshow(psi, cmap='plasma', vmin=0, vmax=1)
axes[1, 0].set_title('psi')

im_chi = axes[1, 1].imshow(chi, cmap='inferno', vmin=0, vmax=1)
axes[1, 1].set_title('chi')

for ax_row in axes:
    for ax in ax_row:
        ax.set_xticks([])
        ax.set_yticks([])

frames_to_save = []

for step in range(steps):
    # random fluctuation with slight decay
    tau += 0.05 * np.random.randn(size, size)
    tau *= 0.99

    # external influence at step 50: heat pulse at center
    if step == 50:
        pulse = np.zeros_like(tau)
        cx = cy = size // 2
        pulse[cx-2:cx+3, cy-2:cy+3] = 5.0
        tau += pulse

    # gradient
    grad_x, grad_y = np.gradient(tau)
    grad_mag = np.sqrt(grad_x**2 + grad_y**2)

    # psi evolves toward regions of low gradient
    psi += 0.1 * (1.0 / (1.0 + grad_mag) - psi)
    psi = np.clip(psi, 0.0, 1.0)

    # chi reinforcement: increase where psi stable, decrease with high grad
    stability = (psi > 0.6).astype(float)
    chi += 0.05 * stability
    chi -= 0.05 * (grad_mag > 1.5)
    chi = np.clip(chi, 0.0, 1.0)

    # update images
    im_tau.set_data(tau)
    im_grad.set_data(grad_mag)
    im_psi.set_data(psi)
    im_chi.set_data(chi)

    # save every 100th frame
    if step % 100 == 0:
        plt.savefig(f'frame_{step}.png')
        frames_to_save.append(step)

# save final visualization
plt.tight_layout()
plt.savefig('weather.png')

# prediction summary
stable_regions = np.argwhere(psi > 0.6)
collapsing_regions = np.argwhere(chi < 0.2)
summary = f"Stable cells: {len(stable_regions)}\nCollapsing cells: {len(collapsing_regions)}"
print(summary)

with open('weather_log.txt', 'w') as f:
    f.write('Frames saved: ' + ', '.join(map(str, frames_to_save)) + '\n')
    f.write(summary + '\n')
