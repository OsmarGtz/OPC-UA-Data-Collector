import { apiFetch } from './client';
import type { Tag } from '../types';

export function getTagsByEquipment(equipmentId: number): Promise<Tag[]> {
  return apiFetch<Tag[]>(`/api/v1/tags/?equipment_id=${equipmentId}`);
}
