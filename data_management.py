import json
import numpy as np

class DataManager:
    """Collect simulation metrics and persist them to disk."""

    def __init__(self, metrics_path="metrics.json", arrays_path="fields_final.npz"):
        self.metrics_path = metrics_path
        self.arrays_path = arrays_path
        self.metrics = []

    def log_step(self, step: int, tau: np.ndarray, psi: np.ndarray, chi: np.ndarray, grad_mag: np.ndarray) -> None:
        """Record step metrics for later analysis."""
        self.metrics.append({
            "step": step,
            "tau_mean": float(np.mean(tau)),
            "tau_std": float(np.std(tau)),
            "grad_mean": float(np.mean(grad_mag)),
            "grad_max": float(np.max(grad_mag)),
            "psi_mean": float(np.mean(psi)),
            "chi_mean": float(np.mean(chi)),
        })

    def save(self, tau: np.ndarray, psi: np.ndarray, chi: np.ndarray) -> None:
        with open(self.metrics_path, "w") as f:
            json.dump(self.metrics, f, indent=2)
        np.savez_compressed(self.arrays_path, tau=tau, psi=psi, chi=chi)
