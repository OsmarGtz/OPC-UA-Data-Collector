import { useQuery } from '@tanstack/react-query';
import { getEquipment, getEquipmentReadings, getLatestReadings, listEquipment } from '../api/equipment';
import { getTagsByEquipment } from '../api/readings';

export function useEquipmentList() {
  return useQuery({
    queryKey: ['equipment'],
    queryFn: listEquipment,
    refetchInterval: 10_000,
  });
}

export function useEquipment(id: number) {
  return useQuery({
    queryKey: ['equipment', id],
    queryFn: () => getEquipment(id),
  });
}

export function useLatestReadings(equipmentId: number) {
  return useQuery({
    queryKey: ['equipment', equipmentId, 'latest'],
    queryFn: () => getLatestReadings(equipmentId),
    refetchInterval: 10_000,
  });
}

export function useTagsByEquipment(equipmentId: number) {
  return useQuery({
    queryKey: ['tags', equipmentId],
    queryFn: () => getTagsByEquipment(equipmentId),
  });
}

export function useEquipmentReadings(equipmentId: number, start: string, end: string) {
  return useQuery({
    queryKey: ['equipment', equipmentId, 'readings', start, end],
    queryFn: () => getEquipmentReadings(equipmentId, start, end),
    refetchInterval: 15_000,
  });
}
