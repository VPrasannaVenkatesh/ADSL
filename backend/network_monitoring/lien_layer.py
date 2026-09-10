"""
Controlled Funds & Lien Protection Layer (Module 14).
For transactions requiring restriction, places controlled liens or holds on funds
without deleting transaction records or mutating underlying customer histories.
Supports amount-level protection and maintains auditable restriction records.
"""

import uuid
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional

STATUS_RESTRICTED = "RESTRICTED"
STATUS_ON_HOLD = "ON_HOLD"
STATUS_LIEN = "LIEN"
STATUS_RELEASED = "RELEASED"

LIEN_STATUSES = [STATUS_RESTRICTED, STATUS_ON_HOLD, STATUS_LIEN, STATUS_RELEASED]


class ControlledFundsLienLayer:
    """
    Manages active liens and holds on suspicious transaction amounts.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self.active_liens: Dict[str, Dict[str, Any]] = {}
        self.liens_by_account: Dict[str, List[str]] = {}
        self.liens_by_tx: Dict[str, str] = {}

    def place_lien(
        self,
        transaction_id: str,
        account_id: str,
        bank: str,
        amount: int,
        reason: str,
        lien_type: str = STATUS_LIEN,
        risk_score: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Places a controlled hold/lien on a specific transaction amount.
        Returns the formal immutable lien receipt.
        """
        with self._lock:
            # Check if lien already exists for this tx
            if transaction_id in self.liens_by_tx:
                existing_id = self.liens_by_tx[transaction_id]
                return self.active_liens[existing_id]

            lien_id = f"LIEN_{uuid.uuid4().hex[:10].upper()}"
            receipt = {
                "lien_id": lien_id,
                "transaction_id": transaction_id,
                "account_id": account_id,
                "bank": bank,
                "amount": amount,
                "status": "UNDER_REVIEW",
                "lien_status": lien_type if lien_type in LIEN_STATUSES else STATUS_LIEN,
                "restriction_reason": reason,
                "risk_score": round(risk_score, 2),
                "restricted_at": datetime.now().isoformat(),
                "release_condition": "Requires Senior Compliance Review and AML Officer Approval",
                "is_active": True,
            }

            self.active_liens[lien_id] = receipt
            self.liens_by_tx[transaction_id] = lien_id

            if account_id not in self.liens_by_account:
                self.liens_by_account[account_id] = []
            self.liens_by_account[account_id].append(lien_id)

            return receipt

    def release_lien(self, lien_id: str, investigator_id: str, reason: str) -> Optional[Dict[str, Any]]:
        """
        Releases an active lien after investigation clearance.
        """
        with self._lock:
            if lien_id not in self.active_liens:
                return None
            lien = self.active_liens[lien_id]
            lien["status"] = "RELEASED"
            lien["lien_status"] = STATUS_RELEASED
            lien["is_active"] = False
            lien["released_at"] = datetime.now().isoformat()
            lien["released_by"] = investigator_id
            lien["release_reason"] = reason
            return lien

    def update_lien_status(
        self,
        identifier: str,
        new_status: str,
        investigator_id: str = "ADMIN_INVESTIGATOR",
        reason: str = "Admin Investigation Action",
    ) -> Optional[Dict[str, Any]]:
        """
        Updates the lien status based on ADSL admin actions.
        Supports: RELEASED, MONITORING, RESTRICTED, FROZEN.
        """
        with self._lock:
            target_id = self.liens_by_tx.get(identifier, identifier)
            if target_id not in self.active_liens:
                return None
            lien = self.active_liens[target_id]
            lien["status"] = new_status
            lien["lien_status"] = new_status
            lien["updated_at"] = datetime.now().isoformat()
            lien["action_by"] = investigator_id
            lien["action_notes"] = reason
            if new_status == STATUS_RELEASED or new_status == "COMPLETED":
                lien["is_active"] = False
                lien["released_at"] = datetime.now().isoformat()
            return lien

    def get_all_active_liens(self) -> List[Dict[str, Any]]:
        """Returns all liens currently active or under review."""
        with self._lock:
            return [l for l in self.active_liens.values() if l.get("is_active", False)]

    def get_account_balance_breakdown(self, account_id: str, current_balance: int) -> Dict[str, Any]:
        """
        Calculates clear distinction between Current Balance, Protected Lien Amount, and Available Balance.
        """
        with self._lock:
            active_ids = self.liens_by_account.get(account_id, [])
            total_lien_amount = 0
            active_liens = []
            for lid in active_ids:
                lien = self.active_liens.get(lid)
                if lien and lien.get("is_active", False) and lien.get("status") in ("UNDER_REVIEW", "RESTRICTED", "FROZEN"):
                    total_lien_amount += int(lien.get("amount", 0))
                    active_liens.append(lien)

            avail = max(0, current_balance - total_lien_amount)
            return {
                "account_id": account_id,
                "current_balance": current_balance,
                "active_lien_amount": total_lien_amount,
                "available_balance": avail,
                "active_lien_count": len(active_liens),
                "is_transfer_blocked": avail <= 0,
                "active_liens": active_liens,
            }

    def get_liens_for_account(self, account_id: str) -> List[Dict[str, Any]]:
        """Returns all liens associated with an account."""
        with self._lock:
            lien_ids = self.liens_by_account.get(account_id, [])
            return [self.active_liens[lid] for lid in lien_ids if lid in self.active_liens]

    def get_lien_history(
        self,
        limit: int = 150,
        status: Optional[str] = None,
        bank: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Returns comprehensive total history of all liens recorded across banks.
        Supports filtering by status (ACTIVE, RELEASED, RESTRICTED, FROZEN, UNDER_REVIEW),
        bank (SBI, AXIS, IOB), or keyword search (tx_id, account_id, lien_id).
        """
        with self._lock:
            all_list = list(self.active_liens.values())
            # Sort latest first
            all_list.reverse()

            filtered = []
            for item in all_list:
                if status and status.upper() != "ALL":
                    item_st = (item.get("status") or item.get("lien_status") or "").upper()
                    if status.upper() == "ACTIVE" and not item.get("is_active"):
                        continue
                    if status.upper() != "ACTIVE" and status.upper() not in item_st:
                        continue

                if bank and bank.upper() != "ALL":
                    if (item.get("bank") or "").upper() != bank.upper():
                        continue

                if search:
                    s_lower = search.lower()
                    haystack = f"{item.get('lien_id', '')} {item.get('transaction_id', '')} {item.get('account_id', '')} {item.get('restriction_reason', '')}".lower()
                    if s_lower not in haystack:
                        continue

                filtered.append(item)
                if len(filtered) >= limit:
                    break

            return filtered

    def get_summary_metrics(self) -> Dict[str, Any]:
        """Returns aggregate lien layer statistics and full active/historical lien dossier."""
        with self._lock:
            all_items = list(self.active_liens.values())
            active = [l for l in all_items if l.get("is_active", False)]
            released = [l for l in all_items if not l.get("is_active", False) or l.get("status") == "RELEASED"]
            restricted = [l for l in all_items if l.get("status") == "RESTRICTED"]
            frozen = [l for l in all_items if l.get("status") == "FROZEN"]

            total_held_amount = sum(l.get("amount", 0) for l in active)
            total_released_amount = sum(l.get("amount", 0) for l in released)

            # Latest 150 items for UI history
            recent_sorted = list(reversed(all_items))[:150]

            return {
                "total_liens_recorded": len(all_items),
                "active_liens_count": len(active),
                "released_liens_count": len(released),
                "restricted_liens_count": len(restricted),
                "frozen_liens_count": len(frozen),
                "total_held_amount": total_held_amount,
                "total_released_amount": total_released_amount,
                "recent_liens": recent_sorted,
                "all_liens": recent_sorted,
            }


# Singleton Global Lien Layer
GLOBAL_LIEN_LAYER = ControlledFundsLienLayer()
