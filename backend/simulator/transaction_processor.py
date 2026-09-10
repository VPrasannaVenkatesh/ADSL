"""
Transaction execution engine for intra-bank and cross-bank operations.
Maintains atomic PostgreSQL transactions, balance constraints, and behaviour updates.
"""

import uuid
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, Optional
import psycopg2
from .account_manager import AccountManager
from .behaviour_updater import update_account_behaviour


@dataclass
class TransactionResult:
    transaction_id: str
    sender_bank: str
    sender_account_id: str
    receiver_bank: str
    receiver_account_id: str
    amount: int
    transaction_type: str
    transaction_timestamp: datetime
    device_ip: str
    location: str
    recipient_is_new: bool
    sender_bal_before: int
    sender_bal_after: int
    receiver_bal_before: int
    receiver_bal_after: int
    is_cross_bank: bool
    status: str = "COMPLETED"


class TransactionProcessor:
    def __init__(self, conns: Dict[str, psycopg2.extensions.connection], account_mgr: AccountManager):
        self.conns = conns
        self.account_mgr = account_mgr

    def execute_transaction(
        self,
        sender: dict,
        receiver: dict,
        amount: int,
        tx_type: str,
        timestamp: datetime,
        device_ip: str,
        location: str,
        recipient_is_new: bool,
    ) -> Optional[TransactionResult]:
        """
        Executes a single banking transaction with atomic balance updates and
        dynamic behavioural profile recalculation.
        """
        sender_bank = sender["bank"]
        receiver_bank = receiver["bank"]
        is_cross_bank = (sender_bank != receiver_bank)
        tx_id = f"TXN_LIVE_{uuid.uuid4().hex[:12].upper()}"

        if not is_cross_bank:
            # ── Same-Bank Transaction (Intra-Bank) ────────────────────────────
            conn = self.conns[sender_bank]
            try:
                with conn.cursor() as cur:
                    # Lock and verify sender balance
                    cur.execute("""
                        SELECT current_balance FROM accounts
                        WHERE account_id = %s FOR UPDATE
                    """, (sender["account_id"],))
                    s_row = cur.fetchone()
                    if not s_row or s_row[0] < amount:
                        conn.rollback()
                        return None
                    s_before = int(s_row[0])
                    s_after = s_before - amount

                    # Lock receiver balance
                    cur.execute("""
                        SELECT current_balance FROM accounts
                        WHERE account_id = %s FOR UPDATE
                    """, (receiver["account_id"],))
                    r_row = cur.fetchone()
                    if not r_row:
                        conn.rollback()
                        return None
                    r_before = int(r_row[0])
                    r_after = r_before + amount

                    # Update sender balance
                    cur.execute("""
                        UPDATE accounts
                        SET current_balance = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE account_id = %s
                    """, (s_after, sender["account_id"]))

                    # Update receiver balance
                    cur.execute("""
                        UPDATE accounts
                        SET current_balance = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE account_id = %s
                    """, (r_after, receiver["account_id"]))

                    # Insert transaction log
                    cur.execute("""
                        INSERT INTO transactions (
                            transaction_id, sender_account_id, sender_bank,
                            receiver_account_id, receiver_bank,
                            amount, transaction_timestamp, transaction_type,
                            sender_balance_before, sender_balance_after,
                            receiver_balance_before, receiver_balance_after,
                            device_ip, location, recipient_is_new,
                            transaction_status, simulation_source
                        ) VALUES (
                            %s, %s, %s, %s, %s,
                            %s, %s, %s,
                            %s, %s, %s, %s,
                            %s, %s, %s,
                            'COMPLETED', 'LIVE_SIMULATOR'
                        )
                    """, (
                        tx_id, sender["account_id"], sender_bank,
                        receiver["account_id"], receiver_bank,
                        amount, timestamp, tx_type,
                        s_before, s_after, r_before, r_after,
                        device_ip, location, recipient_is_new
                    ))

                conn.commit()

                # Update in-memory caches
                self.account_mgr.update_balance_cache(sender["account_id"], s_after)
                self.account_mgr.update_balance_cache(receiver["account_id"], r_after)
                self.account_mgr.record_recent_recipient(receiver["account_id"], amount)

                # Dynamically update daily behaviour history for both parties
                txn_date = timestamp.date()
                update_account_behaviour(conn, sender_bank, sender["account_id"], txn_date)
                update_account_behaviour(conn, sender_bank, receiver["account_id"], txn_date)

                return TransactionResult(
                    transaction_id=tx_id,
                    sender_bank=sender_bank,
                    sender_account_id=sender["account_id"],
                    receiver_bank=receiver_bank,
                    receiver_account_id=receiver["account_id"],
                    amount=amount,
                    transaction_type=tx_type,
                    transaction_timestamp=timestamp,
                    device_ip=device_ip,
                    location=location,
                    recipient_is_new=recipient_is_new,
                    sender_bal_before=s_before,
                    sender_bal_after=s_after,
                    receiver_bal_before=r_before,
                    receiver_bal_after=r_after,
                    is_cross_bank=False,
                )

            except Exception as e:
                conn.rollback()
                raise e

        else:
            # ── Cross-Bank Transaction (Inter-Bank) ───────────────────────────
            s_conn = self.conns[sender_bank]
            r_conn = self.conns[receiver_bank]

            try:
                # 1. Debit from Sender Bank
                with s_conn.cursor() as s_cur:
                    s_cur.execute("""
                        SELECT current_balance FROM accounts
                        WHERE account_id = %s FOR UPDATE
                    """, (sender["account_id"],))
                    s_row = s_cur.fetchone()
                    if not s_row or s_row[0] < amount:
                        s_conn.rollback()
                        return None
                    s_before = int(s_row[0])
                    s_after = s_before - amount

                    s_cur.execute("""
                        UPDATE accounts
                        SET current_balance = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE account_id = %s
                    """, (s_after, sender["account_id"]))

                    s_cur.execute("""
                        INSERT INTO transactions (
                            transaction_id, sender_account_id, sender_bank,
                            receiver_account_id, receiver_bank,
                            amount, transaction_timestamp, transaction_type,
                            sender_balance_before, sender_balance_after,
                            receiver_balance_before, receiver_balance_after,
                            device_ip, location, recipient_is_new,
                            transaction_status, simulation_source
                        ) VALUES (
                            %s, %s, %s, %s, %s,
                            %s, %s, %s,
                            %s, %s, NULL, NULL,
                            %s, %s, %s,
                            'COMPLETED', 'LIVE_SIMULATOR'
                        )
                    """, (
                        tx_id, sender["account_id"], sender_bank,
                        receiver["account_id"], receiver_bank,
                        amount, timestamp, tx_type,
                        s_before, s_after,
                        device_ip, location, recipient_is_new
                    ))

                # 2. Credit to Receiver Bank
                with r_conn.cursor() as r_cur:
                    r_cur.execute("""
                        SELECT current_balance FROM accounts
                        WHERE account_id = %s FOR UPDATE
                    """, (receiver["account_id"],))
                    r_row = r_cur.fetchone()
                    if not r_row:
                        s_conn.rollback()
                        r_conn.rollback()
                        return None
                    r_before = int(r_row[0])
                    r_after = r_before + amount

                    r_cur.execute("""
                        UPDATE accounts
                        SET current_balance = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE account_id = %s
                    """, (r_after, receiver["account_id"]))

                    r_cur.execute("""
                        INSERT INTO transactions (
                            transaction_id, sender_account_id, sender_bank,
                            receiver_account_id, receiver_bank,
                            amount, transaction_timestamp, transaction_type,
                            sender_balance_before, sender_balance_after,
                            receiver_balance_before, receiver_balance_after,
                            device_ip, location, recipient_is_new,
                            transaction_status, simulation_source
                        ) VALUES (
                            %s, %s, %s, %s, %s,
                            %s, %s, %s,
                            NULL, NULL, %s, %s,
                            %s, %s, %s,
                            'COMPLETED', 'LIVE_SIMULATOR'
                        )
                    """, (
                        tx_id, sender["account_id"], sender_bank,
                        receiver["account_id"], receiver_bank,
                        amount, timestamp, tx_type,
                        r_before, r_after,
                        device_ip, location, recipient_is_new
                    ))

                # Commit both databases
                s_conn.commit()
                r_conn.commit()

                # Update in-memory caches
                self.account_mgr.update_balance_cache(sender["account_id"], s_after)
                self.account_mgr.update_balance_cache(receiver["account_id"], r_after)
                self.account_mgr.record_recent_recipient(receiver["account_id"], amount)

                # Dynamically update behaviour history on both bank DBs
                txn_date = timestamp.date()
                update_account_behaviour(s_conn, sender_bank, sender["account_id"], txn_date)
                update_account_behaviour(r_conn, receiver_bank, receiver["account_id"], txn_date)

                return TransactionResult(
                    transaction_id=tx_id,
                    sender_bank=sender_bank,
                    sender_account_id=sender["account_id"],
                    receiver_bank=receiver_bank,
                    receiver_account_id=receiver["account_id"],
                    amount=amount,
                    transaction_type=tx_type,
                    transaction_timestamp=timestamp,
                    device_ip=device_ip,
                    location=location,
                    recipient_is_new=recipient_is_new,
                    sender_bal_before=s_before,
                    sender_bal_after=s_after,
                    receiver_bal_before=r_before,
                    receiver_bal_after=r_after,
                    is_cross_bank=True,
                )

            except Exception as e:
                s_conn.rollback()
                r_conn.rollback()
                raise e
