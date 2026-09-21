import numpy as np


def calculate_metrics(
    time,
    temperature,
    control,
    setpoint,
    u_min=0.0,
    u_max=1.0,
    settling_band=0.02,
    rise_lower=0.10,
    rise_upper=0.90,
    saturation_tol=1e-9,
):
    """
    Calculate performance metrics for one closed-loop simulation.

    Parameters
    ----------
    time : array-like
        Simulation time.
    temperature : array-like
        Temperature response T[k].
    control : array-like
        Control signal u[k].
    setpoint : float
        Constant reference temperature.
    u_min, u_max : float
        Actuator limits.
    settling_band : float
        Relative settling band around the setpoint.
        Default = 0.02 -> +/-2%.
    rise_lower, rise_upper : float
        Fractions used for rise-time calculation.
        Default = 10% to 90% of the commanded temperature change.
    saturation_tol : float
        Numerical tolerance for detecting actuator saturation.

    Returns
    -------
    dict
        Dictionary containing all performance metrics.
    """

    time = np.asarray(time, dtype=float)
    T = np.asarray(temperature, dtype=float)
    u = np.asarray(control, dtype=float)


    if len(time) != len(T):
        raise ValueError(
            "time and temperature must have the same length."
        )

    if len(u) not in (len(time), len(time) - 1):
        raise ValueError(
            "control must have either len(time) or len(time)-1 samples."
        )



    if len(time) < 2:
        raise ValueError("At least two simulation samples are required.")

    dt = np.mean(np.diff(time))

    # ---------------------------------------------------------
    # Tracking error
    # ---------------------------------------------------------
    error = setpoint - T

    final_temperature = T[-1]
    steady_state_error = setpoint - final_temperature

    # ---------------------------------------------------------
    # Maximum temperature and overshoot
    # ---------------------------------------------------------
    max_temperature = np.max(T)

    commanded_change = setpoint - T[0]

    if commanded_change > 0:
        overshoot = max(0.0, max_temperature - setpoint)
        overshoot_percent = (
            100.0 * overshoot / abs(commanded_change)
        )
    else:
        overshoot = np.nan
        overshoot_percent = np.nan

    # ---------------------------------------------------------
    # Rise time: 10% -> 90% of commanded change
    # ---------------------------------------------------------
    rise_time = np.nan

    if commanded_change > 0:
        T_low = T[0] + rise_lower * commanded_change
        T_high = T[0] + rise_upper * commanded_change

        idx_low = np.where(T >= T_low)[0]
        idx_high = np.where(T >= T_high)[0]

        if len(idx_low) > 0 and len(idx_high) > 0:
            i_low = idx_low[0]

            valid_high = idx_high[idx_high >= i_low]

            if len(valid_high) > 0:
                i_high = valid_high[0]
                rise_time = time[i_high] - time[i_low]

    # ---------------------------------------------------------
    # Settling time: response enters and remains in +/- band
    # ---------------------------------------------------------
    settling_time = np.nan

    band = settling_band * abs(setpoint)

    inside_band = np.abs(error) <= band

    for i in range(len(T)):
        if np.all(inside_band[i:]):
            settling_time = time[i]
            break

    # ---------------------------------------------------------
    # Integral error metrics
    # ---------------------------------------------------------
    iae = np.sum(np.abs(error)) * dt
    ise = np.sum(error ** 2) * dt

    # ---------------------------------------------------------
    # Control metrics
    # ---------------------------------------------------------
    control_effort = np.sum(np.abs(u)) * dt

    total_variation = np.sum(np.abs(np.diff(u)))

    u_min_observed = np.min(u)
    u_max_observed = np.max(u)

    # ---------------------------------------------------------
    # Saturation
    # ---------------------------------------------------------
    saturated = (
        (u <= u_min + saturation_tol)
        | (u >= u_max - saturation_tol)
    )

    saturation_duration = np.sum(saturated) * dt

    saturation_fraction = np.mean(saturated)

    # ---------------------------------------------------------
    # Return results
    # ---------------------------------------------------------
    return {
        "final_temperature": final_temperature,
        "steady_state_error": steady_state_error,
        "max_temperature": max_temperature,
        "overshoot": overshoot,
        "overshoot_percent": overshoot_percent,
        "rise_time": rise_time,
        "settling_time": settling_time,
        "IAE": iae,
        "ISE": ise,
        "control_effort": control_effort,
        "total_variation": total_variation,
        "u_min": u_min_observed,
        "u_max": u_max_observed,
        "saturation_duration": saturation_duration,
        "saturation_fraction": saturation_fraction,
    }

def calculate_tracking_metrics(
    time,
    temperature,
    control,
    reference,
    u_min=0.0,
    u_max=1.0,
    saturation_tol=1e-9,
):
    """
    Calculate performance metrics for a time-varying reference.

    Parameters
    ----------
    time : array-like
        Simulation time vector. Length N+1.

    temperature : array-like
        Temperature response. Length N+1.

    control : array-like
        Control signal. Typically length N.

    reference : array-like
        Reference temperature profile. Length N+1.

    u_min, u_max : float
        Actuator limits.

    saturation_tol : float
        Numerical tolerance used for saturation detection.

    Returns
    -------
    dict
        Tracking and control-performance metrics.
    """

    import numpy as np

    time = np.asarray(time, dtype=float)
    T = np.asarray(temperature, dtype=float)
    u = np.asarray(control, dtype=float)
    r = np.asarray(reference, dtype=float)

    # ========================================================
    # INPUT VALIDATION
    # ========================================================

    if len(time) != len(T):
        raise ValueError(
            "time and temperature must have the same length."
        )

    if len(reference) != len(time):
        raise ValueError(
            "reference and time must have the same length."
        )

    if len(u) not in (len(time), len(time) - 1):
        raise ValueError(
            "control must have either len(time) or len(time)-1 samples."
        )

    if len(time) < 2:
        raise ValueError(
            "At least two time samples are required."
        )

    # ========================================================
    # TIME STEP
    # ========================================================

    dt = float(np.mean(np.diff(time)))

    # ========================================================
    # TRACKING ERROR
    # ========================================================

    error = r - T

    IAE = np.sum(np.abs(error)) * dt
    ISE = np.sum(error ** 2) * dt
    RMSE = np.sqrt(np.mean(error ** 2))
    MAE = np.mean(np.abs(error))

    max_abs_error = np.max(np.abs(error))

    final_error = error[-1]

    # ========================================================
    # CONTROL PERFORMANCE
    # ========================================================

    control_effort = np.sum(np.abs(u)) * dt

    if len(u) > 1:
        total_variation = np.sum(np.abs(np.diff(u)))
    else:
        total_variation = 0.0

    # ========================================================
    # SATURATION
    # ========================================================

    saturated = (
        (u <= u_min + saturation_tol)
        | (u >= u_max - saturation_tol)
    )

    saturation_duration = np.sum(saturated) * dt

    if len(u) > 0:
        saturation_fraction = np.mean(saturated)
    else:
        saturation_fraction = 0.0

    # ========================================================
    # RESULTS
    # ========================================================

    return {
        "IAE": float(IAE),
        "ISE": float(ISE),
        "RMSE": float(RMSE),
        "MAE": float(MAE),
        "max_abs_error": float(max_abs_error),
        "final_error": float(final_error),
        "control_effort": float(control_effort),
        "total_variation": float(total_variation),
        "u_min": float(np.min(u)),
        "u_max": float(np.max(u)),
        "saturation_duration": float(saturation_duration),
        "saturation_fraction": float(saturation_fraction),
    }


def calculate_tracking_segment_metrics(
    time,
    temperature,
    control,
    reference,
    start_time,
    u_min=0.0,
    u_max=1.0,
):
    """
    Calculate tracking metrics from a specified event time onward.
    """

    import numpy as np

    time = np.asarray(time, dtype=float)
    T = np.asarray(temperature, dtype=float)
    u = np.asarray(control, dtype=float)
    reference = np.asarray(reference, dtype=float)

    idx = np.where(time >= start_time)[0]

    if len(idx) == 0:
        raise ValueError(
            "start_time lies outside the simulation interval."
        )

    idx = idx[0]

    time_seg = time[idx:] - time[idx]
    T_seg = T[idx:]
    reference_seg = reference[idx:]

    # u[k] corresponds to interval k -> k+1
    u_seg = u[idx:]

    return calculate_tracking_metrics(
        time_seg,
        T_seg,
        u_seg,
        reference_seg,
        u_min=u_min,
        u_max=u_max,
    )
