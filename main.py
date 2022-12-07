import csv
import sys
from enum import Enum


class TradeEnum(Enum):
    SELL = "S"
    BUY = "B"


class BookingSummary:
    def __init__(
        self,
        open_time,
        close_time,
        symbol,
        quantity,
        pnl,
        open_side,
        close_side,
        open_price,
        close_price,
    ) -> None:
        self.open_time = open_time
        self.close_time = close_time
        self.symbol = symbol
        self.quantity = quantity
        self.pnl = pnl
        self.open_side = open_side
        self.close_side = close_side
        self.open_price = open_price
        self.close_price = close_price


class Booking:
    def __init__(self, time, symbol, side, price, quantity) -> None:
        self.time = time
        self.symbol = symbol
        self.side = side
        self.price = price
        self.quantity = quantity


# # assumed trades are sorted w.r.t time
trade_data = []
booking_history = {}
booking_summary = []


def calculate_trade(buy_data, sell_data, short_selling=False):

    if short_selling:
        pnl = round(
            (buy_data["price"] - sell_data["price"])
            * min(buy_data["quantity"], sell_data["quantity"]),
            2,
        )
    else:
        pnl = round(
            (sell_data["price"] - buy_data["price"])
            * min(buy_data["quantity"], sell_data["quantity"]),
            2,
        )

    booking_summary.append(
        BookingSummary(
            open_time=buy_data["time"],
            close_time=sell_data["time"],
            symbol=sell_data["symbol"],
            quantity=min(buy_data["quantity"], sell_data["quantity"]),
            pnl=pnl,
            open_side=buy_data["side"],
            close_side=sell_data["side"],
            open_price=buy_data["price"],
            close_price=sell_data["price"],
        )
    )


def calculate_average_price(old_price, new_price):
    return round((old_price + new_price) / 2, 4)


try:
    file_name = sys.argv[1]
except:
    raise Exception("Please Provide filename")

if file_name:
    with open(file_name, mode="r") as file:

        # reading the CSV file
        csvFile = csv.DictReader(file)

        # displaying the contents of the CSV file
        for lines in csvFile:
            trade_data.append(
                Booking(
                    time=lines["TIME"],
                    symbol=lines["SYMBOL"],
                    side=lines["SIDE"],
                    price=float(lines["PRICE"]),
                    quantity=int(lines["QUANTITY"]),
                )
            )

    for trade in trade_data:
        trade = trade.__dict__

        booking_hash_key = str(trade["symbol"])

        if trade["side"] == TradeEnum.BUY.value:

            if booking_hash_key in booking_history:
                if booking_history[booking_hash_key]["side"] == TradeEnum.SELL.value:
                    if booking_history[booking_hash_key]["quantity"]:
                        calculate_trade(
                            buy_data=booking_history[booking_hash_key],
                            sell_data=trade,
                            short_selling=True,
                        )
                        booking_history[booking_hash_key]["quantity"] -= trade[
                            "quantity"
                        ]

                        if booking_history[booking_hash_key]["quantity"] == 0:
                            # Previous Sell - Buy trade has been completely consumed
                            del booking_history[booking_hash_key]
                        elif booking_history[booking_hash_key]["quantity"] < 0:
                            # Previous Sell - Buy Trade has been closed, Creating a new Buy Order
                            booking_history[booking_hash_key][
                                "side"
                            ] = TradeEnum.BUY.value
                            booking_history[booking_hash_key]["time"] = trade["time"]
                            booking_history[booking_hash_key]["quantity"] = abs(
                                booking_history[booking_hash_key]["quantity"]
                            )
                            booking_history[booking_hash_key]["price"] = trade["price"]

                        # print(
                        #     "booking_history[booking_hash_key]",
                        #     booking_history[booking_hash_key],
                        # )

                elif booking_history[booking_hash_key]["side"] == TradeEnum.BUY.value:
                    # print("I reached here")
                    old_price = booking_history[booking_hash_key]["price"]
                    new_price = trade["price"]
                    old_quantity = booking_history[booking_hash_key]["quantity"]
                    new_quantity = trade["quantity"]

                    average_price = calculate_average_price(
                        old_price=old_price, new_price=new_price
                    )
                    booking_history[booking_hash_key]["quantity"] = (
                        old_quantity + new_quantity
                    )
                    booking_history[booking_hash_key]["price"] = average_price
                    # print(booking_history)

            elif booking_hash_key not in booking_history:
                booking_history[str(booking_hash_key)] = trade

        elif trade["side"] == TradeEnum.SELL.value:
            # Case buy first and sell second
            if booking_hash_key in booking_history:
                if booking_history[booking_hash_key]["side"] == TradeEnum.BUY.value:
                    buy_order_data = booking_history[booking_hash_key]
                    if booking_history[booking_hash_key]["quantity"]:
                        calculate_trade(buy_data=buy_order_data, sell_data=trade)
                        booking_history[booking_hash_key]["quantity"] -= trade[
                            "quantity"
                        ]
                        if booking_history[booking_hash_key]["quantity"] == 0:
                            del booking_history[booking_hash_key]

                        elif booking_history[booking_hash_key]["quantity"] < 0:
                            # Previous Sell - Buy Trade has been closed, Creating a new Buy Order
                            booking_history[booking_hash_key][
                                "side"
                            ] = TradeEnum.SELL.value
                            booking_history[booking_hash_key]["time"] = trade["time"]
                            booking_history[booking_hash_key]["quantity"] = abs(
                                booking_history[booking_hash_key]["quantity"]
                            )
                            booking_history[booking_hash_key]["price"] = trade["price"]

                elif booking_history[booking_hash_key]["side"] == TradeEnum.SELL.value:
                    old_price = booking_history[booking_hash_key]["price"]
                    new_price = trade["price"]
                    old_quantity = booking_history[booking_hash_key]["quantity"]
                    new_quantity = trade["quantity"]

                    average_price = calculate_average_price(
                        old_price=old_price, new_price=new_price
                    )
                    booking_history[booking_hash_key]["quantity"] = (
                        old_quantity + new_quantity
                    )
                    booking_history[booking_hash_key]["price"] = average_price

            elif booking_hash_key not in booking_history:
                booking_history[str(booking_hash_key)] = trade

result_booking_summary = [summary.__dict__ for summary in booking_summary]
print(result_booking_summary)
