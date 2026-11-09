"""Distributed-record correction toy model. Requires numpy. No physical claim."""
import numpy as np

def graph(n, kind):
    W = np.zeros((n, n))
    if kind == "ring":
        for i in range(n):
            W[i, (i+1)%n] = W[(i+1)%n, i] = 1
    elif kind == "hub":
        for i in range(1, n):
            W[0, i] = W[i, 0] = 1
    elif kind == "complete":
        W[:] = 1
        np.fill_diagonal(W, 0)
    elif kind == "modules":
        for i in range(n):
            for j in range(i+1, n):
                if i//(n//2) == j//(n//2):
                    W[i, j] = W[j, i] = 1
        W[n//2-1, n//2] = W[n//2, n//2-1] = 1
    else:
        raise ValueError(kind)
    return W

def run(n, kind, seed, correction_node, steps=80):
    rng = np.random.default_rng(seed)
    W = graph(n, kind)
    x0 = rng.normal(0.7, 0.35, n)  # true scalar event = 0; shared systematic bias
    def evolve(correction):
        x = x0.copy()
        for _ in range(steps):
            degree = W.sum(axis=1)
            neighbor = np.divide(W @ x, degree, out=np.zeros(n), where=degree>0)
            update = 0.18 * (neighbor - x)
            if correction:
                update[correction_node] += 0.35 * (0 - x[correction_node])
            x = x + update
        return x
    baseline, corrected = evolve(False), evolve(True)
    delta = corrected - baseline
    return {
        "fidelity_gain": np.mean(baseline**2) - np.mean(corrected**2),
        "total_cost": np.sum(delta**2),
        "max_cost": np.max(delta**2),
        "reach": np.sum(np.abs(delta) > 0.05),
        "final_error": np.mean(corrected**2),
    }

def test_controls():
    assert np.array_equal(graph(12, "ring"), graph(12, "ring"))
    assert np.all(np.isfinite(list(run(12, "ring", 42, 0).values())))
    assert run(12, "hub", 42, 0) == run(12, "hub", 42, 0)

if __name__ == "__main__":
    test_controls()
    n, N = 12, 400
    print("Topology | MSE improvement | squared reorganization | max squared change | reach")
    for kind in ["ring", "hub", "complete", "modules"]:
        results = [run(n, kind, seed, 0) for seed in range(N)]
        print(kind, *(round(float(np.mean([r[k] for r in results])), 4)
                       for k in ["fidelity_gain", "total_cost", "max_cost", "reach"]))
    print("Hub center versus peripheral correction:")
    for node in [0, 1]:
        results = [run(n, "hub", seed, node) for seed in range(N)]
        print(node, *(round(float(np.mean([r[k] for r in results])), 4)
                      for k in ["fidelity_gain", "total_cost", "max_cost"]))
