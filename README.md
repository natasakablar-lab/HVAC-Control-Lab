# HVAC Control Lab

**Version:** 1.0  
**Application type:** Interactive Streamlit simulation environment  
**Purpose:** Comparison of PI, PI with anti-windup, and Model Predictive Control (MPC) for a first-order HVAC thermal model.

## 1. Overview

HVAC Control Lab is an interactive simulation application for exploring closed-loop temperature control in a simplified first-order HVAC thermal system. The application allows the user to modify HVAC model parameters and controller tuning parameters, run five predefined experiments, inspect temperature and control-signal plots, and compare controller performance using quantitative metrics.

The implemented controllers are:

- PI control,
- PI control with anti-windup,
- Model Predictive Control (MPC).

The application is intended for research, reproducibility, controller-comparison, and educational use. It is a simulation tool rather than a building commissioning or real-time HVAC control platform.

## 2. HVAC Model

The thermal model is implemented as a discrete-time first-order system. At each simulation step,

```text
dT = (T_out - T) / R + K_heating * u
T_next = T + (dt / C) * dT
```

where:

- `T` is the indoor temperature,
- `T_out` is the outdoor temperature,
- `C` is the thermal capacitance parameter,
- `R` is the thermal resistance parameter,
- `K_heating` is the heating gain,
- `u` is the normalized heating control command,
- `dt` is the simulation time step.

The verified default model parameters are:

| Parameter | Default value |
|---|---:|
| Thermal capacitance `C` | 8.0 |
| Thermal resistance `R` | 3.5 |
| Heating gain `K_heating` | 11.0 |
| Outdoor temperature `T_out` | 0.0 °C |
| Initial indoor temperature `T0` | 15.0 °C |
| Temperature setpoint `T_set` | 22.0 °C |
| Time step `dt` | 1.0 min |
| Simulation duration | 240 min |

The user can change the model parameters from the Streamlit sidebar before running an experiment.

## 3. Controllers

### 3.1 PI Controller

The PI controller uses the temperature error

```text
e = T_set - T
```

and computes a proportional-plus-integral control action subject to actuator saturation.

Verified default controller parameters:

| Parameter | Default value |
|---|---:|
| Proportional gain `Kp` | 0.4 |
| Integral gain `Ki` | 0.05 |

For the standard experiments, the normalized actuator range is

```text
0.0 <= u <= 1.0
```

except in the reduced-actuator-authority experiment.

### 3.2 PI with Anti-Windup

The anti-windup version uses the same PI gains but applies conditional integration. When the unsaturated control command is already beyond an actuator limit and the error would drive the controller farther into saturation, the integral state is not advanced. This reduces integral windup during actuator saturation.

### 3.3 Model Predictive Control (MPC)

The MPC implementation evaluates a finite set of candidate constant control actions over a prediction horizon and selects the candidate that minimizes a cost consisting of:

- predicted squared temperature-tracking error, and
- a penalty on the change in control action relative to the previous MPC command.

Verified default MPC parameters:

| Parameter | Default value |
|---|---:|
| Prediction horizon `Np` | 60 |
| Control penalty `lambda_u` | 0.01 |
| Control grid points | 21 |

The user can modify `Np`, `lambda_u`, and the number of control grid points from the sidebar.

## 4. Experiments

The application contains five predefined scenarios.

### S1 — Baseline

Nominal closed-loop temperature regulation for the currently selected HVAC model parameters.

Default case:

```text
C = 8.0
R = 3.5
K_heating = 11.0
T_out = 0.0 °C
T0 = 15.0 °C
T_set = 22.0 °C
u_max = 1.0
```

This scenario provides the baseline comparison of PI, PI with anti-windup, and MPC.

### S2 — Reduced Actuator Authority

The HVAC model is unchanged, but the actuator upper limit is reduced to

```text
u_max = 0.8
```

The scenario is intended to emphasize saturation effects and the behavior of the anti-windup PI controller under a tighter control constraint.

### S3 — Reference Change

A setpoint-tracking experiment with a reference change at

```text
t = 120 min
```

The initial reference follows the user-selected setpoint and the final reference is 2 °C lower:

```text
T_ref_initial = T_set
T_ref_final   = T_set - 2 °C
```

Default case:

```text
22 °C -> 20 °C at 120 min
```

In addition to full-simulation metrics, the application reports post-event performance from the reference-change time onward.

### S4 — Outdoor-Temperature Disturbance

A disturbance-rejection experiment in which the outdoor temperature decreases by 10 °C at

```text
t = 120 min
```

The disturbance is defined relative to the user-selected nominal outdoor temperature:

```text
T_out_initial = T_out
T_out_final   = T_out - 10 °C
```

Default case:

```text
0 °C -> -10 °C at 120 min
```

The application also displays the outdoor-temperature disturbance profile and post-event performance metrics.

### S5 — Model Mismatch

A robustness experiment in which the controller is configured using the user-selected nominal HVAC model while the simulated plant has different thermal parameters.

The mismatch is defined as

```text
C_actual = 1.25 * C_nominal
R_actual = (3.0 / 3.5) * R_nominal
```

Default case:

```text
Nominal model: C = 8.0,  R = 3.5
Actual plant:  C = 10.0, R = 3.0
```

For MPC, the prediction model remains the nominal model while the temperature state is propagated by the mismatched plant model.

## 5. Adjustable Parameters

### HVAC model parameters

The sidebar allows interactive modification of:

- `C` — thermal capacitance,
- `R` — thermal resistance,
- `K_heating` — heating gain,
- `T_out` — nominal outdoor temperature,
- `T0` — initial indoor temperature,
- `T_set` — nominal temperature setpoint.

### PI / PI + Anti-Windup parameters

- `Kp` — proportional gain,
- `Ki` — integral gain.

### MPC parameters

- `Np` — prediction horizon,
- `lambda_u` — control-action penalty,
- `grid_points` — number of candidate control values.

Scenario definitions are preserved while the selected model and controller parameters are passed to the simulation engine.

## 6. Plots and Output

For each experiment, the application displays:

1. **Temperature Response** — reference and controller temperature trajectories.
2. **Control Signals** — PI, PI + anti-windup, and MPC control commands.
3. **Performance Metrics** — controller-comparison table.
4. **Experiment Details** — scenario-specific parameter information.

Additional outputs are shown when relevant:

- **Post-Event Performance** for S3 and S4,
- **Outdoor-Temperature Profile** for S4,
- event markers at `t = 120 min` for S3 and S4.

The plotting convention is consistent across scenarios:

- Reference: blue dashed line,
- PI: orange,
- PI + anti-windup: green,
- MPC: red,
- event/disturbance marker: blue dotted line.

The Streamlit dataframe toolbar can be used to export displayed metric tables as CSV files.

## 7. Performance Metrics

### Constant-reference experiments

The metric engine calculates:

- final temperature,
- steady-state error,
- maximum temperature,
- overshoot,
- overshoot percentage,
- rise time,
- settling time,
- Integral Absolute Error (IAE),
- Integral Squared Error (ISE),
- control effort,
- total variation of the control signal,
- observed minimum and maximum control values,
- saturation duration,
- saturation fraction.

The Streamlit table displays the most relevant subset for controller comparison.

### Tracking / disturbance experiments

For time-varying reference or event-based evaluation, the metric engine calculates:

- IAE,
- ISE,
- Root Mean Square Error (RMSE),
- Mean Absolute Error (MAE),
- maximum absolute error,
- final error,
- control effort,
- total variation,
- observed minimum and maximum control values,
- saturation duration,
- saturation fraction.

For S3 and S4, the same tracking metrics are also calculated on the segment beginning at the event time (`t = 120 min`).

## 8. Project Structure

Core application files:

```text
app.py                  Streamlit user interface and visualization
experiment_runner.py    Scenario definitions, controller/model factories,
                        simulation dispatch, and result packaging
model.py                First-order HVAC thermal model
controllers.py          PI, PI anti-windup, and MPC controllers
simulation.py           Closed-loop simulation functions
metrics.py              Performance and tracking metrics
```

Validation and regression-test scripts in the development package include dedicated tests for:

- baseline behavior,
- performance metrics,
- tracking metrics,
- reference-change scenario,
- outdoor-temperature disturbance,
- model mismatch,
- experiment-runner consistency.

Some earlier scenario-development scripts may remain in the archived development package but are not required by the current Streamlit execution path.

## 9. Installation

Create and activate a Python environment, then install the project dependencies.

```bash
pip install -r requirements.txt
```

The principal Python packages used by the application are:

- Streamlit,
- NumPy,
- pandas,
- Matplotlib.

The current release uses a minimal unpinned `requirements.txt`. For archival reproducibility, tested package versions may be pinned in a later release or recorded with the Zenodo deposit.

## 10. Running the Application

From the project directory, run:

```bash
streamlit run app.py
```

Streamlit will open the application in a browser. Select the desired scenario from the sidebar, adjust model or controller parameters if required, and inspect the plots and metric tables.

## 11. Reproducibility and Validation

Version 1.0 was regression-tested after a fresh application start using all five scenarios:

- S1 Baseline,
- S2 Reduced actuator authority,
- S3 Reference change,
- S4 Outdoor-temperature disturbance,
- S5 Model mismatch.

The numerical core was also checked using the project validation scripts. Controller states are reset before each simulation. In the outdoor-disturbance simulation, the original model outdoor-temperature parameter is restored after the disturbance run, preventing the scenario from modifying the model state used by later runs.

For reproducible research use, archive together:

- the source code,
- `requirements.txt`,
- this README,
- regression-test outputs,
- release/version metadata.

## 12. Scope and Limitations

This release intentionally uses a compact first-order thermal model and a transparent controller implementation. Important scope limitations are:

- the HVAC model is a simplified lumped first-order representation,
- the control command is normalized,
- the MPC implementation searches a finite grid of constant candidate inputs over the prediction horizon rather than solving a general constrained multivariable MPC optimization problem,
- the simulations do not use measured building data,
- the application is not intended for direct real-time control of physical HVAC equipment,
- model parameters and experiments are intended for comparative simulation and research/educational analysis.

These limitations are deliberate because the application is designed to make controller behavior, constraints, tracking, disturbance rejection, and model mismatch directly observable.

## 13. Version 1.0 Status

Version 1.0 contains:

- interactive HVAC model parameters,
- interactive PI and MPC tuning parameters,
- five validated scenarios,
- consistent controller colors and plot conventions,
- global performance metrics,
- post-event metrics for reference and disturbance experiments,
- CSV export through the Streamlit table interface,
- fresh-start S1-S5 regression validation.

Potential later additions, if needed, include a reset-to-defaults control and a concise in-application help panel. These are not required for the Version 1.0 simulation core.

## 14. Release Metadata

- **Author:** Natasa Kablar
- **Affiliation:** Independent Researcher
- **Version:** 1.0
- **Release date:** 2026-09-21
- **Repository:** https://github.com/natasakablar-lab/HVAC-Control-Lab
- **Live application:** https://hvac-control-lab.streamlit.app
- **License:** MIT License
- **Zenodo DOI (Version 1.0):** https://doi.org/10.5281/zenodo.22866664
- **Zenodo Concept DOI (all versions):** https://doi.org/10.5281/zenodo.22866663
