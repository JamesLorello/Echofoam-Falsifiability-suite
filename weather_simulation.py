from echofoam_falsifiability.weather_simulation import create_animation as _create_animation


def create_animation():
    return _create_animation()


if __name__ == "__main__":
    import matplotlib.pyplot as plt
    fig, anim = create_animation()
    plt.show()
