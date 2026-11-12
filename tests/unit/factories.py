from datetime import date, timedelta
from decimal import Decimal

from b3_ir.domain.models import Operation, Side


def op(
    day: date,
    ticker: str,
    side: Side,
    quantity: str,
    price: str,
    costs: str = "0",
    irrf: str = "0",
) -> Operation:
    return Operation(
        trade_date=day,
        settlement_date=day + timedelta(days=2),
        ticker=ticker,
        side=side,
        quantity=Decimal(quantity),
        unit_price=Decimal(price),
        costs=Decimal(costs),
        irrf=Decimal(irrf),
        source="sintetico",
    )
