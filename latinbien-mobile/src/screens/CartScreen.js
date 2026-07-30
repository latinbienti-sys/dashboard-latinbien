// ============================================================
// CartScreen — Carrito de compras
// ============================================================

import React from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  Image,
  Linking,
  Alert,
} from 'react-native';
import { COLORS } from '../utils/constants';
import { getProductImageUrl } from '../services/api';
import { formatPrice } from '../utils/storage';

export default function CartScreen({ cart, onUpdateQty, onRemove, onClear }) {
  const total = cart.reduce((s, i) => s + (i.price || 0) * (i.qty || 1), 0);
  const count = cart.reduce((s, i) => s + (i.qty || 1), 0);

  if (cart.length === 0) {
    return (
      <View style={styles.empty}>
        <Text style={styles.emptyIcon}>🛒</Text>
        <Text style={styles.emptyTitle}>Tu carrito está vacío</Text>
        <Text style={styles.emptyText}>Explora el catálogo y agrega productos</Text>
      </View>
    );
  }

  const renderItem = ({ item }) => (
    <View style={styles.cartItem}>
      <Image
        source={{ uri: getProductImageUrl(item.id) }}
        style={styles.itemImage}
        resizeMode="contain"
      />
      <View style={styles.itemInfo}>
        <Text style={styles.itemName} numberOfLines={2}>
          {item.name}
        </Text>
        <Text style={styles.itemPrice}>
          {formatPrice((item.price || 0) * (item.qty || 1))}
        </Text>
        <View style={styles.actions}>
          <TouchableOpacity
            style={styles.qtyBtn}
            onPress={() => onUpdateQty(item.id, -1)}
          >
            <Text style={styles.qtyBtnText}>−</Text>
          </TouchableOpacity>
          <Text style={styles.qty}>{item.qty || 1}</Text>
          <TouchableOpacity
            style={styles.qtyBtn}
            onPress={() => onUpdateQty(item.id, 1)}
          >
            <Text style={styles.qtyBtnText}>+</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.qtyBtn, styles.removeBtn]}
            onPress={() => onRemove(item.id)}
          >
            <Text style={[styles.qtyBtnText, { color: COLORS.danger }]}>✕</Text>
          </TouchableOpacity>
        </View>
      </View>
    </View>
  );

  return (
    <View style={styles.container}>
      <FlatList
        data={cart}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={styles.list}
        renderItem={renderItem}
      />
      <View style={styles.summary}>
        <View style={styles.summaryRow}>
          <Text style={styles.summaryLabel}>Productos ({count})</Text>
          <Text style={styles.summaryValue}>{formatPrice(total)}</Text>
        </View>
        <View style={[styles.summaryRow, styles.totalRow]}>
          <Text style={styles.totalLabel}>Total estimado</Text>
          <Text style={styles.totalValue}>{formatPrice(total)}</Text>
        </View>
        <View style={styles.summaryActions}>
          <TouchableOpacity
            style={styles.checkoutBtn}
            onPress={() =>
              Linking.openURL('https://latinbien.com/shop/cart')
            }
          >
            <Text style={styles.checkoutText}>🛒 Ir al carrito en la web</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.clearBtn}
            onPress={() => {
              Alert.alert('Vaciar carrito', '¿Eliminar todos los productos?', [
                { text: 'Cancelar', style: 'cancel' },
                { text: 'Vaciar', style: 'destructive', onPress: onClear },
              ]);
            }}
          >
            <Text style={styles.clearText}>🗑️ Vaciar</Text>
          </TouchableOpacity>
        </View>
        <Text style={styles.disclaimer}>
          Los precios son referenciales. El total final se calcula en el sitio web.
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.gray50 },
  empty: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 48 },
  emptyIcon: { fontSize: 48, opacity: 0.5 },
  emptyTitle: { fontSize: 16, color: COLORS.gray600, marginTop: 12 },
  emptyText: { fontSize: 13, color: COLORS.gray400, marginTop: 4 },
  list: { padding: 16 },
  cartItem: {
    flexDirection: 'row',
    backgroundColor: COLORS.white,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: COLORS.gray200,
    padding: 12,
    marginBottom: 10,
    gap: 12,
  },
  itemImage: { width: 60, height: 60, borderRadius: 8, backgroundColor: COLORS.gray50 },
  itemInfo: { flex: 1 },
  itemName: { fontSize: 13, fontWeight: '600', color: COLORS.gray800, marginBottom: 4 },
  itemPrice: { fontSize: 14, fontWeight: '700', color: COLORS.accent, marginBottom: 6 },
  actions: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  qtyBtn: {
    width: 28,
    height: 28,
    borderRadius: 14,
    borderWidth: 1.5,
    borderColor: COLORS.gray200,
    justifyContent: 'center',
    alignItems: 'center',
  },
  qtyBtnText: { fontSize: 16, fontWeight: '600', color: COLORS.gray700 },
  removeBtn: { borderColor: COLORS.danger, marginLeft: 8 },
  qty: { fontSize: 14, fontWeight: '600', minWidth: 20, textAlign: 'center', color: COLORS.dark },
  summary: {
    backgroundColor: COLORS.white,
    borderTopWidth: 1,
    borderTopColor: COLORS.gray200,
    padding: 16,
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 6,
  },
  summaryLabel: { fontSize: 14, color: COLORS.gray600 },
  summaryValue: { fontSize: 14, color: COLORS.gray800, fontWeight: '500' },
  totalRow: { borderTopWidth: 1, borderTopColor: COLORS.gray200, marginTop: 4, paddingTop: 12 },
  totalLabel: { fontSize: 18, fontWeight: '700', color: COLORS.dark },
  totalValue: { fontSize: 18, fontWeight: '700', color: COLORS.accent },
  summaryActions: { gap: 8, marginTop: 12 },
  checkoutBtn: {
    backgroundColor: COLORS.accent,
    borderRadius: 10,
    padding: 14,
    alignItems: 'center',
  },
  checkoutText: { color: COLORS.white, fontSize: 15, fontWeight: '700' },
  clearBtn: {
    borderWidth: 2,
    borderColor: COLORS.gray200,
    borderRadius: 10,
    padding: 12,
    alignItems: 'center',
  },
  clearText: { color: COLORS.gray600, fontSize: 13, fontWeight: '600' },
  disclaimer: {
    fontSize: 11,
    color: COLORS.gray400,
    textAlign: 'center',
    marginTop: 12,
  },
});
