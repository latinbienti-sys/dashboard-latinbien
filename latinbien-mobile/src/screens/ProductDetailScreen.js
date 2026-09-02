// ============================================================
// ProductDetailScreen — Detalle de producto con calculadora
// de planes de pago (replica latinbien.com)
// ============================================================

import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  Image,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Linking,
  ActivityIndicator,
} from 'react-native';
import { COLORS } from '../utils/constants';
import { getProductImageUrl, getProductPlans } from '../services/api';
import { formatPrice } from '../utils/storage';
import {
  calculatePlan,
  getReferencePlan,
  INITIAL_OPTIONS,
  INSTALLMENT_OPTIONS,
  ADMIN_FEE_PER_QUINCENA,
} from '../utils/plans';

export default function ProductDetailScreen({ route, navigation, onAddToCart }) {
  const { product } = route.params || {};
  const [plans, setPlans] = useState(null);
  const [adminFee, setAdminFee] = useState(ADMIN_FEE_PER_QUINCENA);
  const [initialPct, setInitialPct] = useState(0.2);
  const [installments, setInstallments] = useState(20);
  const [loading, setLoading] = useState(true);

  // Obtener cuota_administrativa real del servidor (fallback 2.7)
  useEffect(() => {
    let mounted = true;
    setLoading(true);
    getProductPlans(product?.id)
      .then((res) => {
        if (!mounted) return;
        if (res && typeof res.cuota_administrativa !== 'undefined') {
          setAdminFee(res.cuota_administrativa);
        }
      })
      .catch(() => {})
      .finally(() => {
        if (mounted) setLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, [product?.id]);

  if (!product) {
    return (
      <View style={styles.center}>
        <Text>Producto no encontrado</Text>
      </View>
    );
  }

  const listPrice = product.list_price || 0;
  const plan = calculatePlan(listPrice, initialPct, installments, adminFee);
  const refPlan = getReferencePlan(listPrice, adminFee);
  const imgUrl = getProductImageUrl(product.id);

  const openShop = () => {
    const url = product.website_url || `https://latinbien.com/shop/product/${product.id}`;
    Linking.openURL(url);
  };

  const requestCredit = () => {
    navigation.navigate('Solicitud', {
      product,
      plan: {
        numInstallments: installments,
        initialPct,
      },
    });
  };

  const addToCart = () => {
    onAddToCart?.(product);
    navigation.navigate('Checkout', {
      items: [
        {
          id: product.id,
          name: product.name,
          price: product.list_price || 0,
          qty: 1,
        },
      ],
      total: product.list_price || 0,
    });
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Imagen */}
      <View style={styles.imageWrap}>
        {loading ? (
          <ActivityIndicator color={COLORS.accent} style={styles.imgLoading} />
        ) : (
          <Image
            source={{ uri: imgUrl }}
            style={styles.image}
            resizeMode="contain"
          />
        )}
      </View>

      {/* Info básica */}
      <View style={styles.infoSection}>
        <Text style={styles.name}>{product.name}</Text>
        {product.default_code && (
          <Text style={styles.sku}>Cód: {product.default_code}</Text>
        )}

        <View style={styles.priceRow}>
          <Text style={styles.price}>{formatPrice(listPrice)}</Text>
          <Text style={styles.priceContado}>precio contado</Text>
        </View>

        <View style={styles.refPlanBox}>
          <Text style={styles.refPlanText}>
            🔹 Cuota referencial:{' '}
            <Text style={styles.refPlanStrong}>${refPlan.cuota.toFixed(2)}</Text>
            {' /quincena '}
            <Text style={styles.refPlanMeta}>(inicial 20% • 20 cuotas)</Text>
          </Text>
        </View>
      </View>

      {/* Calculadora de planes */}
      <View style={styles.calculator}>
        <View style={styles.calcHeader}>
          <Text style={styles.calcTitle}>🧮 Personaliza tu Plan de Pago</Text>
          <Text style={styles.calcSubtitle}>Cálculos sugeridos — Solicitar Evaluación</Text>
        </View>

        {/* Selector de inicial */}
        <Text style={styles.fieldLabel}>Elige el Porcentaje de Inicial</Text>
        <View style={styles.optionsRow}>
          {INITIAL_OPTIONS.map((opt) => (
            <TouchableOpacity
              key={opt.value}
              style={[
                styles.optionPill,
                initialPct === opt.value && styles.optionPillActive,
              ]}
              onPress={() => setInitialPct(opt.value)}
            >
              <Text
                style={[
                  styles.optionPillText,
                  initialPct === opt.value && styles.optionPillTextActive,
                ]}
              >
                {opt.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Selector de cuotas */}
        <Text style={[styles.fieldLabel, { marginTop: 16 }]}>
          Elige la Cantidad de Cuotas Quincenales
        </Text>
        <View style={styles.optionsRow}>
          {INSTALLMENT_OPTIONS.map((n) => (
            <TouchableOpacity
              key={n}
              style={[
                styles.optionPill,
                installments === n && styles.optionPillActive,
              ]}
              onPress={() => setInstallments(n)}
            >
              <Text
                style={[
                  styles.optionPillText,
                  installments === n && styles.optionPillTextActive,
                ]}
              >
                {n}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Resultados */}
        <View style={styles.results}>
          <ResultRow label="Valor de Inicial ($)" value={`$${plan.initialAmount.toFixed(2)}`} />
          <ResultRow label="Monto a Financiar ($)" value={`$${plan.montoFinanciar.toFixed(2)}`} />
          <ResultRow label="Plazo (meses)" value={String(plan.months)} />
          <ResultRow
            label="Saldo Administrativo"
            value={`${plan.adminPctTotal.toFixed(2)}% ($${plan.adminAmount.toFixed(2)})`}
          />
          <ResultRow
            label="Valor de la Cuota ($)"
            value={`$${plan.cuota.toFixed(2)}`}
            strong
          />
          <ResultRow
            label="Precio Final a Crédito ($)"
            value={`$${plan.finalCreditPrice.toFixed(2)}`}
            strong
          />
        </View>
      </View>

      {/* Alert */}
      <View style={styles.alertBox}>
        <Text style={styles.alertText}>
          💡 Todos nuestros precios son pagaderos en bolívares a la tasa BCV
        </Text>
      </View>

      {/* Acciones */}
      <TouchableOpacity style={styles.btnPrimary} onPress={addToCart}>
        <Text style={styles.btnPrimaryText}>🛒 AGREGAR AL CARRITO (CONTADO)</Text>
      </TouchableOpacity>

      <TouchableOpacity style={styles.btnCredit} onPress={requestCredit}>
        <Text style={styles.btnCreditText}>⚡ SOLICITAR COMPRA A CRÉDITO</Text>
      </TouchableOpacity>

      <TouchableOpacity style={styles.btnOutline} onPress={openShop}>
        <Text style={styles.btnOutlineText}>Ver en latinbien.com →</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

function ResultRow({ label, value, strong }) {
  return (
    <View style={styles.resultRow}>
      <Text style={styles.resultLabel}>{label}</Text>
      <Text style={[styles.resultValue, strong && styles.resultValueStrong]}>
        {value}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.gray50 },
  content: { paddingBottom: 40 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  imageWrap: {
    backgroundColor: COLORS.white,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
  },
  image: { width: '100%', aspectRatio: 1 },
  imgLoading: { height: 280, paddingTop: 120 },
  infoSection: { padding: 16, backgroundColor: COLORS.white, borderBottomWidth: 1, borderBottomColor: COLORS.gray200 },
  name: { fontSize: 18, fontWeight: '700', color: COLORS.dark, lineHeight: 24 },
  sku: { fontSize: 12, color: COLORS.gray400, marginTop: 4 },
  priceRow: { flexDirection: 'row', alignItems: 'baseline', marginTop: 10 },
  price: { fontSize: 28, fontWeight: '800', color: COLORS.accent },
  priceContado: { fontSize: 12, color: COLORS.gray400, marginLeft: 8 },
  refPlanBox: {
    marginTop: 12,
    backgroundColor: COLORS.primaryUltra,
    borderRadius: 8,
    padding: 10,
  },
  refPlanText: { fontSize: 13, color: COLORS.primary },
  refPlanStrong: { fontWeight: '800' },
  refPlanMeta: { color: COLORS.gray500, fontSize: 12 },
  calculator: {
    margin: 16,
    backgroundColor: COLORS.white,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: COLORS.gray200,
    padding: 16,
  },
  calcHeader: { backgroundColor: COLORS.gray100, borderRadius: 8, padding: 12, marginBottom: 16 },
  calcTitle: { fontSize: 16, fontWeight: '700', color: COLORS.primary, textAlign: 'center' },
  calcSubtitle: { fontSize: 11, color: COLORS.gray500, textAlign: 'center', marginTop: 2 },
  fieldLabel: { fontSize: 13, fontWeight: '600', color: COLORS.gray700, marginBottom: 8 },
  optionsRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  optionPill: {
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 100,
    borderWidth: 1.5,
    borderColor: COLORS.gray200,
    backgroundColor: COLORS.white,
  },
  optionPillActive: {
    backgroundColor: COLORS.primary,
    borderColor: COLORS.primary,
  },
  optionPillText: { fontSize: 13, color: COLORS.gray600, fontWeight: '600' },
  optionPillTextActive: { color: COLORS.white },
  results: {
    marginTop: 20,
    borderTopWidth: 1,
    borderTopColor: COLORS.gray200,
    paddingTop: 12,
  },
  resultRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 6,
  },
  resultLabel: { fontSize: 13, color: COLORS.gray600 },
  resultValue: { fontSize: 14, color: COLORS.dark, fontWeight: '600' },
  resultValueStrong: { fontSize: 16, fontWeight: '800', color: COLORS.primary },
  alertBox: {
    marginHorizontal: 16,
    backgroundColor: COLORS.accentLight,
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
  },
  alertText: { fontSize: 12, color: COLORS.accentDark, textAlign: 'center' },
  btnPrimary: {
    marginHorizontal: 16,
    backgroundColor: COLORS.primary,
    borderRadius: 8,
    padding: 14,
    alignItems: 'center',
  },
  btnPrimaryText: { color: COLORS.white, fontWeight: '700', fontSize: 13 },
  btnCredit: {
    marginHorizontal: 16,
    marginTop: 10,
    backgroundColor: COLORS.accent,
    borderRadius: 8,
    padding: 14,
    alignItems: 'center',
  },
  btnCreditText: { color: COLORS.white, fontWeight: '700', fontSize: 13 },
  btnOutline: {
    marginHorizontal: 16,
    marginTop: 10,
    borderWidth: 1.5,
    borderColor: COLORS.gray300,
    borderRadius: 8,
    padding: 12,
    alignItems: 'center',
  },
  btnOutlineText: { color: COLORS.gray600, fontWeight: '600', fontSize: 13 },
});
