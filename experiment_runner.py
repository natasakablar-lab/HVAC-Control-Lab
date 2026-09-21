import numpy as np

from model import HVACModel, HVACParameters
from controllers import PIController, MPCController

from simulation import (
    simulate,
    simulate_reference_profile,
    simulate_disturbance_profile,
    simulate_model_mismatch,
)

from metrics import (
    calculate_metrics,
    calculate_tracking_metrics,
    calculate_tracking_segment_metrics,
)

# ============================================================
# DEFAULT CONTROLLER PARAMETERS
# ============================================================

DEFAULT_KP = 0.4
DEFAULT_KI = 0.05

DEFAULT_NP = 60
DEFAULT_LAMBDA_U = 0.01
DEFAULT_GRID_POINTS = 21


# ============================================================
# CONTROLLER FACTORY
# ============================================================

def get_model_parameters(user_params=None):
    """
    Merge user-defined HVAC model parameters with
    verified baseline defaults.
    """

    params = {
        "C": 8.0,
        "R": 3.5,
        "K_heating": 11.0,
        "T_out": 0.0,
        "T0": 15.0,
        "T_set": 22.0,
    }

    if user_params is not None:
        params.update(user_params)

    return params

def get_controller_parameters(user_params=None):
    """
    Merge user-defined controller parameters with
    verified baseline defaults.
    """

    params = {
        "Kp": DEFAULT_KP,
        "Ki": DEFAULT_KI,
        "Np": DEFAULT_NP,
        "lambda_u": DEFAULT_LAMBDA_U,
        "grid_points": DEFAULT_GRID_POINTS,
    }

    if user_params is not None:
        params.update(user_params)

    return params


def create_controllers(
    model,
    dt,
    u_min=0.0,
    u_max=1.0,
    controller_params=None,
):
    """
    Create PI, PI with anti-windup, and MPC controllers.

    If controller_params is omitted, verified baseline
    controller parameters are used.
    """

    p = get_controller_parameters(
        controller_params
    )

    pi = PIController(
        Kp=p["Kp"],
        Ki=p["Ki"],
        dt=dt,
        anti_windup=False,
        u_min=u_min,
        u_max=u_max,
    )

    pi_aw = PIController(
        Kp=p["Kp"],
        Ki=p["Ki"],
        dt=dt,
        anti_windup=True,
        u_min=u_min,
        u_max=u_max,
    )

    mpc = MPCController(
        model=model,
        Np=p["Np"],
        lambda_u=p["lambda_u"],
        u_min=u_min,
        u_max=u_max,
        grid_points=p["grid_points"],
    )

    return {
        "PI": pi,
        "PI_AW": pi_aw,
        "MPC": mpc,
    }


# ============================================================
# MODEL FACTORY
# ============================================================

def create_model(
    C=8.0,
    R=3.5,
    K_heating=11.0,
    T_out=0.0,
    dt=1.0,
):
    """
    Create an HVAC model from physical parameters.
    """

    params = HVACParameters(
        C=C,
        R=R,
        K_heating=K_heating,
        T_out=T_out,
        dt=dt,
    )

    return HVACModel(params)


# ============================================================
# RESULT PACKAGING
# ============================================================

def package_results(
    scenario_name,
    time,
    reference,
    responses,
    metrics,
    extra=None,
):
    """
    Return results in one standardized structure.
    """

    return {
        "scenario": scenario_name,
        "time": time,
        "reference": reference,
        "controllers": {
            name: {
                "T": responses[name]["T"],
                "u": responses[name]["u"],
                "metrics": metrics[name],
            }
            for name in responses
        },
        "extra": extra or {},
    }

# ============================================================
# EXPERIMENT 1 — BASELINE
# ============================================================

def run_baseline(
    controller_params=None,
    model_params=None,
):
    """
    Nominal constant-setpoint experiment.
    """

    p = get_model_parameters(
        model_params
    )

    T0 = p["T0"]
    T_set = p["T_set"]
    sim_time = 240.0

    model = create_model(
        C=p["C"],
        R=p["R"],
        K_heating=p["K_heating"],
        T_out=p["T_out"],
    )

    controllers = create_controllers(
        model=model,
        dt=model.params.dt,
        controller_params=controller_params,
    )

    responses = {}
    metrics = {}

    for name, controller in controllers.items():

        time, T, u = simulate(
            model,
            controller,
            T0,
            T_set,
            sim_time,
        )

        responses[name] = {
            "T": T,
            "u": u,
        }

        metrics[name] = calculate_metrics(
            time,
            T,
            u,
            T_set,
        )

    reference = np.full_like(
        time,
        T_set,
        dtype=float,
    )

    return package_results(
        "Baseline",
        time,
        reference,
        responses,
        metrics,
    )


# ============================================================
# EXPERIMENT 2 — REDUCED ACTUATOR AUTHORITY
# ============================================================

def run_actuator_limit(
    controller_params=None,
    model_params=None,
):
    """
    Reduced actuator upper limit: u_max = 0.8.
    """

    p = get_model_parameters(model_params)

    T0 = p["T0"]
    T_set = p["T_set"]
    sim_time = 240.0

    u_min = 0.0
    u_max = 0.8

    model = create_model(
        C=p["C"],
        R=p["R"],
        K_heating=p["K_heating"],
        T_out=p["T_out"],
    )

    controllers = create_controllers(
        model=model,
        dt=model.params.dt,
        u_min=u_min,
        u_max=u_max,
        controller_params=controller_params,
    )

    responses = {}
    metrics = {}

    for name, controller in controllers.items():

        time, T, u = simulate(
            model,
            controller,
            T0,
            T_set,
            sim_time,
        )

        responses[name] = {
            "T": T,
            "u": u,
        }

        metrics[name] = calculate_metrics(
            time,
            T,
            u,
            T_set,
            u_min=u_min,
            u_max=u_max,
        )

    reference = np.full_like(
        time,
        T_set,
        dtype=float,
    )

    return package_results(
        "Reduced actuator authority",
        time,
        reference,
        responses,
        metrics,
        extra={
            "u_min": u_min,
            "u_max": u_max,
        },
    )


# ============================================================
# EXPERIMENT 3 — REFERENCE CHANGE
# ============================================================

def run_reference_change(
    controller_params=None,
    model_params=None,
):
    """
    Reference change experiment.

    Default case:
    22 °C -> 20 °C at t = 120 min.

    If model parameters are changed interactively,
    the initial reference follows T_set and the
    post-event reference remains 2 °C lower.
    """

    p = get_model_parameters(model_params)

    T0 = p["T0"]

    sim_time = 240.0
    dt = 1.0
    change_time = 120.0

    reference_initial = p["T_set"]
    reference_final = reference_initial - 2.0

    model = create_model(
        C=p["C"],
        R=p["R"],
        K_heating=p["K_heating"],
        T_out=p["T_out"],
        dt=dt,
    )

    n_steps = int(sim_time / dt)

    time_profile = (
        np.arange(n_steps + 1) * dt
    )

    reference = np.where(
        time_profile < change_time,
        reference_initial,
        reference_final,
    )

    controllers = create_controllers(
        model=model,
        dt=dt,
        controller_params=controller_params,
    )

    responses = {}
    metrics = {}

    for name, controller in controllers.items():

        time, T, u = simulate_reference_profile(
            model,
            controller,
            T0,
            reference,
        )

        responses[name] = {
            "T": T,
            "u": u,
        }

        metrics[name] = calculate_tracking_metrics(
            time,
            T,
            u,
            reference,
        )

    event_metrics = {}

    for name in responses:

        event_metrics[name] = (
            calculate_tracking_segment_metrics(
                time,
                responses[name]["T"],
                responses[name]["u"],
                reference,
                start_time=change_time,
            )
        )

    return package_results(
        "Reference change",
        time,
        reference,
        responses,
        metrics,
        extra={
            "change_time": change_time,
            "reference_initial": reference_initial,
            "reference_final": reference_final,
            "event_metrics": event_metrics,
        },
    )

# ============================================================
# EXPERIMENT 4 — OUTDOOR DISTURBANCE
# ============================================================




def run_outdoor_disturbance(
    controller_params=None,
    model_params=None,
):
    """
    Outdoor-temperature disturbance experiment.

    Default case:
    0 °C -> -10 °C at t = 120 min.

    The disturbance is defined as a 10 °C decrease
    relative to the user-selected nominal outdoor
    temperature.
    """

    p = get_model_parameters(model_params)

    T0 = p["T0"]
    T_set = p["T_set"]

    sim_time = 240.0
    dt = 1.0

    disturbance_time = 120.0

    T_out_initial = p["T_out"]
    T_out_final = T_out_initial - 10.0

    model = create_model(
        C=p["C"],
        R=p["R"],
        K_heating=p["K_heating"],
        T_out=T_out_initial,
        dt=dt,
    )

    n_steps = int(sim_time / dt)

    time_profile = (
        np.arange(n_steps + 1) * dt
    )

    T_out_profile = np.where(
        time_profile < disturbance_time,
        T_out_initial,
        T_out_final,
    )

    reference = np.full(
        n_steps + 1,
        T_set,
        dtype=float,
    )

    controllers = create_controllers(
        model=model,
        dt=dt,
        controller_params=controller_params,
    )

    responses = {}
    metrics = {}

    for name, controller in controllers.items():

        time, T, u = simulate_disturbance_profile(
            model,
            controller,
            T0,
            T_set,
            T_out_profile,
        )

        responses[name] = {
            "T": T,
            "u": u,
        }

        metrics[name] = calculate_tracking_metrics(
            time,
            T,
            u,
            reference,
        )

    event_metrics = {}

    for name in responses:

        event_metrics[name] = (
            calculate_tracking_segment_metrics(
                time,
                responses[name]["T"],
                responses[name]["u"],
                reference,
                start_time=disturbance_time,
            )
        )

    return package_results(
        "Outdoor-temperature disturbance",
        time,
        reference,
        responses,
        metrics,
        extra={
            "disturbance_time": disturbance_time,
            "T_out_profile": T_out_profile,
            "T_out_initial": T_out_initial,
            "T_out_final": T_out_final,
            "event_metrics": event_metrics,
        },
    )


# ============================================================
# EXPERIMENT 5 — MODEL MISMATCH
# ============================================================

def run_model_mismatch(
    controller_params=None,
    model_params=None,
):
    """
    Model-mismatch robustness experiment.

    The user-selected HVAC parameters define the
    nominal controller model.

    The actual plant differs from the nominal model:
        C_actual = 1.25 * C_nominal
        R_actual = (3.0 / 3.5) * R_nominal

    Default case:
        nominal C = 8.0, R = 3.5
        actual  C = 10.0, R = 3.0
    """

    p = get_model_parameters(model_params)

    T0 = p["T0"]
    T_set = p["T_set"]

    sim_time = 240.0
    dt = 1.0

    nominal_C = p["C"]
    nominal_R = p["R"]

    plant_C = 1.25 * nominal_C
    plant_R = (3.0 / 3.5) * nominal_R

    nominal_model = create_model(
        C=nominal_C,
        R=nominal_R,
        K_heating=p["K_heating"],
        T_out=p["T_out"],
        dt=dt,
    )

    plant_model = create_model(
        C=plant_C,
        R=plant_R,
        K_heating=p["K_heating"],
        T_out=p["T_out"],
        dt=dt,
    )

    controllers = create_controllers(
        model=nominal_model,
        dt=dt,
        controller_params=controller_params,
    )

    responses = {}
    metrics = {}

    for name, controller in controllers.items():

        time, T, u = simulate_model_mismatch(
            plant_model,
            controller,
            T0,
            T_set,
            sim_time,
        )

        responses[name] = {
            "T": T,
            "u": u,
        }

        metrics[name] = calculate_metrics(
            time,
            T,
            u,
            T_set,
        )

    reference = np.full_like(
        time,
        T_set,
        dtype=float,
    )

    return package_results(
        "Model mismatch",
        time,
        reference,
        responses,
        metrics,
        extra={
            "nominal_C": nominal_C,
            "nominal_R": nominal_R,
            "plant_C": plant_C,
            "plant_R": plant_R,
            "C_mismatch_factor": 1.25,
            "R_mismatch_factor": 3.0 / 3.5,
        },
    )


# ============================================================
# MAIN EXPERIMENT DISPATCHER
# ============================================================

EXPERIMENTS = {
    "Baseline": run_baseline,
    "Reduced actuator authority": run_actuator_limit,
    "Reference change": run_reference_change,
    "Outdoor-temperature disturbance":
        run_outdoor_disturbance,
    "Model mismatch": run_model_mismatch,
}



def run_experiment(
    name,
    controller_params=None,
    model_params=None,
):
    """
    Run one predefined HVAC control experiment.

    Optional controller_params allow interactive
    controller tuning.

    Optional model_params allow interactive
    modification of HVAC plant parameters.
    """

    if name not in EXPERIMENTS:
        raise ValueError(
            f"Unknown experiment '{name}'. "
            f"Available experiments: "
            f"{list(EXPERIMENTS.keys())}"
        )

    return EXPERIMENTS[name](
        controller_params=controller_params,
        model_params=model_params,
    )
