import numpy as np


def simulate(
    model,
    controller,
    T0=15.0,
    T_set=22.0,
    sim_time=240.0,
):
    dt = model.params.dt
    n_steps = int(sim_time / dt)

    time = np.arange(n_steps + 1) * dt
    T = np.zeros(n_steps + 1)
    u = np.zeros(n_steps)

    T[0] = T0
    controller.reset()

    for k in range(n_steps):
        u[k] = controller.compute(
            T[k],
            T_set
        )

        T[k + 1] = model.step(
            T[k],
            u[k]
        )

    return time, T, u


def simulate_reference_profile(
    model,
    controller,
    T0,
    reference,
):
    """
    Simulate the closed-loop system with a time-varying
    temperature reference.
    """

    import numpy as np

    reference = np.asarray(reference, dtype=float)

    n_steps = len(reference) - 1
    dt = model.params.dt

    time = np.arange(n_steps + 1) * dt

    T = np.zeros(n_steps + 1)
    u = np.zeros(n_steps)

    T[0] = T0
    controller.reset()

    for k in range(n_steps):

        T_set_k = reference[k]

        u[k] = controller.compute(
            T[k],
            T_set_k
        )

        T[k + 1] = model.step(
            T[k],
            u[k]
        )

    return time, T, u


def simulate_disturbance_profile(
    model,
    controller,
    T0,
    T_set,
    T_out_profile,
):
    """
    Simulate the closed-loop HVAC system with a
    time-varying outdoor-temperature disturbance.

    Parameters
    ----------
    model : HVACModel
        HVAC thermal model.

    controller :
        PI or MPC controller.

    T0 : float
        Initial indoor temperature.

    T_set : float
        Constant indoor-temperature reference.

    T_out_profile : array-like
        Outdoor-temperature profile. Length N+1.

    Returns
    -------
    time : ndarray
        Simulation time vector.

    T : ndarray
        Indoor-temperature response.

    u : ndarray
        Control signal.
    """

    import numpy as np

    T_out_profile = np.asarray(
        T_out_profile,
        dtype=float
    )

    n_steps = len(T_out_profile) - 1
    dt = model.params.dt

    time = np.arange(n_steps + 1) * dt

    T = np.zeros(n_steps + 1)
    u = np.zeros(n_steps)

    T[0] = T0

    controller.reset()

    # Store original outdoor temperature
    original_T_out = model.params.T_out

    try:

        for k in range(n_steps):

            # Apply outdoor-temperature disturbance
            model.params.T_out = T_out_profile[k]

            u[k] = controller.compute(
                T[k],
                T_set
            )

            T[k + 1] = model.step(
                T[k],
                u[k]
            )

    finally:

        # Restore original model parameter
        model.params.T_out = original_T_out

    return time, T, u


def simulate_model_mismatch(
    plant_model,
    controller,
    T0=15.0,
    T_set=22.0,
    sim_time=240.0,
):
    """
    Simulate a controller applied to a plant whose model
    may differ from the model used by the controller.

    Parameters
    ----------
    plant_model :
        Actual HVAC plant used for state propagation.

    controller :
        Controller. For MPC, the controller may contain
        a different nominal prediction model.

    T0 : float
        Initial indoor temperature.

    T_set : float
        Temperature reference.

    sim_time : float
        Simulation duration [min].

    Returns
    -------
    time, T, u
    """

    import numpy as np

    dt = plant_model.params.dt
    n_steps = int(sim_time / dt)

    time = np.arange(n_steps + 1) * dt

    T = np.zeros(n_steps + 1)
    u = np.zeros(n_steps)

    T[0] = T0

    controller.reset()

    for k in range(n_steps):

        # Controller sees the measured plant temperature
        u[k] = controller.compute(
            T[k],
            T_set
        )

        # Actual state evolution is determined by the plant,
        # not by the controller's internal prediction model.
        T[k + 1] = plant_model.step(
            T[k],
            u[k]
        )

    return time, T, u
