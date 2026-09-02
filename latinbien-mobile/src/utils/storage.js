// ============================================================
// LatinBien Mobile — Storage helpers (AsyncStorage)
// ============================================================

import AsyncStorage from '@react-native-async-storage/async-storage';

export async function getCart() {
  try {
    const data = await AsyncStorage.getItem('latinbien_cart');
    return data ? JSON.parse(data) : [];
  } catch {
    return [];
  }
}

export async function saveCart(items) {
  try {
    await AsyncStorage.setItem('latinbien_cart', JSON.stringify(items));
  } catch (_) {}
}

export function formatPrice(amount) {
  if (amount == null || isNaN(amount)) return 'Consultar';
  return `$${Number(amount).toFixed(2)}`;
}

export function formatDate(dateStr) {
  if (!dateStr) return 'Fecha no disponible';
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString('es-VE', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  } catch {
    return dateStr;
  }
}

export function getStatusLabel(state) {
  const labels = {
    draft: 'Borrador',
    sent: 'Enviado',
    sale: 'Vendido',
    done: 'Completado',
    cancel: 'Cancelado',
    approved: 'Aprobada',
    pending: 'Pendiente',
    refused: 'Rechazada',
  };
  return labels[state] || state || '--';
}
