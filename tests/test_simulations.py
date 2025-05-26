import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import unittest
from matplotlib.figure import Figure
from matplotlib.animation import FuncAnimation

class TestCreateAnimation(unittest.TestCase):
    def _check_module(self, module_name):
        mod = __import__(module_name)
        if not hasattr(mod, "create_animation"):
            self.fail(f"{module_name}.create_animation does not exist")
        fig, anim = mod.create_animation()
        self.assertIsInstance(fig, Figure)
        self.assertIsInstance(anim, FuncAnimation)

    def test_simulation(self):
        self._check_module("simulation")

    def test_teleportation(self):
        self._check_module("teleportation")

    def test_weather_simulation(self):
        self._check_module("weather_simulation")

    def test_laser_filamentation(self):
        self._check_module("laser_filamentation")

if __name__ == "__main__":
    unittest.main()
