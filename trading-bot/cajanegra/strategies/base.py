"""Interfaz de estrategia. Una estrategia solo puede mirar el pasado a través de `ctx`."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

if TYPE_CHECKING:
    from ..engine.backtest import Context


class Strategy:
    name: ClassVar[str] = "base"
    description: ClassVar[str] = ""
    defaults: ClassVar[dict[str, Any]] = {}

    def __init__(self, **params: Any):
        unknown = set(params) - set(self.defaults)
        if unknown:
            raise ValueError(
                f"Parámetros desconocidos para '{self.name}': {sorted(unknown)}. "
                f"Válidos: {sorted(self.defaults)}"
            )
        self.p: dict[str, Any] = {**self.defaults, **params}

    def on_day_start(self, ctx: "Context") -> None:
        """Se llama antes de la primera barra de cada sesión."""

    def on_bar(self, ctx: "Context") -> None:
        """Se llama al CIERRE de cada barra. Las órdenes se ejecutan desde la barra siguiente."""

    def __repr__(self) -> str:
        return f"{self.name}({', '.join(f'{k}={v}' for k, v in self.p.items())})"
