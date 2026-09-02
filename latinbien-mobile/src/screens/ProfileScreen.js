// ============================================================
// ProfileScreen — Perfil del usuario
// ============================================================

import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Alert,
  Linking,
} from 'react-native';
import { COLORS } from '../utils/constants';
import { getCurrentUser, logout } from '../services/auth';
import { getPartnerInfo } from '../services/api';
import * as auth from '../services/auth';

export default function ProfileScreen({ navigation, onLogout }) {
  const [user, setUser] = useState(null);
  const [partner, setPartner] = useState(null);

  useEffect(() => {
    const u = getCurrentUser();
    setUser(u);
    if (u?.partner_id) {
      getPartnerInfo()
        .then((res) => {
          if (res?.length > 0) setPartner(res[0]);
        })
        .catch(() => {});
    }
  }, []);

  const handleLogout = () => {
    Alert.alert('Cerrar sesión', '¿Estás seguro?', [
      { text: 'Cancelar', style: 'cancel' },
      {
        text: 'Cerrar sesión',
        style: 'destructive',
        onPress: async () => {
          await auth.logout();
          onLogout?.();
        },
      },
    ]);
  };

  const userName = partner?.name || user?.name || 'Usuario';
  const userEmail = partner?.email || user?.username || '';

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>👤</Text>
        </View>
        <Text style={styles.name}>{userName}</Text>
        {userEmail ? <Text style={styles.email}>{userEmail}</Text> : null}
        {partner?.credit_limit ? (
          <Text style={styles.creditText}>
            💳 Límite: ${Number(partner.credit_limit).toFixed(2)}
          </Text>
        ) : null}
      </View>

      <View style={styles.menu}>
        <MenuItem
          icon="📋"
          label="Mis contratos"
          onPress={() => navigation?.navigate('Orders')}
        />
        <MenuItem
          icon="💳"
          label="Líneas de crédito"
          onPress={() => navigation?.navigate('Credit')}
        />
        <MenuItem
          icon="⭐"
          label="Club de membresía"
          onPress={() => navigation?.navigate('Club')}
        />
        <MenuItem
          icon="💰"
          label="Reportar pago"
          onPress={() => navigation?.navigate('Payment')}
        />
        <MenuItem
          icon="🌐"
          label="Ir al sitio web"
          onPress={() => Linking.openURL('https://latinbien.com/my')}
        />
        <MenuItem
          icon="🚪"
          label="Cerrar sesión"
          danger
          onPress={handleLogout}
        />
      </View>
    </ScrollView>
  );
}

function MenuItem({ icon, label, onPress, danger }) {
  return (
    <TouchableOpacity style={styles.menuItem} onPress={onPress}>
      <View style={[styles.menuIcon, danger && { backgroundColor: '#fee2e2' }]}>
        <Text style={{ fontSize: 16 }}>{icon}</Text>
      </View>
      <Text style={[styles.menuLabel, danger && { color: COLORS.danger }]}>
        {label}
      </Text>
      <Text style={styles.menuArrow}>›</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.gray50 },
  header: {
    backgroundColor: COLORS.primary,
    padding: 24,
    alignItems: 'center',
  },
  avatar: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: 'rgba(255,255,255,0.15)',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 3,
    borderColor: 'rgba(255,255,255,0.2)',
    marginBottom: 12,
  },
  avatarText: { fontSize: 32 },
  name: { fontSize: 20, fontWeight: '700', color: COLORS.white },
  email: { fontSize: 13, color: 'rgba(255,255,255,0.7)', marginTop: 4 },
  creditText: {
    fontSize: 13,
    color: COLORS.accent,
    marginTop: 8,
    fontWeight: '600',
  },
  menu: {
    backgroundColor: COLORS.white,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: COLORS.gray200,
    margin: 16,
    overflow: 'hidden',
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 14,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.gray100,
  },
  menuIcon: {
    width: 32,
    height: 32,
    borderRadius: 8,
    backgroundColor: COLORS.primaryUltra,
    justifyContent: 'center',
    alignItems: 'center',
  },
  menuLabel: {
    flex: 1,
    fontSize: 14,
    color: COLORS.gray700,
    marginLeft: 12,
    fontWeight: '500',
  },
  menuArrow: { fontSize: 18, color: COLORS.gray300, fontWeight: '300' },
});
