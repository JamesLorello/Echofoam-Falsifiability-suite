"""Present-state sufficiency: illustrative deterministic controls, not physical validation."""

def step(x, v, dt=0.05, k=1.0):
    return x + dt*v, v - dt*k*x

def memory_step(x, v, h, dt=0.05):
    return x + dt*v, v - dt*(x + 0.5*h), h

def test_matched_complete_states():
    # Earlier states are overwritten by the same state preparation.
    a, b = (1.0, 0.0), (-2.0, 3.0)
    a = b = (0.7, -0.2)
    for _ in range(100):
        a, b = step(*a), step(*b)
    assert a == b

def test_incomplete_observation():
    a, b = (0.7, -0.2), (0.7, 0.4)
    assert step(*a) != step(*b)

def test_omitted_present_variable():
    a, b = (0.7, -0.2, 1.0), (0.7, -0.2, -1.0)
    assert memory_step(*a) != memory_step(*b)

if __name__ == "__main__":
    test_matched_complete_states()
    test_incomplete_observation()
    test_omitted_present_variable()
    print("Three illustrative controls passed; no new physics established.")
