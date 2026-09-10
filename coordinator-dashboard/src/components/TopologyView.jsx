import React from 'react';
import { Shield, Database, Cpu, ArrowRightLeft, Lock } from 'lucide-react';

export function TopologyView() {
  return (
    <div style={{
      margin: '0 24px 20px',
      background: 'var(--bg-card)',
      border: '1px solid var(--border)',
      borderRadius: 12,
      padding: '16px 20px',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Shield size={16} color="#8B5CF6" />
          <span style={{ fontSize: '0.78rem', fontWeight: 800, letterSpacing: '0.05em', color: 'var(--text-primary)', textTransform: 'uppercase' }}>
            Decentralized Privacy-Preserving Architecture
          </span>
        </div>
        <span style={{ fontSize: '0.7rem', color: '#10B981', display: 'flex', alignItems: 'center', gap: 5 }}>
          <Lock size={12} /> Zero PII & Private Balance Sharing
        </span>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: 12,
      }}>
        {/* SBI Bank */}
        <div style={{
          background: 'var(--bg-surface)',
          border: '1px solid #3B82F635',
          borderRadius: 8,
          padding: '10px 14px',
          borderLeft: '3px solid #3B82F6',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 800, color: '#3B82F6' }}>SBI NODE</span>
            <Database size={13} color="#3B82F6" />
          </div>
          <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: 2 }}>
            Database: <code>sbi_db</code> (Private)
          </div>
          <div style={{ fontSize: '0.68rem', color: 'var(--text-secondary)', marginTop: 4 }}>
            Local Risk Engine: <strong>Active</strong>
          </div>
        </div>

        {/* Coordinator Core */}
        <div style={{
          background: 'rgba(139, 92, 246, 0.10)',
          border: '1px solid rgba(139, 92, 246, 0.4)',
          borderRadius: 8,
          padding: '10px 14px',
          borderLeft: '3px solid #8B5CF6',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 800, color: '#A78BFA' }}>RISK COORDINATOR</span>
            <Cpu size={13} color="#A78BFA" />
          </div>
          <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: 2 }}>
            Storage: <code>coordinator.db</code> (Decoupled)
          </div>
          <div style={{ fontSize: '0.68rem', color: '#DDD6FE', marginTop: 4 }}>
            Targeted 2-Bank API Communication
          </div>
        </div>

        {/* AXIS Bank */}
        <div style={{
          background: 'var(--bg-surface)',
          border: '1px solid #EC489935',
          borderRadius: 8,
          padding: '10px 14px',
          borderLeft: '3px solid #EC4899',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 800, color: '#EC4899' }}>AXIS NODE</span>
            <Database size={13} color="#EC4899" />
          </div>
          <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: 2 }}>
            Database: <code>axis_db</code> (Private)
          </div>
          <div style={{ fontSize: '0.68rem', color: 'var(--text-secondary)', marginTop: 4 }}>
            Local Risk Engine: <strong>Active</strong>
          </div>
        </div>

        {/* IOB Bank */}
        <div style={{
          background: 'var(--bg-surface)',
          border: '1px solid #F59E0B35',
          borderRadius: 8,
          padding: '10px 14px',
          borderLeft: '3px solid #F59E0B',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 800, color: '#F59E0B' }}>IOB NODE</span>
            <Database size={13} color="#F59E0B" />
          </div>
          <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: 2 }}>
            Database: <code>iob_db</code> (Private)
          </div>
          <div style={{ fontSize: '0.68rem', color: 'var(--text-secondary)', marginTop: 4 }}>
            Local Risk Engine: <strong>Active</strong>
          </div>
        </div>
      </div>
    </div>
  );
}
