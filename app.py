import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

from experiment_runner import (
    EXPERIMENTS,
    run_experiment,
)

# ============================================================
# PLOT COLORS
# ============================================================

REFERENCE_COLOR = "tab:blue"
PI_COLOR = "tab:orange"
PI_AW_COLOR = "tab:green"
MPC_COLOR = "tab:red"

EVENT_COLOR = "tab:blue"
OUTDOOR_COLOR = "tab:blue"

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="HVAC Control Lab",
    page_icon="🌡️",
    layout="wide",
)


# ============================================================
# TITLE
# ============================================================

st.title("HVAC Control Lab")

st.markdown(
    """
    Interactive simulation environment for comparing
    **PI**, **PI with anti-windup**, and **Model Predictive
    Control (MPC)** in a first-order HVAC thermal system.
    """
)


# ============================================================
# SIDEBAR — EXPERIMENT SELECTION
# ============================================================

st.sidebar.header("Experiment")

scenario_name = st.sidebar.selectbox(
    "Select scenario",
    list(EXPERIMENTS.keys()),
)


st.sidebar.markdown("---")

st.sidebar.header("HVAC Model")

C = st.sidebar.number_input(
    "Thermal capacitance C",
    min_value=1.0,
    max_value=30.0,
    value=8.0,
    step=0.5,
)

R = st.sidebar.number_input(
    "Thermal resistance R",
    min_value=0.5,
    max_value=10.0,
    value=3.5,
    step=0.1,
)

K_heating = st.sidebar.number_input(
    "Heating gain K",
    min_value=1.0,
    max_value=30.0,
    value=11.0,
    step=0.5,
)

T_out = st.sidebar.number_input(
    "Outdoor temperature [°C]",
    min_value=-30.0,
    max_value=30.0,
    value=0.0,
    step=1.0,
)

T0 = st.sidebar.number_input(
    "Initial indoor temperature [°C]",
    min_value=0.0,
    max_value=40.0,
    value=15.0,
    step=1.0,
)

T_set = st.sidebar.number_input(
    "Temperature setpoint [°C]",
    min_value=10.0,
    max_value=30.0,
    value=22.0,
    step=0.5,
)

with st.sidebar.expander(
    "Current model settings"
):
    st.write(
        f"C = {C:.1f}, "
        f"R = {R:.1f}"
    )

    st.write(
        f"K = {K_heating:.1f}, "
        f"T_out = {T_out:.1f} °C"
    )

    st.write(
        f"T0 = {T0:.1f} °C, "
        f"T_set = {T_set:.1f} °C"
    )

st.sidebar.markdown("---")

st.sidebar.header(
    "Controller Tuning"
)

st.sidebar.subheader(
    "PI / PI + Anti-Windup"
)

Kp = st.sidebar.number_input(
    "Proportional gain Kp",
    min_value=0.0,
    max_value=2.0,
    value=0.4,
    step=0.05,
)

Ki = st.sidebar.number_input(
    "Integral gain Ki",
    min_value=0.0,
    max_value=0.5,
    value=0.05,
    step=0.01,
)


st.sidebar.subheader(
    "Model Predictive Control"
)

Np = st.sidebar.slider(
    "Prediction horizon Np",
    min_value=5,
    max_value=120,
    value=60,
    step=5,
)

lambda_u = st.sidebar.number_input(
    "Control penalty λ",
    min_value=0.0,
    max_value=1.0,
    value=0.01,
    step=0.01,
    format="%.3f",
)

grid_points = st.sidebar.slider(
    "Control grid points",
    min_value=5,
    max_value=101,
    value=21,
    step=2,
)

controller_params = {
    "Kp": Kp,
    "Ki": Ki,
    "Np": Np,
    "lambda_u": lambda_u,
    "grid_points": grid_points,
}


model_params = {
    "C": C,
    "R": R,
    "K_heating": K_heating,
    "T_out": T_out,
    "T0": T0,
    "T_set": T_set,
}

st.sidebar.markdown("---")

st.sidebar.markdown(
    """
    **Controllers**

    - PI
    - PI + Anti-Windup
    - MPC
    """
)


with st.sidebar.expander(
    "Current controller settings"
):
    st.write(
        f"PI: Kp = {Kp:.2f}, "
        f"Ki = {Ki:.3f}"
    )

    st.write(
        f"MPC: Np = {Np}, "
        f"λ = {lambda_u:.3f}, "
        f"grid = {grid_points}"
    )



# ============================================================
# RUN EXPERIMENT
# ============================================================

results = run_experiment(
    scenario_name,
    controller_params=controller_params,
    model_params=model_params,
)

time = results["time"]
reference = results["reference"]
controllers = results["controllers"]
extra = results["extra"]


# ============================================================
# SCENARIO DESCRIPTION
# ============================================================

SCENARIO_DESCRIPTIONS = {

    "Baseline":
        "Closed-loop temperature regulation for the "
        "selected HVAC model settings.",

    "Reduced actuator authority":
        "Evaluation of controller behavior when the "
        "maximum heating command is reduced to 0.8.",

    "Reference change":
        "Reference-tracking experiment with a temperature "
        "setpoint change from 22 °C to 20 °C at 120 min.",

    "Outdoor-temperature disturbance":
        "Disturbance-rejection experiment with outdoor "
        "temperature changing from 0 °C to −10 °C "
        "at 120 min.",

    "Model mismatch":
        "Robustness experiment in which the MPC controller "
        "uses the nominal HVAC model while the actual plant "
        "has different thermal parameters.",
}

# Dynamic scenario descriptions

if scenario_name == "Reference change":
    T_ref_initial = model_params["T_set"]
    T_ref_final = T_ref_initial - 2.0

    SCENARIO_DESCRIPTIONS["Reference change"] = (
        f"Reference-tracking experiment with a temperature "
        f"setpoint change from {T_ref_initial:g} °C to "
        f"{T_ref_final:g} °C at 120 min."
    )

elif scenario_name == "Outdoor-temperature disturbance":
    T_out_initial = model_params["T_out"]
    T_out_final = T_out_initial - 10.0

    SCENARIO_DESCRIPTIONS["Outdoor-temperature disturbance"] = (
        f"Disturbance-rejection experiment with outdoor temperature "
        f"changing from {T_out_initial:g} °C to "
        f"{T_out_final:g} °C at 120 min."
    )

st.subheader(scenario_name)

st.info(
    SCENARIO_DESCRIPTIONS[
        scenario_name
    ]
)


# ============================================================
# TEMPERATURE RESPONSE
# ============================================================

st.header("Temperature Response")

fig_temp, ax_temp = plt.subplots(
    figsize=(9, 5)
)

ax_temp.plot(
    time,
    reference,
    "--",
    color=REFERENCE_COLOR,
    label="Reference",
)

ax_temp.plot(
    time,
    controllers["PI"]["T"],
    color=PI_COLOR,
    label="PI",
)

ax_temp.plot(
    time,
    controllers["PI_AW"]["T"],
    color=PI_AW_COLOR,
    label="PI + AW",
)

ax_temp.plot(
    time,
    controllers["MPC"]["T"],
    color=MPC_COLOR,
    label="MPC",
)



# Event marker
if scenario_name == "Reference change":

    ax_temp.axvline(
        extra["change_time"],
        linestyle=":",
        color=EVENT_COLOR,
        label="Reference change",
    )


elif scenario_name == "Outdoor-temperature disturbance":

    ax_temp.axvline(
        extra["disturbance_time"],
        linestyle=":",
        color=EVENT_COLOR,
        label="Disturbance",
    )


ax_temp.set_xlabel(
    "Time [min]"
)

ax_temp.set_ylabel(
    "Temperature [°C]"
)

ax_temp.grid(True)

ax_temp.legend()

fig_temp.tight_layout()

st.pyplot(
    fig_temp,
    width=1000,
)

plt.close(fig_temp)


# ============================================================
# CONTROL SIGNALS
# ============================================================

st.header("Control Signals")

fig_control, ax_control = plt.subplots(
    figsize=(9, 5)
)

ax_control.plot(
    time[:-1],
    controllers["PI"]["u"],
    color=PI_COLOR,
    label="PI",
)

ax_control.plot(
    time[:-1],
    controllers["PI_AW"]["u"],
    color=PI_AW_COLOR,
    label="PI + AW",
)

ax_control.plot(
    time[:-1],
    controllers["MPC"]["u"],
    color=MPC_COLOR,
    label="MPC",
)

if scenario_name == "Reference change":

    ax_control.axvline(
        extra["change_time"],
        linestyle=":",
        color=EVENT_COLOR,
    )


elif scenario_name == "Outdoor-temperature disturbance":

    ax_control.axvline(
        extra["disturbance_time"],
        linestyle=":",
        color=EVENT_COLOR,
    )


ax_control.set_xlabel("Time [min]")
ax_control.set_ylabel("Control signal u[k]")
ax_control.set_ylim(-0.05, 1.05)
ax_control.grid(True)
ax_control.legend()

fig_control.tight_layout()

st.pyplot(
    fig_control,
    width=1000,
)
plt.close(fig_control)


# ============================================================
# PERFORMANCE METRICS
# ============================================================

st.header("Performance Metrics")

metric_rows = []

for controller_name, display_name in [
    ("PI", "PI"),
    ("PI_AW", "PI + AW"),
    ("MPC", "MPC"),
]:

    m = controllers[
        controller_name
    ]["metrics"]

    row = {
        "Controller": display_name,
        "IAE": m["IAE"],
        "ISE": m["ISE"],
        "Control effort":
            m["control_effort"],
        "Total variation":
            m["total_variation"],
        "Saturation [%]":
            100 * m["saturation_fraction"],
    }

    # Constant-reference experiments
    if "final_temperature" in m:

        row["Final T [°C]"] = (
            m["final_temperature"]
        )

        row["Steady-state error [°C]"] = (
            m["steady_state_error"]
        )

        row["Overshoot [°C]"] = (
            m["overshoot"]
        )

        row["Settling time [min]"] = (
            m["settling_time"]
        )

    # Tracking experiments
    else:

        row["RMSE [°C]"] = (
            m["RMSE"]
        )

        row["MAE [°C]"] = (
            m["MAE"]
        )

        row["Final error [°C]"] = (
            m["final_error"]
        )

    metric_rows.append(row)


metrics_df = pd.DataFrame(
    metric_rows
)

metrics_df = metrics_df.set_index(
    "Controller"
)

st.dataframe(
    metrics_df.style.format(
        "{:.4f}"
    ),
    width=1000,
)


# ============================================================
# EVENT METRICS
# ============================================================

if "event_metrics" in extra:

    st.header(
        "Post-Event Performance"
    )

    event_rows = []

    for controller_name, display_name in [
        ("PI", "PI"),
        ("PI_AW", "PI + AW"),
        ("MPC", "MPC"),
    ]:

        m = extra[
            "event_metrics"
        ][controller_name]

        event_rows.append(
            {
                "Controller":
                    display_name,

                "IAE":
                    m["IAE"],

                "ISE":
                    m["ISE"],

                "RMSE [°C]":
                    m["RMSE"],

                "MAE [°C]":
                    m["MAE"],

                "Final error [°C]":
                    m["final_error"],

                "Total variation":
                    m["total_variation"],
            }
        )


    event_df = pd.DataFrame(
        event_rows
    )

    event_df = event_df.set_index(
        "Controller"
    )

    st.dataframe(
        event_df.style.format(
            "{:.4f}"
        ),
        width=1000,
    )


# ============================================================
# DISTURBANCE PROFILE
# ============================================================

if (
    scenario_name
    == "Outdoor-temperature disturbance"
):

    st.header(
        "Outdoor-Temperature Profile"
    )

    fig_dist, ax_dist = plt.subplots(
        figsize=(9, 3.5)
    )

    ax_dist.plot(
        time,
        extra["T_out_profile"],
        color=OUTDOOR_COLOR,
    )

    ax_dist.set_xlabel(
        "Time [min]"
    )

    ax_dist.set_ylabel(
        "Outdoor temperature [°C]"
    )

    ax_dist.grid(True)

    fig_dist.tight_layout()

    st.pyplot(
        fig_dist,
        width=1000,
    )

    plt.close(fig_dist)


# ============================================================
# EXPERIMENT DETAILS
# ============================================================

with st.expander(
    "Experiment details"
):

    if scenario_name == "Baseline":

        st.write(
            f"HVAC model: "
            f"C = {model_params['C']:.1f}, "
            f"R = {model_params['R']:.1f}, "
            f"K_heating = {model_params['K_heating']:.1f}, "
            f"T_out = {model_params['T_out']:.1f} °C."
        )

    elif scenario_name == "Reduced actuator authority":

        st.write(
            f"Actuator limits: "
            f"{extra['u_min']:.1f} ≤ u ≤ "
            f"{extra['u_max']:.1f}."
        )

    elif scenario_name == "Reference change":

        st.write(
            f"Reference changes from "
            f"{extra['reference_initial']:.1f} °C "
            f"to {extra['reference_final']:.1f} °C "
            f"at t = {extra['change_time']:.0f} min."
        )

    elif scenario_name == "Outdoor-temperature disturbance":

        st.write(
            f"Outdoor temperature changes from "
            f"{extra['T_out_initial']:.1f} °C "
            f"to {extra['T_out_final']:.1f} °C "
            f"at t = "
            f"{extra['disturbance_time']:.0f} min."
        )

    elif scenario_name == "Model mismatch":

        st.write(
            f"Nominal MPC model: "
            f"C = {extra['nominal_C']:.1f}, "
            f"R = {extra['nominal_R']:.1f}."
        )

        st.write(
            f"Actual plant: "
            f"C = {extra['plant_C']:.1f}, "
            f"R = {extra['plant_R']:.1f}."
        )
