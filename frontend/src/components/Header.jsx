import React from 'react';
import {
  Play,
  Pause,
  Square,
  Clock,
  Zap,
  RefreshCw,
  Layers,
  Activity,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react';

export function Header({
  status,
  activeBank,
  onSelectActiveBank,
  onStart,
  onPause,
  onResume,
  onStop,
  onSetSpeed,
  onRefresh,
}) {
  const isRunning = status?.is_running && !status?.is_paused;
  const isPaused = status?.is_running && status?.is_paused;
  const isStopped = !status?.is_running;
  const currentSpeed = status?.mode || 'normal';
  const currentActiveBank = activeBank || status?.active_bank || 'SBI';

  const [currentDisplayTime, setCurrentDisplayTime] = React.useState(new Date());

  // Sync to backend sim_clock whenever it updates from API
  React.useEffect(() => {
    if (status?.sim_clock) {
      const parsed = new Date(status.sim_clock);
      if (!isNaN(parsed.getTime())) {
        setCurrentDisplayTime(parsed);
      }
    }
  }, [status?.sim_clock]);

  // Smooth continuous 1-second ticking
  React.useEffect(() => {
    const timer = setInterval(() => {
      setCurrentDisplayTime((prev) => new Date(prev.getTime() + 1000));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const formatClock = (dateObj) => {
    if (!dateObj || isNaN(dateObj.getTime())) return '--:--:--';
    return dateObj.toLocaleTimeString('en-IN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: true,
    });
  };

  const formatDate = (dateObj) => {
    if (!dateObj || isNaN(dateObj.getTime())) return '';
    return dateObj.toLocaleDateString('en-IN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  return (
    <header style={{
      background: 'rgba(10, 14, 23, 0.85)',
      backdropFilter: 'blur(20px)',
      WebkitBackdropFilter: 'blur(20px)',
      borderBottom: '1px solid var(--border-color)',
      padding: '14px 24px',
      display: 'flex',
      flexWrap: 'wrap',
      justifyContent: 'space-between',
      alignItems: 'center',
      gap: '16px',
      position: 'sticky',
      top: 0,
      zIndex: 100,
    }}>
      {/* Title & Active Bank Selector */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        <div style={{
          width: '42px',
          height: '42px',
          borderRadius: '10px',
          background: 'linear-gradient(135deg, rgba(0, 229, 255, 0.2) 0%, rgba(59, 130, 246, 0.3) 100%)',
          border: '1px solid rgba(0, 229, 255, 0.4)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 0 15px rgba(0, 229, 255, 0.25)',
        }}>
          <Activity size={22} color="var(--accent-cyan)" />
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h1 style={{ fontSize: '1.2rem', fontWeight: '700', letterSpacing: '-0.02em', color: '#FFFFFF' }}>
              TRANSACTION SIMULATOR
            </h1>
            <span style={{
              fontSize: '0.68rem',
              fontWeight: '700',
              padding: '2px 8px',
              borderRadius: '6px',
              background: 'rgba(0, 229, 255, 0.12)',
              color: 'var(--accent-cyan)',
              border: '1px solid rgba(0, 229, 255, 0.3)',
            }}>
              ACTIVE BANK LEDGER
            </span>
          </div>
          {/* Active Bank Selector per Architecture Requirement */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px' }}>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Active Bank:</span>
            {['ALL', 'SBI', 'AXIS', 'IOB'].map((b) => {
              const isSelected = currentActiveBank.toUpperCase() === b;
              const isConnected = currentActiveBank.toUpperCase() === 'ALL' || isSelected;
              const label = b === 'ALL' ? 'ALL BANKS' : b;
              const statusText = b === 'ALL'
                ? (isSelected ? 'ALL CONNECTED' : 'MULTI')
                : (isConnected ? 'CONNECTED' : 'INACTIVE');
              return (
                <button
                  key={b}
                  onClick={() => onSelectActiveBank && onSelectActiveBank(b)}
                  title={`Switch active bank ledger to ${label}`}
                  style={{
                    padding: '2px 8px',
                    borderRadius: '5px',
                    fontSize: '0.72rem',
                    fontWeight: '700',
                    cursor: 'pointer',
                    border: isConnected ? '1px solid #10B981' : '1px solid rgba(255,255,255,0.1)',
                    background: isSelected ? 'rgba(16, 185, 129, 0.25)' : isConnected ? 'rgba(16, 185, 129, 0.10)' : 'rgba(255, 255, 255, 0.04)',
                    color: isConnected ? '#34D399' : 'var(--text-muted)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <span style={{
                    width: '5px',
                    height: '5px',
                    borderRadius: '50%',
                    background: isConnected ? '#10B981' : '#6B7280',
                    boxShadow: isConnected ? '0 0 6px #10B981' : 'none',
                  }} />
                  <span>{label}</span>
                  <span style={{ fontSize: '0.64rem', opacity: 0.85 }}>
                    ({statusText})
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      </div>


      {/* Center: Live Simulation Clock */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        background: 'rgba(16, 22, 34, 0.9)',
        padding: '6px 16px',
        borderRadius: '10px',
        border: '1px solid var(--border-color)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-muted)', fontSize: '0.75rem' }}>
          <Clock size={15} color="var(--accent-cyan)" />
          <span>SIM CLOCK:</span>
        </div>
        <div className="mono" style={{ fontSize: '1.05rem', fontWeight: '700', color: 'var(--accent-cyan)' }}>
          {formatClock(currentDisplayTime)}
        </div>
        <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
          {formatDate(currentDisplayTime)}
        </div>

        {/* State Indicator */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          padding: '2px 8px',
          borderRadius: '20px',
          background: isRunning ? 'rgba(16, 185, 129, 0.15)' : isPaused ? 'rgba(245, 158, 11, 0.15)' : 'rgba(100, 116, 139, 0.15)',
          border: `1px solid ${isRunning ? 'rgba(16, 185, 129, 0.4)' : isPaused ? 'rgba(245, 158, 11, 0.4)' : 'rgba(100, 116, 139, 0.3)'}`,
          fontSize: '0.7rem',
          fontWeight: '700',
          color: isRunning ? '#10B981' : isPaused ? '#F59E0B' : '#94A3B8',
        }}>
          <span className={`pulse-dot ${isRunning ? 'running' : isPaused ? 'paused' : 'stopped'}`} />
          <span>{isRunning ? 'STREAMING' : isPaused ? 'PAUSED' : 'STANDBY'}</span>
        </div>
      </div>

      {/* Right Controls: Speed Selector & Action Buttons */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        
        {/* Speed Buttons */}
        <div style={{
          display: 'flex',
          background: 'rgba(16, 22, 34, 0.9)',
          padding: '3px',
          borderRadius: '8px',
          border: '1px solid var(--border-color)',
          gap: '2px',
        }}>
          {['slow', 'normal', 'fast'].map((s) => (
            <button
              key={s}
              onClick={() => onSetSpeed(s)}
              style={{
                background: currentSpeed === s ? 'var(--accent-cyan)' : 'transparent',
                color: currentSpeed === s ? '#030712' : 'var(--text-secondary)',
                fontWeight: '700',
                fontSize: '0.725rem',
                padding: '4px 10px',
                borderRadius: '6px',
                border: 'none',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
                textTransform: 'uppercase',
              }}
            >
              {s}
            </button>
          ))}
        </div>

        {/* Start / Pause / Resume / Stop Buttons */}
        {isStopped ? (
          <button className="btn-primary" onClick={() => onStart('normal')} style={{ padding: '8px 16px', fontSize: '0.85rem' }}>
            <Play size={15} fill="#030712" />
            <span>Start Live</span>
          </button>
        ) : isRunning ? (
          <>
            <button className="btn-secondary" onClick={onPause} style={{ padding: '8px 14px', fontSize: '0.85rem', color: '#F59E0B' }}>
              <Pause size={15} />
              <span>Pause</span>
            </button>
            <button className="btn-danger" onClick={onStop} style={{ padding: '8px 14px', fontSize: '0.85rem' }}>
              <Square size={15} />
              <span>Stop</span>
            </button>
          </>
        ) : (
          <>
            <button className="btn-primary" onClick={onResume} style={{ padding: '8px 16px', fontSize: '0.85rem' }}>
              <Play size={15} fill="#030712" />
              <span>Resume</span>
            </button>
            <button className="btn-danger" onClick={onStop} style={{ padding: '8px 14px', fontSize: '0.85rem' }}>
              <Square size={15} />
              <span>Stop</span>
            </button>
          </>
        )}

        <button
          className="btn-secondary"
          onClick={onRefresh}
          title="Manual Refresh"
          style={{ padding: '8px', minWidth: 'auto' }}
        >
          <RefreshCw size={15} />
        </button>
      </div>
    </header>
  );
}
