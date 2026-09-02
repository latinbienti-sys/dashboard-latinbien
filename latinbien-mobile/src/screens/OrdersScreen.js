// ============================================================
// OrdersScreen — Mis contratos / órdenes de compra
// ============================================================

import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  Linking,
} from 'react-native';
import { COLORS } from '../utils/constants';
import { getMyOrders } from '../services/api';
import { formatPrice, formatDate, getStatusLabel } from '../utils/storage';

export default function OrdersScreen() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getMyOrders(20)
      .then((result) => setOrders(result || []))
      .catch(() => setOrders([]))
      .finally(() => setLoading(false));
  }, []);

  const renderItem = ({ item }) => (
    <View style={styles.orderCard}>
      <View style={styles.orderHeader}>
        <Text style={styles.orderRef}>{item.name || 'Contrato'}</Text>
        <Text style={[styles.orderStatus, styles[`status${item.state}`]]}>
          {getStatusLabel(item.state)}
        </Text>
      </View>
      <View style={styles.orderBody}>
        <Text style={styles.orderDate}>📅 {formatDate(item.date_order)}</Text>
        <Text style={styles.orderAmount}>💰 {formatPrice(item.amount_total)}</Text>
      </View>
    </View>
  );

  if (loading) {
    return (
      <View style={styles.center}>
        <Text style={styles.loadingText}>Cargando contratos...</Text>
      </View>
    );
  }

  if (orders.length === 0) {
    return (
      <View style={styles.center}>
        <Text style={styles.emptyIcon}>📋</Text>
        <Text style={styles.emptyTitle}>No tienes contratos aún</Text>
        <Text style={styles.emptyText}>Visita el catálogo y haz tu primera compra</Text>
        <TouchableOpacity
          style={styles.emptyBtn}
          onPress={() => Linking.openURL('https://latinbien.com/shop')}
        >
          <Text style={styles.emptyBtnText}>Ir al catálogo</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <FlatList
        data={orders}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={styles.list}
        renderItem={renderItem}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.gray50 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 48 },
  loadingText: { fontSize: 14, color: COLORS.gray500 },
  emptyIcon: { fontSize: 48, opacity: 0.5 },
  emptyTitle: { fontSize: 16, color: COLORS.gray600, marginTop: 12 },
  emptyText: { fontSize: 13, color: COLORS.gray400, marginTop: 4, textAlign: 'center' },
  emptyBtn: {
    backgroundColor: COLORS.accent,
    borderRadius: 8,
    paddingVertical: 10,
    paddingHorizontal: 20,
    marginTop: 16,
  },
  emptyBtnText: { color: COLORS.white, fontWeight: '600', fontSize: 13 },
  list: { padding: 16 },
  orderCard: {
    backgroundColor: COLORS.white,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: COLORS.gray200,
    padding: 16,
    marginBottom: 10,
  },
  orderHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  orderRef: { fontSize: 14, fontWeight: '600', color: COLORS.primary },
  orderStatus: { fontSize: 10, fontWeight: '700', paddingHorizontal: 8, paddingVertical: 3, borderRadius: 100, overflow: 'hidden' },
  statusdraft: { backgroundColor: COLORS.gray100, color: COLORS.gray600 },
  statussent: { backgroundColor: '#dbeafe', color: '#1d4ed8' },
  statussale: { backgroundColor: '#d1fae5', color: '#065f46' },
  statusdone: { backgroundColor: '#d1fae5', color: '#065f46' },
  statuscancel: { backgroundColor: '#fee2e2', color: '#991b1b' },
  orderBody: {},
  orderDate: { fontSize: 13, color: COLORS.gray500, marginBottom: 2 },
  orderAmount: { fontSize: 16, fontWeight: '700', color: COLORS.dark },
});
