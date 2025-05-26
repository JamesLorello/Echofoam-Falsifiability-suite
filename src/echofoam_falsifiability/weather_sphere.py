import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401


def run(
    radius=1.0,
    theta_extent=np.pi / 2,
    phi_extent=2 * np.pi,
    bump=0.05,
    steps=100,
    grid_r=10,
    grid_theta=32,
    grid_phi=64,
    show=False,
):
    """Run a simple 3D spherical weather simulation.

    Parameters
    ----------
    radius : float
        Base sphere radius.
    theta_extent : float
        Polar angle extent in radians.
    phi_extent : float
        Azimuthal angle extent in radians.
    bump : float
        Amplitude of terrain bumpiness.
    steps : int
        Number of simulation steps.
    grid_r : int
        Radial grid points for the atmospheric shell.
    grid_theta : int
        Number of polar samples.
    grid_phi : int
        Number of azimuthal samples.
    show : bool, optional
        If True, display a live matplotlib plot updating every ten steps.
    """
    r = np.linspace(0.05, 0.2, grid_r)
    theta = np.linspace(0.0, theta_extent, grid_theta)
    phi = np.linspace(0.0, phi_extent, grid_phi)

    R, Theta, Phi = np.meshgrid(r, theta, phi, indexing="ij")
    terrain = radius + bump * np.sin(4 * Theta) * np.sin(4 * Phi)
    Rabs = terrain + R

    shape = R.shape
    tau = np.random.randn(*shape) * 0.1
    psi = np.zeros(shape)
    chi = np.zeros(shape)

    fig = None
    ax = None
    if show:
        plt.ion()
        fig = plt.figure()
        ax = fig.add_subplot(111, projection="3d")

    for i in range(steps):
        tau += 0.05 * np.random.randn(*shape)
        tau *= 0.99

        grad_r, grad_t, grad_p = np.gradient(tau)
        grad_mag = np.sqrt(grad_r ** 2 + grad_t ** 2 + grad_p ** 2)

        psi += 0.05 * (1.0 / (1.0 + grad_mag) - psi)
        psi = np.clip(psi, 0.0, 1.0)

        chi += 0.05 * (psi - chi) - 0.02 * grad_mag
        chi = np.clip(chi, 0.0, 1.0)

        if show and i % 10 == 0:
            mid = shape[0] // 2
            layer_tau = tau[mid]
            layer_R = Rabs[mid]

            X = layer_R * np.sin(Theta[mid]) * np.cos(Phi[mid])
            Y = layer_R * np.sin(Theta[mid]) * np.sin(Phi[mid])
            Z = layer_R * np.cos(Theta[mid])

            ax.clear()
            norm = (layer_tau - layer_tau.min()) / (layer_tau.ptp() + 1e-6)
            ax.plot_surface(
                X,
                Y,
                Z,
                facecolors=plt.cm.coolwarm(norm),
                rstride=1,
                cstride=1,
                linewidth=0,
                antialiased=False,
                shade=False,
            )
            ax.set_title(f"Tau field shell slice step {i}")
            plt.draw()
            plt.pause(0.001)

    mid = shape[0] // 2
    layer_tau = tau[mid]
    layer_R = Rabs[mid]

    X = layer_R * np.sin(Theta[mid]) * np.cos(Phi[mid])
    Y = layer_R * np.sin(Theta[mid]) * np.sin(Phi[mid])
    Z = layer_R * np.cos(Theta[mid])

    if fig is None:
        fig = plt.figure()
        ax = fig.add_subplot(111, projection="3d")
    norm = (layer_tau - layer_tau.min()) / (layer_tau.ptp() + 1e-6)
    ax.plot_surface(
        X,
        Y,
        Z,
        facecolors=plt.cm.coolwarm(norm),
        rstride=1,
        cstride=1,
        linewidth=0,
        antialiased=False,
        shade=False,
    )
    ax.set_title("Tau field shell slice")
    plt.tight_layout()
    plt.savefig("weather_sphere.png")
    if show:
        plt.show(block=False)
        plt.pause(0.1)
    plt.close(fig)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="3D spherical weather simulation")
    parser.add_argument("--radius", type=float, default=1.0, help="Base sphere radius")
    parser.add_argument(
        "--theta",
        type=float,
        default=np.pi / 2,
        help="Polar angle extent (radians)",
    )
    parser.add_argument(
        "--phi",
        type=float,
        default=2 * np.pi,
        help="Azimuthal angle extent (radians)",
    )
    parser.add_argument(
        "--bump", type=float, default=0.05, help="Terrain bump amplitude"
    )
    parser.add_argument("--steps", type=int, default=100, help="Simulation steps")
    parser.add_argument(
        "--show",
        action="store_true",
        help="Display real-time visualization",
    )
    args = parser.parse_args()

    run(
        radius=args.radius,
        theta_extent=args.theta,
        phi_extent=args.phi,
        bump=args.bump,
        steps=args.steps,
        show=args.show,
    )
