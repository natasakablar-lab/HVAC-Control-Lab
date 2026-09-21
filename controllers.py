import numpy as np


class PIController:
    def __init__(
        self,
        Kp=0.4,
        Ki=0.05,
        dt=1.0,
        u_min=0.0,
        u_max=1.0,
        anti_windup=False,
    ):
        self.Kp = Kp
        self.Ki = Ki
        self.dt = dt
        self.u_min = u_min
        self.u_max = u_max
        self.anti_windup = anti_windup
        self.integral = 0.0

    def reset(self):
        self.integral = 0.0

    def compute(self, T, T_set):
        e = T_set - T

        I_candidate = self.integral + e * self.dt
        u_unsat = self.Kp * e + self.Ki * I_candidate
        u_sat = np.clip(u_unsat, self.u_min, self.u_max)

        if self.anti_windup:
            pushing_upper = (
                u_sat == self.u_max
                and u_unsat > self.u_max
                and e > 0
            )

            pushing_lower = (
                u_sat == self.u_min
                and u_unsat < self.u_min
                and e < 0
            )

            if pushing_upper or pushing_lower:
                u_unsat = (
                    self.Kp * e
                    + self.Ki * self.integral
                )
                u_sat = np.clip(
                    u_unsat,
                    self.u_min,
                    self.u_max
                )
            else:
                self.integral = I_candidate

        else:
            self.integral = I_candidate

        return float(u_sat)

class MPCController:
    def __init__(
        self,
        model,
        Np=60,
        lambda_u=0.01,
        u_min=0.0,
        u_max=1.0,
        grid_points=21,
    ):
        self.model = model
        self.Np = Np
        self.lambda_u = lambda_u
        self.u_min = u_min
        self.u_max = u_max
        self.grid_points = grid_points
        self.prev_u = 0.0

    def reset(self):
        self.prev_u = 0.0

    def compute(self, T, T_set):
        best_cost = np.inf
        best_u = self.u_min

        candidates = np.linspace(
            self.u_min,
            self.u_max,
            self.grid_points
        )

        for u0 in candidates:
            T_pred = T
            cost = 0.0

            for _ in range(self.Np):
                T_pred = self.model.step(T_pred, u0)
                cost += (T_pred - T_set) ** 2

            cost += (
                self.lambda_u
                * (u0 - self.prev_u) ** 2
            )

            if cost < best_cost:
                best_cost = cost
                best_u = u0

        self.prev_u = best_u

        return float(best_u)
