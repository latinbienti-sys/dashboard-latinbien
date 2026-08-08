// ============================================================
// LatinBien Mobile — Constantes
// ============================================================

import { Platform } from 'react-native';

// En web, usar URL relativa (el proxy local se encarga de redirigir a latinbien.com)
export const BASE_URL = Platform.OS === 'web' ? '' : 'https://latinbien.com';
export const STORAGE_KEYS = {
  SESSION: 'latinbien_session',
  CART: 'latinbien_cart',
  SETTINGS: 'latinbien_settings',
};

export const CREDIT_PLANS = [
  {
    id: 'clasico',
    name: 'Credi Clásico',
    initial: 50,
    installments: '6 a 20 cuotas',
    features: ['Sin aval', 'Aprobación rápida'],
    popular: false,
  },
  {
    id: 'mas',
    name: 'Credi Más',
    initial: 40,
    installments: '6 a 20 cuotas',
    features: ['Sin aval', 'Mejores condiciones'],
    popular: false,
  },
  {
    id: 'pro',
    name: 'Credi Pro',
    initial: 30,
    installments: '6 a 20 cuotas',
    features: ['Sin aval', 'Crédito preferencial'],
    popular: true,
  },
  {
    id: 'premium',
    name: 'Credi Club Premium',
    initial: 20,
    installments: '6 a 20 cuotas',
    features: ['Sin aval', 'Beneficios exclusivos', 'Asesor dedicado'],
    popular: false,
    vip: true,
  },
];

export const CLUB_BENEFITS = [
  { icon: '💰', title: 'Crédito Preferencial', desc: 'Inicial desde 20%' },
  { icon: '🍽️', title: 'Descuentos', desc: 'Hasta 30% OFF en comercios' },
  { icon: '🚀', title: 'Envío Prioritario', desc: 'Sin costo adicional' },
  { icon: '🏆', title: 'Programa de Puntos', desc: 'Acumula y canjea' },
];

export const COLORS = {
  primary: '#213C83',
  primaryDark: '#1a2f66',
  primaryLight: '#3D6194',
  primaryUltra: '#e8edf5',
  accent: '#F98B10',
  accentLight: '#fff3e0',
  accentDark: '#e07d00',
  success: '#10b981',
  danger: '#ef4444',
  warning: '#f59e0b',
  dark: '#1a1a2e',
  white: '#ffffff',
  gray50: '#f9fafb',
  gray100: '#f3f4f6',
  gray200: '#e5e7eb',
  gray300: '#d1d5db',
  gray400: '#9ca3af',
  gray500: '#6b7280',
  gray600: '#4b5563',
  gray700: '#374151',
  gray800: '#1f2937',
};
