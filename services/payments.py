"""Paid tier (Pro). Works with Easypaisa / JazzCash by hand-check:
student pays -> sends the transaction ID -> admin checks the money arrived -> admin approves -> Pro starts.
"""
import re
import sqlite3
import uuid

import requests

from . import config, db

METHODS = ["Easypaisa", "JazzCash"]


def payment_instructions() -> dict:
    return {
        "price": config.PRO_PRICE_PKR,
        "days": config.PRO_DAYS,
        "account_name": config.PAY_ACCOUNT_NAME,
        "numbers": {
            "Easypaisa": config.PAY_EASYPAISA_NUMBER,
            "JazzCash": config.PAY_JAZZCASH_NUMBER,
        },
    }


def submit_payment(email: str, method: str, amount: int, txn_ref: str, sender: str):
    """Returns (ok, message)."""
    if method not in METHODS:
        return False, "Please choose a payment method."
    txn_ref = (txn_ref or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9\-]{6,40}", txn_ref):
        return False, "The transaction ID should be 6 to 40 letters or numbers."
    if int(amount) < config.PRO_PRICE_PKR:
        return False, f"The amount must be at least Rs {config.PRO_PRICE_PKR}."
    if not re.fullmatch(r"[0-9+\- ]{10,16}", (sender or "").strip()):
        return False, "Please enter the phone number you paid from."
    try:
        db.add_payment(email, method, amount, txn_ref, sender)
    except sqlite3.IntegrityError:
        return False, "This transaction ID was already sent."
    return True, "Thank you. We will check your payment and turn on Pro soon."


def approve(payment_id: int):
    """Admin: mark paid and give Pro days. Returns (ok, message)."""
    p = db.get_payment(payment_id)
    if not p or p["status"] != "pending":
        return False, "This payment is not waiting."
    db.set_payment_status(payment_id, "approved")
    end = db.grant_pro(p["email"], config.PRO_DAYS)
    return True, f"Pro is on for {p['email']} until {end.strftime('%d %b %Y')}."


def reject(payment_id: int):
    db.set_payment_status(payment_id, "rejected")
    return True, "Payment rejected."


def create_safepay_checkout(email: str, amount_pkr: int) -> str:
    """UNTESTED. Best-effort Safepay checkout link."""
    if not config.SAFEPAY_PUBLIC_KEY:
        raise RuntimeError("Set SAFEPAY_PUBLIC_KEY in .env first.")
    sandbox = config.SAFEPAY_ENV == "sandbox"
    base = "https://sandbox.api.getsafepay.com" if sandbox else "https://api.getsafepay.com"
    resp = requests.post(
        f"{base}/order/v1/init",
        json={"client": config.SAFEPAY_PUBLIC_KEY, "amount": amount_pkr, "currency": "PKR",
              "environment": "sandbox" if sandbox else "production"},
        timeout=20,
    )
    resp.raise_for_status()
    token = resp.json()["data"]["token"]
    return (f"{base}/checkout/pay?env={'sandbox' if sandbox else 'production'}"
            f"&beacon={token}&source=custom&order_id={uuid.uuid4().hex}")