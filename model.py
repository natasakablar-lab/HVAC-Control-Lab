from dataclasses import dataclass


@dataclass
class HVACParameters:
    C: float = 8.0
    R: float = 3.5
    K_heating: float = 11.0
    T_out: float = 0.0
    dt: float = 1.0


class HVACModel:
    def __init__(self, params=None):
        self.params = params or HVACParameters()

    def step(self, T, u, T_out=None):
        p = self.params

        if T_out is None:
            T_out = p.T_out

        dT = (T_out - T) / p.R + p.K_heating * u

        return T + (p.dt / p.C) * dT
