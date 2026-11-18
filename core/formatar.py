"""Formatação de números no padrão brasileiro."""


def br(x, casas: int = 2) -> str:
    """1234.5 → '1.234,50'."""
    if x is None:
        return "—"
    try:
        v = float(x)
        if round(v, casas) == 0:
            v = 0.0  # evita "-0,00"
        s = f"{v:,.{casas}f}"
    except (TypeError, ValueError):
        return str(x)
    return s.replace(",", "X").replace(".", ",").replace("X", ".")
