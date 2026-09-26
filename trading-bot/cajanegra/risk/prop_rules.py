"""Reglas de cuentas de fondeo y simulación de una cuenta día a día.

Las reglas cambian a menudo y difieren entre firmas: los ficheros de config/reglas son
PLANTILLAS. Copia los números exactos de la web de tu firma antes de fiarte del resultado.
"""

from __future__ import annotations

import math
import tomllib
from dataclasses import dataclass, field, fields
from pathlib import Path

DD_TYPES = ("estatico", "trailing_cierre", "trailing_intradia")


@dataclass
class AccountRules:
    nombre: str = "Evaluación"
    capital_inicial: float = 50_000.0
    objetivo_beneficio: float | None = None   # en la fondeada: beneficio necesario para el PRIMER retiro
    objetivo_ciclo: float | None = None       # fondeada: beneficio desde el último retiro para pedir otro
    drawdown_maximo: float = 2_000.0
    tipo_drawdown: str = "trailing_cierre"    # estatico | trailing_cierre | trailing_intradia
    bloqueo_drawdown: float | None = None     # el suelo deja de subir en capital_inicial + este valor
    perdida_diaria_max: float | None = None
    accion_perdida_diaria: str = "suspende_dia"  # suspende_dia (la firma cierra y paras hoy) | elimina
    dias_minimos: int = 0                     # días operados mínimos (por fase o por ciclo de retiro)
    dias_ganadores_minimos: int = 0           # por fase o por ciclo de retiro
    ganancia_minima_dia: float = 0.0          # para que un día cuente como "ganador"
    consistencia_max_dia: float | None = None  # el mejor día no puede superar esta fracción del beneficio del ciclo
    dias_maximos: int | None = None           # sesiones máximas desde el inicio (None = sin límite)
    max_contratos: int | None = None          # se aplica en el backtest vía guardián

    def __post_init__(self):
        if self.tipo_drawdown not in DD_TYPES:
            raise ValueError(f"tipo_drawdown debe ser uno de {DD_TYPES}")
        if self.accion_perdida_diaria not in ("suspende_dia", "elimina"):
            raise ValueError("accion_perdida_diaria debe ser 'suspende_dia' o 'elimina'")

    @classmethod
    def from_dict(cls, d: dict) -> "AccountRules":
        valid = {f.name for f in fields(cls)}
        unknown = set(d) - valid
        if unknown:
            raise ValueError(f"Campos desconocidos en reglas: {sorted(unknown)}")
        return cls(**d)


@dataclass
class Economics:
    coste_evaluacion: float = 0.0
    cobro_evaluacion: str = "unico"  # unico | mensual
    coste_activacion: float = 0.0    # al pasar a fondeada
    reparto: float = 0.9             # parte del beneficio que cobras
    retiro_maximo: float | None = None   # tope por retiro (importe bruto)
    retiro_fraccion: float = 1.0     # fracción del beneficio retirable por petición (p. ej. 0.5)
    retiro_minimo: float = 0.0       # importe bruto mínimo de un retiro
    colchon_retiro: float = 0.0      # beneficio que debe quedar siempre en la cuenta
    sesiones_por_mes: int = 21

    def evaluation_cost(self, sessions: int) -> float:
        if self.cobro_evaluacion == "mensual":
            return self.coste_evaluacion * max(1, math.ceil(sessions / self.sesiones_por_mes))
        return self.coste_evaluacion

    def withdrawable(self, profit: float) -> float:
        """Importe bruto que se puede retirar ahora con ese beneficio acumulado (0 si no llega al mínimo)."""
        amount = max(0.0, profit - self.colchon_retiro) * self.retiro_fraccion
        if self.retiro_maximo is not None:
            amount = min(amount, self.retiro_maximo)
        return amount if amount > 0 and amount >= self.retiro_minimo else 0.0

    def payout(self, profit: float) -> float:
        """Lo que cobras (tras el reparto) al retirar con ese beneficio."""
        return self.withdrawable(profit) * self.reparto


@dataclass
class FirmConfig:
    nombre: str
    fases: list[AccountRules]
    fondeada: AccountRules | None = None
    economia: Economics = field(default_factory=Economics)
    aviso: str = ""

    @classmethod
    def from_toml(cls, path: str | Path) -> "FirmConfig":
        data = tomllib.loads(Path(path).read_text(encoding="utf-8"))
        fases = [AccountRules.from_dict(f) for f in data.get("fase", [])]
        if not fases:
            raise ValueError(f"{path}: falta al menos una sección [[fase]]")
        fondeada = AccountRules.from_dict(data["fondeada"]) if "fondeada" in data else None
        economia = Economics(**data.get("economia", {}))
        return cls(data.get("nombre", Path(path).stem), fases, fondeada, economia, data.get("aviso", ""))

    @property
    def max_contratos(self) -> int | None:
        caps = [r.max_contratos for r in [*self.fases, self.fondeada] if r is not None and r.max_contratos]
        return min(caps) if caps else None


class PropAccount:
    """Cuenta simulada que procesa resúmenes diarios (pnl, extremos intradía) y aplica las reglas.

    Precisión: estático, trailing al cierre y pérdida diaria son exactos con los extremos
    intradía. El trailing intradía es exacto si la cuenta empieza el día en su máximo, y
    conservador (puede suspender de más) si no.
    """

    def __init__(self, rules: AccountRules):
        self.r = rules
        self.balance = rules.capital_inicial
        self.hwm = rules.capital_inicial
        self.floor = self._floor_from(self.hwm)
        self.sessions = 0
        self.days_traded = 0
        self.winning_days = 0
        self.best_day = 0.0
        self.status = "activa"   # activa | aprobada (o retiro disponible) | suspendida | caducada
        self.reason = ""
        self.payouts = 0
        self._new_cycle()

    def _new_cycle(self) -> None:
        self.cycle_start = self.balance
        self.cycle_days = 0
        self.cycle_winning = 0
        self.cycle_best = 0.0

    @property
    def profit(self) -> float:
        return self.balance - self.r.capital_inicial

    def _floor_from(self, hwm: float) -> float:
        f = hwm - self.r.drawdown_maximo
        if self.r.bloqueo_drawdown is not None:
            f = min(f, self.r.capital_inicial + self.r.bloqueo_drawdown)
        return f

    def _fail(self, reason: str) -> str:
        self.status, self.reason = "suspendida", reason
        return self.status

    def process_day(self, pnl: float, min_equity: float, max_equity: float, dd_intradia: float, n_trades: int) -> str:
        """Aplica un día. Los importes son relativos al balance de inicio del día."""
        if self.status != "activa":
            return self.status
        r = self.r
        self.sessions += 1
        if n_trades > 0:
            start = self.balance
            low, day_pnl, retrace = min_equity, pnl, dd_intradia
            dll = r.perdida_diaria_max
            if dll is not None and min_equity <= -dll:
                if r.accion_perdida_diaria == "elimina":
                    # si el suelo está por encima del límite diario, se tocó antes el suelo
                    return self._fail("drawdown máximo" if self.floor >= start - dll else "pérdida diaria máxima")
                # suspende_dia: la firma liquida al tocar el límite y ese día ya no se opera
                low, day_pnl = -dll, -dll
                retrace = min(dd_intradia, max_equity + dll)
            if start + low <= self.floor:
                return self._fail("drawdown máximo")
            if r.tipo_drawdown == "trailing_intradia" and start + max_equity > self.hwm:
                # el suelo sube con el pico intradía; distancia pico-suelo más pequeña posible hoy:
                gap = r.drawdown_maximo
                if r.bloqueo_drawdown is not None:
                    gap = max(gap, self.hwm - (r.capital_inicial + r.bloqueo_drawdown))
                if retrace >= gap:
                    return self._fail("drawdown máximo (trailing intradía)")
                self.hwm = start + max_equity
                self.floor = max(self.floor, self._floor_from(self.hwm))
            self.balance = start + day_pnl
            self.days_traded += 1
            self.cycle_days += 1
            self.best_day = max(self.best_day, day_pnl)
            self.cycle_best = max(self.cycle_best, day_pnl)
            if day_pnl > 0 and day_pnl >= r.ganancia_minima_dia:
                self.winning_days += 1
                self.cycle_winning += 1
            if r.tipo_drawdown != "estatico" and self.balance > self.hwm:
                self.hwm = self.balance
                self.floor = max(self.floor, self._floor_from(self.hwm))
            if self._target_reached():
                self.status = "aprobada"
                return self.status
        if r.dias_maximos is not None and self.sessions >= r.dias_maximos:
            self.status, self.reason = "caducada", "límite de días"
        return self.status

    def withdraw(self, amount: float) -> None:
        """Retira `amount` (bruto). El suelo de drawdown NO baja: quedas más cerca de él."""
        self.balance -= amount
        self.payouts += 1
        self.status, self.reason = "activa", ""
        self._new_cycle()

    def _target_reached(self) -> bool:
        r = self.r
        if self.payouts == 0:
            if r.objetivo_beneficio is None or self.profit < r.objetivo_beneficio:
                return False
        else:
            goal = r.objetivo_ciclo if r.objetivo_ciclo is not None else r.objetivo_beneficio
            if goal is None or self.balance - self.cycle_start < goal:
                return False
        if self.cycle_days < r.dias_minimos or self.cycle_winning < r.dias_ganadores_minimos:
            return False
        cycle_profit = self.balance - self.cycle_start
        if r.consistencia_max_dia is not None and self.cycle_best > r.consistencia_max_dia * cycle_profit:
            return False
        return True
