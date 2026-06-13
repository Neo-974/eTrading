#!/usr/bin/env python3
"""
Bridge MetaTrader 5 <-> backend Node.js.
Lit une requete JSON sur stdin, execute la commande, renvoie le resultat sur stdout.
Compatible VTMarkets (serveurs MT5 standard).
Installation : pip install MetaTrader5
"""
import sys
import json

try:
    import MetaTrader5 as mt5
except ImportError:
    print(json.dumps({"error": "Package MetaTrader5 non installe (pip install MetaTrader5)"}))
    sys.exit(0)

TIMEFRAMES = {
    "M1": mt5.TIMEFRAME_M1, "M5": mt5.TIMEFRAME_M5, "M15": mt5.TIMEFRAME_M15,
    "M30": mt5.TIMEFRAME_M30, "H1": mt5.TIMEFRAME_H1, "H4": mt5.TIMEFRAME_H4,
    "D1": mt5.TIMEFRAME_D1,
}


def _init(req):
    login = req.get("login")
    password = req.get("password")
    server = req.get("server")
    if login and password and server:
        ok = mt5.initialize(login=int(login), password=password, server=server)
    else:
        ok = mt5.initialize()
    if not ok:
        raise RuntimeError(f"initialize() a echoue: {mt5.last_error()}")


def cmd_connect(req): return {"connected": True}


def cmd_account_info(req):
    info = mt5.account_info()
    if info is None: raise RuntimeError("account_info indisponible")
    return {"balance": info.balance, "equity": info.equity, "currency": info.currency}


def cmd_price(req):
    symbol = req["args"]["symbol"]
    mt5.symbol_select(symbol, True)
    tick = mt5.symbol_info_tick(symbol)
    info = mt5.symbol_info(symbol)
    if tick is None or info is None: raise RuntimeError(f"Symbole {symbol} indisponible")
    return {"symbol": symbol, "bid": tick.bid, "ask": tick.ask, "point": info.point}


def cmd_rates(req):
    a = req["args"]
    symbol = a["symbol"]
    timeframe = TIMEFRAMES.get(a.get("timeframe", "M15"), mt5.TIMEFRAME_M15)
    count = int(a.get("count", 100))
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
    if rates is None: raise RuntimeError(f"Pas de donnees pour {symbol}")
    candles = [{"time": int(r[0]) * 1000, "open": r[1], "high": r[2], "low": r[3], "close": r[4]} for r in rates]
    return {"candles": candles}


def cmd_open(req):
    a = req["args"]
    symbol = a["symbol"]
    mt5.symbol_select(symbol, True)
    tick = mt5.symbol_info_tick(symbol)
    order_type = mt5.ORDER_TYPE_BUY if a["action"] == "BUY" else mt5.ORDER_TYPE_SELL
    price = tick.ask if a["action"] == "BUY" else tick.bid
    request = {
        "action": mt5.TRADE_ACTION_DEAL, "symbol": symbol, "volume": float(a["volume"]),
        "type": order_type, "price": price, "sl": float(a["sl"]), "tp": float(a["tp"]),
        "deviation": 20, "magic": 20240612, "comment": a.get("comment", "neotechno"),
        "type_time": mt5.ORDER_TIME_GTC, "type_filling": mt5.ORDER_FILLING_FOK,
    }
    result = mt5.order_send(request)
    if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
        raise RuntimeError(f"order_send echoue: {getattr(result, 'comment', mt5.last_error())}")
    return {"ticket": result.order, "symbol": symbol, "action": a["action"],
            "volume": float(a["volume"]), "open_price": price, "sl": float(a["sl"]), "tp": float(a["tp"])}


def cmd_close(req):
    ticket = int(req["args"]["ticket"])
    positions = mt5.positions_get(ticket=ticket)
    if not positions: raise RuntimeError(f"Position {ticket} introuvable")
    pos = positions[0]
    tick = mt5.symbol_info_tick(pos.symbol)
    if pos.type == mt5.ORDER_TYPE_BUY:
        order_type = mt5.ORDER_TYPE_SELL; price = tick.bid
    else:
        order_type = mt5.ORDER_TYPE_BUY; price = tick.ask
    request = {
        "action": mt5.TRADE_ACTION_DEAL, "symbol": pos.symbol, "volume": pos.volume,
        "type": order_type, "position": ticket, "price": price,
        "deviation": 20, "magic": 20240612, "comment": "neotechno close",
        "type_time": mt5.ORDER_TIME_GTC, "type_filling": mt5.ORDER_FILLING_FOK,
    }
    result = mt5.order_send(request)
    if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
        raise RuntimeError(f"close echoue: {getattr(result, 'comment', mt5.last_error())}")
    return {"ticket": ticket, "profit": pos.profit, "close_price": price}


def cmd_open_trades(req):
    positions = mt5.positions_get()
    trades = []
    for p in (positions or []):
        trades.append({"ticket": p.ticket, "symbol": p.symbol,
                       "action": "BUY" if p.type == mt5.ORDER_TYPE_BUY else "SELL",
                       "volume": p.volume, "open_price": p.price_open,
                       "sl": p.sl, "tp": p.tp, "profit": p.profit})
    return {"trades": trades}


COMMANDS = {
    "connect": cmd_connect, "account_info": cmd_account_info, "price": cmd_price,
    "rates": cmd_rates, "open": cmd_open, "close": cmd_close, "open_trades": cmd_open_trades,
}


def main():
    raw = sys.stdin.read()
    try:
        req = json.loads(raw)
    except Exception as e:
        print(json.dumps({"error": f"JSON invalide: {e}"})); return
    command = req.get("command")
    handler = COMMANDS.get(command)
    if handler is None:
        print(json.dumps({"error": f"Commande inconnue: {command}"})); return
    try:
        _init(req)
        result = handler(req)
        print(json.dumps(result))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    main()
