export interface Equipment {
  id: number;
  name: string;
  description: string | null;
  location: string | null;
  created_at: string;
  updated_at: string;
}

export interface Tag {
  id: number;
  name: string;
  node_id: string;
  unit: string | null;
  data_type: string;
  equipment_id: number;
  created_at: string;
}

export interface Reading {
  id: number;
  tag_id: number;
  value: number | null;
  raw_value: string | null;
  quality: string;
  timestamp: string;
}

export interface LatestReading {
  tag_id: number;
  tag_name: string;
  unit: string | null;
  value: number | null;
  raw_value: string | null;
  quality: string;
  timestamp: string;
}

export interface AlertRule {
  id: number;
  name: string;
  tag_id: number;
  operator: string;
  threshold: number;
  duration_seconds: number;
  severity: 'info' | 'warning' | 'critical';
  is_active: boolean;
  created_by: number | null;
  created_at: string;
}

export interface Alert {
  id: number;
  rule_id: number;
  triggering_value: number;
  fired_at: string;
  resolved_at: string | null;
  acknowledged_at: string | null;
  acknowledged_by: number | null;
  // Joined context from backend
  tag_name: string | null;
  tag_unit: string | null;
  equipment_id: number | null;
  equipment_name: string | null;
  equipment_location: string | null;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export type Severity = 'info' | 'warning' | 'critical';
export type AlertStatus = 'open' | 'acknowledged' | 'resolved';

export interface User {
  id: number;
  username: string;
  email: string;
  role: 'operator' | 'engineer' | 'admin';
  is_active: boolean;
}
