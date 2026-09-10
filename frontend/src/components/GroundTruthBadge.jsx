import React from 'react';
import { ShieldCheck, UserX, AlertOctagon, HelpCircle } from 'lucide-react';

export const GroundTruthBadge = ({ type, showIcon = true, size = 'sm' }) => {
  const normalized = (type || '').toUpperCase();

  if (normalized === 'GENUINE') {
    return (
      <span className="badge-gt badge-genuine" title="Simulation Ground Truth: Genuine Account">
        {showIcon && <ShieldCheck size={13} />}
        <span>Genuine</span>
      </span>
    );
  }

  if (normalized === 'MULE') {
    return (
      <span className="badge-gt badge-mule" title="Simulation Ground Truth: Mule Account">
        {showIcon && <UserX size={13} />}
        <span>Mule</span>
      </span>
    );
  }

  if (normalized === 'COMPROMISED') {
    return (
      <span className="badge-gt badge-compromised" title="Simulation Ground Truth: Compromised Account (ATO)">
        {showIcon && <AlertOctagon size={13} />}
        <span>Compromised</span>
      </span>
    );
  }

  return (
    <span className="badge-gt badge-notice">
      {showIcon && <HelpCircle size={13} />}
      <span>{type || 'Unknown'}</span>
    </span>
  );
};
