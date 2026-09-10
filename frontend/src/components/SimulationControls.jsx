import React from 'react';
import {
  Play,
  Pause,
  Square,
  Zap,
  Sliders,
  Layers,
  Sparkles,
  RefreshCw,
  Cpu,
} from 'lucide-react';

export function SimulationControls({
  status,
  onStart,
  onPause,
  onResume,
  onStop,
  onSetSpeed,
  onSetMix,
  onRefresh,
}) {
  const isRunning = status?.is_running && !status?.is_paused;
  const isPaused = status?.is_running && status?.is_paused;
  const isStopped = !status?.is_running;
  const currentSpeed = status?.mode || 'normal';
  const currentMix = status?.mix_mode || 'balanced';

  const mixModes = [
    { id: 'balanced', label: 'BALANCED MIX', desc: 'Realistic combination of Normal, Business & Mule' },
    { id: 'normal', label: 'NORMAL MIX', desc: 'UPI, NEFT, Utility & Personal transfers' },
    { id: 'business', label: 'BUSINESS MIX', desc: 'Commercial, Vendor, Payroll & B2B' },
    { id: 'mule', label: 'MULE MIX', desc: 'Fan-in, Fan-out, Rapid forwarding & Circular' },
  ];

  const speedModes = [
    { id: 'slow', label: 'SLOW' },
    { id: 'normal', label: 'NORMAL' },
    { id: 'fast', label: 'FAST' },
  ];

  return (
    <div className="glass-panel" style={{
      margin: '0 24px 16px 24px',
      padding: '14px 20px',
      display: 'flex',
      flexWrap: 'wrap',
      justifyContent: 'space-between',
      alignItems: 'center',
      gap: '16px',
      background: 'rgba(16, 22, 34, 0.75)',
      border: '1px solid var(--border-color)',
    }}>
      {/* Left: Section Label & Primary State Controls */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{
            width: '32px',
            height: '32px',
            borderRadius: '8px',
            background: 'rgba(0, 229, 255, 0.12)',
            border: '1px solid rgba(0, 229, 255, 0.3)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            <Sliders size={16} color="var(--accent-cyan)" />
          </div>
          <div>
            <div style={{ fontSize: '0.78rem', fontWeight: '800', color: '#FFFFFF', letterSpacing: '0.04em' }}>
              SIMULATION CONTROLS
            </div>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '0.68rem',
              color: isRunning ? '#34D399' : isPaused ? '#FBBF24' : 'var(--text-muted)',
              fontWeight: '700',
            }}>
              <span className={`pulse-dot ${isRunning ? 'running' : isPaused ? 'paused' : 'stopped'}`} style={{ width: '6px', height: '6px' }} />
              <span>{isRunning ? 'TRANSACTION ENGINE ACTIVE' : isPaused ? 'SIMULATION PAUSED' : 'SIMULATOR STANDBY'}</span>
            </div>
          </div>
        </div>

        {/* Action Buttons: START, PAUSE, RESUME, STOP */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {isStopped ? (
            <button
              className="btn-primary"
              onClick={() => onStart('normal')}
              style={{
                padding: '8px 18px',
                fontSize: '0.825rem',
                fontWeight: '800',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                background: 'linear-gradient(135deg, #00E5FF 0%, #10B981 100%)',
                boxShadow: '0 0 15px rgba(0, 229, 255, 0.3)',
              }}
            >
              <Play size={14} fill="#030712" />
              <span>START</span>
            </button>
          ) : isRunning ? (
            <>
              <button
                className="btn-secondary"
                onClick={onPause}
                style={{
                  padding: '8px 14px',
                  fontSize: '0.825rem',
                  fontWeight: '700',
                  color: '#F59E0B',
                  border: '1px solid rgba(245, 158, 11, 0.4)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                <Pause size={14} />
                <span>PAUSE</span>
              </button>
              <button
                className="btn-danger"
                onClick={onStop}
                style={{
                  padding: '8px 14px',
                  fontSize: '0.825rem',
                  fontWeight: '700',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                <Square size={14} fill="#EF4444" />
                <span>STOP</span>
              </button>
            </>
          ) : (
            <>
              <button
                className="btn-primary"
                onClick={onResume}
                style={{
                  padding: '8px 16px',
                  fontSize: '0.825rem',
                  fontWeight: '800',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                <Play size={14} fill="#030712" />
                <span>RESUME</span>
              </button>
              <button
                className="btn-danger"
                onClick={onStop}
                style={{
                  padding: '8px 14px',
                  fontSize: '0.825rem',
                  fontWeight: '700',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                <Square size={14} fill="#EF4444" />
                <span>STOP</span>
              </button>
            </>
          )}

          {onRefresh && (
            <button
              className="btn-secondary"
              onClick={onRefresh}
              title="Refresh simulator data"
              style={{ padding: '8px 10px' }}
            >
              <RefreshCw size={14} />
            </button>
          )}
        </div>
      </div>

      {/* Center/Right: Speed Selector & Mix Selector */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
        
        {/* Speed Selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ fontSize: '0.7rem', fontWeight: '700', color: 'var(--text-muted)' }}>
            SPEED:
          </span>
          <div style={{
            display: 'flex',
            background: 'rgba(7, 9, 14, 0.7)',
            padding: '2px',
            borderRadius: '6px',
            border: '1px solid var(--border-color)',
            gap: '2px',
          }}>
            {speedModes.map((s) => {
              const active = currentSpeed === s.id;
              return (
                <button
                  key={s.id}
                  onClick={() => onSetSpeed(s.id)}
                  style={{
                    background: active ? 'var(--accent-cyan)' : 'transparent',
                    color: active ? '#030712' : 'var(--text-secondary)',
                    fontWeight: '800',
                    fontSize: '0.68rem',
                    padding: '3px 8px',
                    borderRadius: '4px',
                    border: 'none',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                >
                  {s.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Transaction Mix Selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ fontSize: '0.7rem', fontWeight: '700', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Layers size={13} color="var(--accent-cyan)" />
            <span>GENERATION MIX:</span>
          </span>
          <div style={{
            display: 'flex',
            background: 'rgba(7, 9, 14, 0.7)',
            padding: '2px',
            borderRadius: '6px',
            border: '1px solid var(--border-color)',
            gap: '2px',
            flexWrap: 'wrap',
          }}>
            {mixModes.map((m) => {
              const active = currentMix === m.id;
              return (
                <button
                  key={m.id}
                  onClick={() => onSetMix && onSetMix(m.id)}
                  title={m.desc}
                  style={{
                    background: active ? 'rgba(0, 229, 255, 0.22)' : 'transparent',
                    color: active ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                    border: active ? '1px solid var(--accent-cyan)' : '1px solid transparent',
                    fontWeight: active ? '800' : '600',
                    fontSize: '0.7rem',
                    padding: '4px 10px',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                  }}
                >
                  {active && <span style={{ width: '4px', height: '4px', borderRadius: '50%', background: 'var(--accent-cyan)' }} />}
                  <span>{m.label}</span>
                </button>
              );
            })}
          </div>
        </div>

      </div>
    </div>
  );
}
