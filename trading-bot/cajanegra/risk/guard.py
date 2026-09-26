"""Guardián de riesgo diario: las reglas de disciplina que un humano rompe y un bot no."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DailyRiskGuard:
    max_trades: int | None = None              # operaciones máximas por día
    max_daily_loss: float | None = None        # USD; el motor cierra la posición al tocarlo
    daily_profit_target: float | None = None   # USD; al alcanzarlo, no más entradas ese día
    max_consecutive_losses: int | None = None  # pérdidas seguidas que paran el día
    max_contracts: int | None = None           # tope de contratos por orden

    def entry_block_reason(self, trades_opened: int, realized: float, consecutive_losses: int) -> str | None:
        if self.max_trades is not None and trades_opened >= self.max_trades:
            return "max_operaciones"
        if self.max_daily_loss is not None and realized <= -self.max_daily_loss:
            return "limite_diario"
        if self.daily_profit_target is not None and realized >= self.daily_profit_target:
            return "objetivo_diario"
        if self.max_consecutive_losses is not None and consecutive_losses >= self.max_consecutive_losses:
            return "perdidas_seguidas"
        return None
