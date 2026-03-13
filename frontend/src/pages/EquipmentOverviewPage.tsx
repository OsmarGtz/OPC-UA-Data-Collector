import type { ReactNode } from 'react';
import { useAlertRules, useAlerts } from '../hooks/useAlerts';
import { useEquipmentList, useLatestReadings } from '../hooks/useEquipment';
import type { Alert, AlertRule, Equipment, LatestReading } from '../types';
import { EquipmentCard } from '../components/EquipmentCard';

function EquipmentCardWrapper({
  equipment,
  openAlerts,
  alertRules,
}: {
  equipment: Equipment;
  openAlerts: Alert[];
  alertRules: AlertRule[];
}) {
  const { data: latest = [] } = useLatestReadings(equipment.id);

  // Filter alerts that belong to this equipment via alert rule → tag relationship
  // We approximate by passing all alerts; EquipmentCard uses the rule map to determine worst severity
  return (
    <EquipmentCard
      equipment={equipment}
      latestReadings={latest as LatestReading[]}
      openAlerts={openAlerts}
      alertRules={alertRules}
    />
  );
}

export function EquipmentOverviewPage() {
  const { data: equipmentList = [], isLoading, isError } = useEquipmentList();
  const { data: openAlerts = [] }  = useAlerts('open');
  const { data: alertRules  = [] } = useAlertRules();

  if (isLoading) return <Placeholder>Loading equipment…</Placeholder>;
  if (isError)   return <Placeholder color="#ff4444">Failed to load equipment.</Placeholder>;
  if (equipmentList.length === 0) return <Placeholder>No equipment registered yet.</Placeholder>;

  return (
    <div>
      {/* Page header */}
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 20, fontWeight: 700, color: '#e6edf3', margin: 0 }}>
          Equipment Overview
        </h1>
        <p style={{ fontSize: 13, color: '#7d8590', marginTop: 4 }}>
          {equipmentList.length} unit{equipmentList.length !== 1 ? 's' : ''} monitored · auto-refreshes every 10 s
        </p>
      </div>

      {/* Summary strip */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(3, 1fr)',
        gap: 12,
        marginBottom: 28,
      }}>
        <StatCard label="Total units"   value={equipmentList.length} color="#00d4aa" />
        <StatCard label="Active alerts" value={openAlerts.length}    color={openAlerts.length > 0 ? '#ff4444' : '#00d4aa'} />
        <StatCard label="Alert rules"   value={alertRules.length}    color="#0084ff" />
      </div>

      {/* Equipment cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(310px, 1fr))',
        gap: 16,
      }}>
        {equipmentList.map((eq) => (
          <EquipmentCardWrapper
            key={eq.id}
            equipment={eq}
            openAlerts={openAlerts}
            alertRules={alertRules}
          />
        ))}
      </div>
    </div>
  );
}

function StatCard({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div style={{
      background: '#161b22',
      border: '1px solid #21262d',
      borderRadius: 10,
      padding: '14px 18px',
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
    }}>
      <span style={{ fontSize: 12, color: '#7d8590', textTransform: 'uppercase', letterSpacing: '0.07em' }}>
        {label}
      </span>
      <span style={{ fontSize: 22, fontWeight: 700, color, fontVariantNumeric: 'tabular-nums' }}>
        {value}
      </span>
    </div>
  );
}

function Placeholder({ children, color = '#7d8590' }: { children: ReactNode; color?: string }) {
  return (
    <div style={{ padding: 48, textAlign: 'center', color, fontSize: 14 }}>
      {children}
    </div>
  );
}
