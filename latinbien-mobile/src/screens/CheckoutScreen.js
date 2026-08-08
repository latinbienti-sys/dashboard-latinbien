// ============================================================
// CheckoutScreen — Compra a contado (resumen + pago)
// ============================================================

import React, { useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Linking,
  Platform,
} from 'react-native';
import { COLORS } from '../utils/constants';
import { formatPrice } from '../utils/storage';

export default function CheckoutScreen({ route }) {
  const { items = [], total = 0 } = route.params || {};
  const [showDetail, setShowDetail] = useState(false);

  const goToPayment = () => {
    // En web, abrir en pestaña nueva (no saca de la app); en nativo, abrir navegador
    if (Platform.OS === 'web' && typeof window !== 'undefined') {
      window.open('https://latinbien.com/shop/cart', '_blank');
    } else {
      Linking.openURL('https://latinbien.com/shop/cart');
    }
  };

  const goWhatsApp = () => {
    const msg = encodeURIComponent(
      `Hola, quiero comprar de contado:\n${items
        .map((i) => `- ${i.name} x${i.qty || 1} (${formatPrice((i.price || 0) * (i.qty || 1))})`)
        .join('\n')}\nTotal: ${formatPrice(total)}`
    );
    if (Platform.OS === 'web' && typeof window !== 'undefined') {
      window.open(`https://wa.me/584247035927?text=${msg}`, '_blank');
    } else {
      Linking.openURL(`https://wa.me/584247035927?text=${msg}`);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.header}>
        <Text style={styles.headerIcon}>🛒</Text>
        <Text style={styles.headerTitle}>Compra a Contado</Text>
        <Text style={styles.headerSubtitle}>Revisa tu pedido antes de pagar</Text>
      </View>

      {/* Resumen de productos */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Tu pedido ({items.length})</Text>
        {items.map((item) => (
          <View key={String(item.id)} style={styles.itemRow}>
            <Text style={styles.itemName} numberOfLines={2}>
              {item.name}
            </Text>
            <Text style={styles.itemQty}>x{item.qty || 1}</Text>
            <Text style={styles.itemPrice}>
              {formatPrice((item.price || 0) * (item.qty || 1))}
            </Text>
          </View>
        ))}
        <View style={styles.divider} />
        <View style={styles.totalRow}>
          <Text style={styles.totalLabel}>Total estimado</Text>
          <Text style={styles.totalValue}>{formatPrice(total)}</Text>
        </View>
        <Text style={styles.note}>
          Los precios son pagaderos en bolívares a la tasa BCV. El total final se confirma en el sitio web.
        </Text>
      </View>

      {/* Detalle plegable */}
      <TouchableOpacity
        style={styles.toggleBtn}
        onPress={() => setShowDetail(!showDetail)}
      >
        <Text style={styles.toggleText}>
          {showDetail ? '▼ Ocultar pasos de pago' : '▶ ¿Cómo pago mi compra?'}
        </Text>
      </TouchableOpacity>
      {showDetail && (
        <View style={styles.card}>
          <Step num={1} text="Completa tu pedido en latinbien.com o por WhatsApp." />
          <Step num={2} text="Recibirás confirmación de tu asesor de ventas." />
          <Step num={3} text="Realiza el pago por transferencia o punto de venta." />
          <Step num={4} text="Recibe tu producto con entrega gratuita." />
        </View>
      )}

      {/* Acciones */}
      <TouchableOpacity style={styles.payBtn} onPress={goToPayment}>
        <Text style={styles.payBtnText}>💳 PAGAR EN LATINBIEN.COM</Text>
      </TouchableOpacity>
      <TouchableOpacity style={styles.wsBtn} onPress={goWhatsApp}>
        <Text style={styles.wsBtnText}>💬 CONFIRMAR POR WHATSAPP</Text>
      </TouchableOpacity>
      <Text style={styles.disclaimer}>
        El pago se procesa en el sitio seguro de LatinBien.
      </Text>
    </ScrollView>
  );
}

function Step({ num, text }) {
  return (
    <View style={styles.stepRow}>
      <View style={styles.stepNum}>
        <Text style={styles.stepNumText}>{num}</Text>
      </View>
      <Text style={styles.stepText}>{text}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.gray50 },
  content: { padding: 16, paddingBottom: 40 },
  header: { alignItems: 'center', marginBottom: 20 },
  headerIcon: { fontSize: 40, marginBottom: 8 },
  headerTitle: { fontSize: 22, fontWeight: '800', color: COLORS.primary },
  headerSubtitle: { fontSize: 13, color: COLORS.gray500, marginTop: 4 },
  card: {
    backgroundColor: COLORS.white,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: COLORS.gray200,
    padding: 16,
    marginBottom: 12,
  },
  cardTitle: { fontSize: 15, fontWeight: '700', color: COLORS.dark, marginBottom: 12 },
  itemRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 6,
    gap: 8,
  },
  itemName: { flex: 1, fontSize: 13, color: COLORS.gray700 },
  itemQty: { fontSize: 12, color: COLORS.gray500, minWidth: 24, textAlign: 'center' },
  itemPrice: { fontSize: 13, fontWeight: '700', color: COLORS.accent, minWidth: 70, textAlign: 'right' },
  divider: { height: 1, backgroundColor: COLORS.gray200, marginVertical: 10 },
  totalRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  totalLabel: { fontSize: 16, fontWeight: '700', color: COLORS.dark },
  totalValue: { fontSize: 18, fontWeight: '800', color: COLORS.accent },
  note: { fontSize: 11, color: COLORS.gray400, marginTop: 10, lineHeight: 15 },
  toggleBtn: { padding: 12, marginBottom: 12 },
  toggleText: { color: COLORS.primary, fontWeight: '600', fontSize: 13, textAlign: 'center' },
  stepRow: { flexDirection: 'row', alignItems: 'center', gap: 12, paddingVertical: 8 },
  stepNum: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: COLORS.primary,
    justifyContent: 'center',
    alignItems: 'center',
  },
  stepNumText: { color: COLORS.white, fontWeight: '700', fontSize: 13 },
  stepText: { flex: 1, fontSize: 13, color: COLORS.gray700 },
  payBtn: {
    backgroundColor: COLORS.accent,
    borderRadius: 10,
    padding: 16,
    alignItems: 'center',
  },
  payBtnText: { color: COLORS.white, fontSize: 15, fontWeight: '800' },
  wsBtn: {
    backgroundColor: '#25D366',
    borderRadius: 10,
    padding: 16,
    alignItems: 'center',
    marginTop: 10,
  },
  wsBtnText: { color: COLORS.white, fontSize: 15, fontWeight: '800' },
  disclaimer: { fontSize: 11, color: COLORS.gray400, textAlign: 'center', marginTop: 12 },
});
