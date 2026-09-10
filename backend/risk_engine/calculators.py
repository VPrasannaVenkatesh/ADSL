"""
Risk Component Calculators.
Computes 8 independent behavioral risk components (0 to 100) and explainable reasons.
"""

from typing import Dict, Any, Tuple, List


def calculate_amount_risk(features: Dict[str, Any]) -> Tuple[float, List[str]]:
    """
    Evaluates amount anomalies against account's historical average and current balance.
    """
    reasons = []
    score = 0.0

    curr_tx = features["current_tx"]
    account = features["account"]
    baseline = features["historical_baseline"]

    amount = curr_tx["amount"]
    balance = account["current_balance"]
    hist_avg = baseline["hist_avg_amount"]
    hist_max = baseline["hist_max_amount"]

    # 1. Multiplier over historical average amount
    if hist_avg > 0:
        multiplier = amount / hist_avg
        if multiplier >= 8.0:
            score += 45.0
            reasons.append(f"Transaction amount is {multiplier:.1f}x higher than historical average (₹{hist_avg:,})")
        elif multiplier >= 4.0:
            score += 30.0
            reasons.append(f"Amount is {multiplier:.1f}x higher than historical average")
        elif multiplier >= 2.5:
            score += 18.0
            reasons.append(f"Amount is {multiplier:.1f}x above average baseline")

    # 2. Exceeding historical maximum
    if amount > hist_max and hist_max > 0:
        score += 20.0
        reasons.append(f"Amount exceeds previous 90-day recorded maximum (₹{hist_max:,})")

    # 3. High balance depletion ratio (for SENDER)
    if curr_tx["role"] == "SENDER" and (balance + amount) > 0:
        drain_ratio = amount / (balance + amount)
        if drain_ratio >= 0.90:
            score += 35.0
            reasons.append(f"Transfer drains {drain_ratio*100:.0f}% of total available account balance")
        elif drain_ratio >= 0.70:
            score += 20.0
            reasons.append(f"High balance depletion ratio ({drain_ratio*100:.0f}% of funds)")

    return min(100.0, score), reasons


def calculate_velocity_risk(features: Dict[str, Any]) -> Tuple[float, List[str]]:
    """
    Evaluates short-term transaction frequency, velocity windows (1h, 6h), and intervals.
    """
    reasons = []
    score = 0.0

    today = features["today_behaviour"]
    tx_1h = today["transactions_1h"]
    tx_6h = today["transactions_6h"]
    min_interval = today["min_interval_sec"]
    avg_interval = today["avg_interval_sec"]

    # 1. Transactions within 1 hour
    if tx_1h >= 5:
        score += 50.0
        reasons.append(f"Severe transaction surge: {tx_1h} transactions executed in the last 1 hour")
    elif tx_1h >= 3:
        score += 30.0
        reasons.append(f"High velocity: {tx_1h} transactions in the last 1 hour")
    elif tx_1h == 2:
        score += 12.0

    # 2. Transactions within 6 hours
    if tx_6h >= 8:
        score += 25.0
        reasons.append(f"Heavy sustained activity: {tx_6h} transactions in 6-hour window")
    elif tx_6h >= 5:
        score += 15.0

    # 3. Unusually short interval between consecutive transactions
    if min_interval > 0 and min_interval <= 10:
        score += 35.0
        reasons.append(f"Rapid burst pattern: Consecutive transactions executed within {min_interval}s")
    elif min_interval > 0 and min_interval <= 45:
        score += 20.0
        reasons.append(f"Short transaction interval of {min_interval}s detected")

    return min(100.0, score), reasons


def calculate_behaviour_deviation_risk(features: Dict[str, Any]) -> Tuple[float, List[str]]:
    """
    Evaluates deviation from account's baseline daily volume and balance patterns.
    """
    reasons = []
    score = 0.0

    today = features["today_behaviour"]
    baseline = features["historical_baseline"]
    account = features["account"]

    today_count = today["transaction_count"]
    hist_avg_count = baseline["hist_avg_daily_tx_count"]
    account_age = account.get("account_age_days", 365)

    # 1. Surge relative to baseline daily count
    if hist_avg_count > 0:
        count_ratio = today_count / hist_avg_count
        if count_ratio >= 5.0 and today_count >= 4:
            score += 45.0
            reasons.append(f"Daily volume is {count_ratio:.1f}x higher than account historical baseline")
        elif count_ratio >= 3.0 and today_count >= 3:
            score += 25.0
            reasons.append(f"Volume is {count_ratio:.1f}x higher than normal baseline")

    # 2. Sudden activity on relatively dormant account
    if baseline["hist_active_days_count"] < 3 and today_count >= 2:
        score += 25.0
        reasons.append("Sudden burst of activity on historically dormant account")

    # 3. New account (< 30 days old) high volume
    if account_age <= 30 and today_count >= 3:
        score += 25.0
        reasons.append(f"High activity volume on relatively new account ({account_age} days old)")

    return min(100.0, score), reasons


def calculate_device_risk(features: Dict[str, Any]) -> Tuple[float, List[str]]:
    """
    Evaluates device novelty, device changes, and channel anomalies.
    """
    reasons = []
    score = 0.0

    today = features["today_behaviour"]
    curr_tx = features["current_tx"]

    new_dev = today["new_device_count"]
    dev_changes = today["device_change_count"]
    primary_dev = today["primary_device"]
    current_dev_type = (curr_tx["device_ip"] or "").split(':')[0]

    # 1. New device detected
    if new_dev > 0:
        score += 40.0
        reasons.append(f"Transaction originating from an unrecognised device ({current_dev_type})")

    # 2. Multiple device switches in the same day
    if dev_changes >= 2:
        score += 35.0
        reasons.append(f"Multiple device switches observed today ({dev_changes} switches)")
    elif dev_changes == 1:
        score += 15.0

    # 3. Mismatch with primary device
    if primary_dev and current_dev_type and primary_dev != current_dev_type:
        score += 15.0
        reasons.append(f"Channel switch: Using {current_dev_type} instead of primary {primary_dev}")

    return min(100.0, score), reasons


def calculate_location_risk(features: Dict[str, Any]) -> Tuple[float, List[str]]:
    """
    Evaluates geographic movement, new cities, and location switches.
    """
    reasons = []
    score = 0.0

    today = features["today_behaviour"]
    curr_tx = features["current_tx"]
    account = features["account"]

    home_loc = account.get("home_location") or "Chennai"
    tx_loc = curr_tx.get("location") or home_loc
    new_loc_cnt = today["new_location_count"]
    loc_changes = today["location_change_count"]

    # 1. Different from registered home location
    if home_loc and tx_loc and home_loc.lower() != tx_loc.lower():
        score += 30.0
        reasons.append(f"Geographic deviation: Transacting from {tx_loc} (Registered Home: {home_loc})")

    # 2. Multiple location hops in one day
    if loc_changes >= 2:
        score += 35.0
        reasons.append(f"Rapid geographic mobility: {loc_changes} location changes recorded today")
    elif new_loc_cnt > 0:
        score += 20.0
        reasons.append(f"First-time activity observed from {tx_loc}")

    return min(100.0, score), reasons


def calculate_counterparty_risk(features: Dict[str, Any]) -> Tuple[float, List[str]]:
    """
    Evaluates counterparty novelty, unique counterparty dispersion, and relationship history.
    """
    reasons = []
    score = 0.0

    today = features["today_behaviour"]
    curr_tx = features["current_tx"]

    is_new_recip = curr_tx["recipient_is_new"]
    new_recip_cnt = today["new_recipients_count"]
    unique_recip = today["unique_recipients"]
    amount = curr_tx["amount"]

    # 1. First-time transfer to an unknown recipient
    if is_new_recip and curr_tx["role"] == "SENDER":
        if amount >= 25000:
            score += 40.0
            reasons.append(f"High-value transfer (₹{amount:,}) to a brand new beneficiary")
        else:
            score += 25.0
            reasons.append("First-time transaction with a new counterparty")

    # 2. Multiple new counterparties in single day
    if new_recip_cnt >= 3:
        score += 35.0
        reasons.append(f"High counterparty dispersion: {new_recip_cnt} new beneficiaries added today")
    elif unique_recip >= 4:
        score += 20.0
        reasons.append(f"Transacting with {unique_recip} distinct counterparties today")

    return min(100.0, score), reasons


def calculate_timing_risk(features: Dict[str, Any]) -> Tuple[float, List[str]]:
    """
    Evaluates off-hours activity, late night / early morning transactions.
    """
    reasons = []
    score = 0.0

    curr_tx = features["current_tx"]
    today = features["today_behaviour"]
    tx_time = curr_tx["timestamp"]
    hour = tx_time.hour
    night_count = today["night_count"]

    # 1. Late night / Early morning window (10 PM to 6 AM)
    if hour >= 23 or hour < 5:
        score += 40.0
        reasons.append(f"Unusual timing: Transaction initiated during late night window ({tx_time.strftime('%I:%M %p')})")
    elif hour == 22 or hour == 5:
        score += 25.0
        reasons.append(f"Off-peak timing: Transaction executed at {tx_time.strftime('%I:%M %p')}")

    # 2. Repeated night-time activity
    if night_count >= 3:
        score += 30.0
        reasons.append(f"Multiple night-time transactions recorded today ({night_count} night txns)")

    return min(100.0, score), reasons


def calculate_network_pattern_risk(features: Dict[str, Any]) -> Tuple[float, List[str]]:
    """
    Evaluates flow patterns: rapid forwarding, short dwell times, amount splitting,
    fan-in, fan-out, and repeated cross-bank transfers.
    """
    reasons = []
    score = 0.0

    today = features["today_behaviour"]
    short_dwell = today["short_dwell_count"]
    amount_split = today["amount_split_count"]
    fwd_count = today["same_day_forward_count"]
    fwd_amount = today["forwarded_amount"]
    fan_in = today["fan_in"]
    fan_out = today["fan_out"]
    cross_bank = today["cross_bank_count"]

    # 1. Short Dwell Time (Received & Forwarded in < 60 mins)
    if short_dwell >= 2:
        score += 55.0
        reasons.append(f"Repeated short dwell-time forwarding: Funds forwarded rapidly after credit ({short_dwell} occurrences)")
    elif short_dwell == 1:
        score += 35.0
        reasons.append("Short dwell-time: Account forwarded funds shortly after receiving credit")

    # 2. Amount Splitting / Smurfing Pattern
    if amount_split >= 2:
        score += 45.0
        reasons.append(f"Amount splitting: Inbound fund dispersed across multiple smaller outflows ({amount_split} times)")
    elif amount_split == 1:
        score += 25.0
        reasons.append("Amount splitting behavior: Large inflow broken into smaller transfers")

    # 3. Same-Day Rapid Forwarding Ratio
    if fwd_count > 0 and fwd_amount >= 10000:
        score += 30.0
        reasons.append(f"High pass-through volume: ₹{fwd_amount:,} forwarded on the same day")

    # 4. Aggregation (Fan-In) or Dispersion (Fan-Out)
    if fan_in >= 3 and fan_out >= 2:
        score += 40.0
        reasons.append(f"Hub relay pattern: High aggregation ({fan_in} senders) and dispersion ({fan_out} recipients)")
    elif fan_in >= 3:
        score += 25.0
        reasons.append(f"Fan-in collection: Receiving transfers from {fan_in} distinct accounts")
    elif fan_out >= 3:
        score += 25.0
        reasons.append(f"Fan-out distribution: Sending funds to {fan_out} distinct accounts")

    # 5. Frequent Cross-Bank Transfers
    if cross_bank >= 3:
        score += 20.0
        reasons.append(f"Frequent cross-bank movement: {cross_bank} inter-bank transfers today")

    return min(100.0, score), reasons
