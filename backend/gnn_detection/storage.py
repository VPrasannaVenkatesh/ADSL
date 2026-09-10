"""
Database Storage for GNN Account and Network Assessments.
Upserts GNN predictions into gnn_account_assessments and gnn_network_assessments
tables across all three bank PostgreSQL databases using direct psycopg2.
"""

import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
import psycopg2


def save_gnn_account_assessment(
    conn: psycopg2.extensions.connection,
    account_id: str,
    bank: str,
    classification: str,
    mule_probability: float,
    suspicious_probability: float,
    normal_probability: float,
    gnn_risk_score: float,
    risk_level: str,
    network_pattern: str,
    connected_account_count: int,
    confidence: float,
    explanation: List[str],
    model_version: str = "v1.0.0-gatv2",
    trigger_transaction_id: Optional[str] = None,
) -> str:
    """
    Upserts a GNN account assessment record.
    If an assessment for this account already exists, updates it.
    Returns the assessment_id.
    """
    assessment_id    = f"GNN_{uuid.uuid4().hex[:12].upper()}"
    explanation_json = json.dumps(explanation or [])

    try:
        with conn.cursor() as cur:
            # Upsert: update if recent record exists (within last hour)
            cur.execute("""
                SELECT assessment_id FROM gnn_account_assessments
                WHERE account_id = %s
                  AND created_at >= NOW() - INTERVAL '1 hour'
                LIMIT 1
            """, (account_id,))
            existing = cur.fetchone()

            if existing:
                existing_id = existing[0]
                cur.execute("""
                    UPDATE gnn_account_assessments SET
                        classification         = %s,
                        mule_probability       = %s,
                        suspicious_probability = %s,
                        normal_probability     = %s,
                        gnn_risk_score         = %s,
                        risk_level             = %s,
                        network_pattern        = %s,
                        connected_account_count = %s,
                        confidence             = %s,
                        explanation            = %s::jsonb,
                        model_version          = %s,
                        trigger_transaction_id = COALESCE(%s, trigger_transaction_id),
                        updated_at             = NOW()
                    WHERE assessment_id = %s
                """, (
                    classification, float(mule_probability), float(suspicious_probability),
                    float(normal_probability), float(gnn_risk_score), risk_level,
                    network_pattern, int(connected_account_count), float(confidence),
                    explanation_json, model_version, trigger_transaction_id, existing_id
                ))
                conn.commit()
                return existing_id
            else:
                cur.execute("""
                    INSERT INTO gnn_account_assessments (
                        assessment_id, account_id, bank,
                        classification, mule_probability, suspicious_probability,
                        normal_probability, gnn_risk_score, risk_level,
                        network_pattern, connected_account_count, confidence,
                        explanation, model_version, trigger_transaction_id
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s
                    )
                """, (
                    assessment_id, account_id, bank,
                    classification, float(mule_probability), float(suspicious_probability),
                    float(normal_probability), float(gnn_risk_score), risk_level,
                    network_pattern, int(connected_account_count), float(confidence),
                    explanation_json, model_version, trigger_transaction_id
                ))
                conn.commit()
                return assessment_id
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        print(f"[GNN Storage] save_gnn_account_assessment error: {e}")
        return assessment_id


def save_gnn_network_assessment(
    conn: psycopg2.extensions.connection,
    trigger_transaction_id: str,
    node_count: int,
    edge_count: int,
    mule_accounts_detected: int,
    suspicious_accounts_detected: int,
    network_pattern: str,
    network_risk_score: float,
    node_classifications: Dict[str, Any],
) -> str:
    """Inserts a network-level GNN assessment record."""
    network_id = f"NET_{uuid.uuid4().hex[:12].upper()}"
    node_cls_json = json.dumps(node_classifications or {})

    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO gnn_network_assessments (
                    network_id, trigger_transaction_id,
                    node_count, edge_count,
                    mule_accounts_detected, suspicious_accounts_detected,
                    network_pattern, network_risk_score, node_classifications
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                ON CONFLICT (network_id) DO NOTHING
            """, (
                network_id, trigger_transaction_id,
                node_count, edge_count,
                mule_accounts_detected, suspicious_accounts_detected,
                network_pattern, float(network_risk_score), node_cls_json
            ))
            conn.commit()
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        print(f"[GNN Storage] save_gnn_network_assessment error: {e}")

    return network_id


def fetch_gnn_flagged_accounts(
    conns: Dict[str, psycopg2.extensions.connection],
    bank: str = "ALL",
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Fetches recent GNN flagged accounts (SUSPICIOUS or MULE) from all/specified bank DB."""
    results = []
    banks_to_query = list(conns.keys()) if bank == "ALL" else [bank]

    for b in banks_to_query:
        if b not in conns:
            continue
        conn = conns[b]
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        assessment_id, account_id, bank, classification,
                        mule_probability, gnn_risk_score, risk_level,
                        network_pattern, connected_account_count, confidence,
                        explanation, trigger_transaction_id, created_at
                    FROM gnn_account_assessments
                    WHERE classification IN ('SUSPICIOUS', 'MULE')
                      AND bank = %s
                    ORDER BY gnn_risk_score DESC, created_at DESC
                    LIMIT %s
                """, (b, limit))
                rows = cur.fetchall()
                for row in rows:
                    results.append({
                        "assessment_id":             row[0],
                        "account_id":                row[1],
                        "bank":                      row[2],
                        "classification":            row[3],
                        "mule_probability":          float(row[4] or 0),
                        "gnn_risk_score":            float(row[5] or 0),
                        "risk_level":                row[6],
                        "network_pattern":           row[7],
                        "connected_account_count":   int(row[8] or 0),
                        "confidence":                float(row[9] or 0),
                        "explanation":               row[10] if isinstance(row[10], list) else [],
                        "trigger_transaction_id":    row[11],
                        "created_at":                row[12].isoformat() if row[12] else None,
                    })
        except Exception as e:
            print(f"[GNN Storage] fetch_gnn_flagged_accounts error ({b}): {e}")

    # Sort merged results by risk score desc
    results.sort(key=lambda r: r["gnn_risk_score"], reverse=True)
    return results[:limit]


def fetch_gnn_network_summary(
    conns: Dict[str, psycopg2.extensions.connection],
) -> Dict[str, Any]:
    """Returns aggregate GNN network statistics across all bank databases."""
    total_mule        = 0
    total_suspicious  = 0
    total_normal      = 0
    total_networks    = 0
    total_mule_networks = 0

    for bank, conn in conns.items():
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT classification, COUNT(*) as cnt
                    FROM gnn_account_assessments
                    WHERE created_at >= NOW() - INTERVAL '24 hours'
                    GROUP BY classification
                """)
                for row in cur.fetchall():
                    cls, cnt = row
                    if cls == "MULE":
                        total_mule += int(cnt)
                    elif cls == "SUSPICIOUS":
                        total_suspicious += int(cnt)
                    elif cls == "NORMAL":
                        total_normal += int(cnt)

                cur.execute("""
                    SELECT COUNT(*), SUM(CASE WHEN mule_accounts_detected > 0 THEN 1 ELSE 0 END)
                    FROM gnn_network_assessments
                    WHERE created_at >= NOW() - INTERVAL '24 hours'
                """)
                row = cur.fetchone()
                if row and row[0]:
                    total_networks      += int(row[0] or 0)
                    total_mule_networks += int(row[1] or 0)
        except Exception:
            pass

    from network_monitoring.graph_engine import GLOBAL_NETWORK_GRAPH
    graph_summary = GLOBAL_NETWORK_GRAPH.get_summary_metrics()

    return {
        "total_graph_nodes":        graph_summary.get("total_accounts_in_graph", 0),
        "total_graph_edges":        graph_summary.get("total_transactions_in_graph", 0),
        "mule_accounts_24h":        total_mule,
        "suspicious_accounts_24h":  total_suspicious,
        "normal_accounts_24h":      total_normal,
        "total_gnn_assessments":    total_mule + total_suspicious + total_normal,
        "total_networks_analyzed":  total_networks,
        "mule_networks_detected":   total_mule_networks,
    }
