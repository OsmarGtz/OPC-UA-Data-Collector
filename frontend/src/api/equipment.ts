import { apiFetch } from './client';
import type { Equipment, LatestReading, Reading } from '../types';

export function listEquipment(): Promise<Equipment[]> {
  return apiFetch<Equipment[]>('/api/v1/equipment/');
}

export function getEquipment(id: number): Promise<Equipment> {
  return apiFetch<Equipment>(`/api/v1/equipment/${id}`);
}

export function getLatestReadings(equipmentId: number): Promise<LatestReading[]> {
  return apiFetch<LatestReading[]>(`/api/v1/equipment/${equipmentId}/latest`);
}

export function getEquipmentReadings(
  equipmentId: number,
  start: string,
  end: string,
): Promise<Reading[]> {
  const params = new URLSearchParams({ start, end, limit: '2000' });
  return apiFetch<Reading[]>(`/api/v1/equipment/${equipmentId}/readings?${params}`);
}
