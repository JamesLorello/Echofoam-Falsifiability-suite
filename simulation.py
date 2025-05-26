from echofoam_falsifiability.simulation import create_animation as _create_animation
import matplotlib.pyplot as plt


def create_animation(frames: int = 20):
    """Re-exported create_animation from the package."""
    return _create_animation(frames)


def main():
    fig, anim = create_animation()
    plt.show()


if __name__ == "__main__":
    main()
