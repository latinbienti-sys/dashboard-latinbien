// ============================================================
// PaymentScreen — Pagar facturas con las pasarelas del ERP
// El cobro lo hace Odoo (payment.provider): la app solo arma
// el pedido y abre /payment/pay. Nunca se manda la clave del banco.
// ============================================================

import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  Linking,
  Alert,
  RefreshControl,
} from 'react-native';
import { COLORS } from '../utils/constants';
import { formatPrice, formatDate } from '../utils/storage';
import {
  getMyUnpaidInvoices,
  getPaymentProviders,
  getMyPaymentTransactions,
  buildInvoicePaymentUrl,
  paymentStateLabel,
  PROVIDER_BDV,
} from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';

export default function PaymentScreen() {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [invoices, setInvoices] = useState([]);
  const [providers, setProviders] = useState([]);
const [history, setHistory] = useState([]);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setError(null);
    // Cada bloque va por separado: el Portal no tiene ACL de lectura
    // sobre payment.transaction, y eso no debe tumbar la pantalla.
    const safe = (p, fallback) =>
      p.catch(() => fallback);

    const [inv, provs, hist] = await Promise.all([
      safe(getMyUnpaidInvoices(), null),
      safe(getPaymentProviders(), []),
      safe(getMyPaymentTransactions(), []),
    ]);

    if (inv === null) {
      setError('No se pudieron cargar tus facturas. Revisa tu conexión.');
    } else {
      setInvoices(inv);
    }
    setProviders(provs);
    setHistory(hist);
  }, []);

  useEffect(() => {
    (async () => {
      await load();
      setLoading(false);
    })();
  }, [load]);

  const pay = async (invoice, provider) => {
    if (!provider) {
      Alert.alert('Sin pasarela', 'No hay ninguna pasarela habilitada en el sistema.');
      return;
    }
    const amount = invoice.amount_residual || 0;
    const url = buildInvoicePaymentUrl({
      invoiceId: invoice.id,
      amount,
      currencyId: invoice.currency_id ? invoice.currency_id[0] : 2,
      accessToken: invoice.access_token,
      providerId: provider.id,
      providerCode: provider.code,
    });

    try {
      const res = await Linking.canOpenURL(url);
      if (!res) throw new Error('no navegador');
      await Linking.openURL(url);
    } catch (e) {
      Alert.alert(
        'No se pudo abrir el pago',
        'Intenta de nuevo o comunícate con atención al cliente.'
      );
    }
  };

  if (loading) return <LoadingSpinner message="Cargando tus facturas..." />;

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={async () => {
            setRefreshing(true);
            await load();
            setRefreshing(false);
          }}
          tintColor={COLORS.primary}
        />
      }
    >
      <Text style={styles.title}>💳 Pagar</Text>
      <Text style={styles.subtitle}>
        Elige la factura y paga con la pasarela de LatinBien. Te lleva al Banco de
        Venezuela para confirmar.
      </Text>

      {error && (
        <View style={styles.errorBox}>
          <Text style={styles.errorText}>⚠️ {error}</Text>
        </View>
      )}

      {!error && invoices.length === 0 && (
        <View style={styles.emptyBox}>
          <Text style={styles.emptyIcon}>✅</Text>
          <Text style={styles.emptyTitle}>No tienes facturas pendientes</Text>
          <Text style={styles.emptyText}>
            Cuando LatinBien emita una factura por una compra o crédito, aparecerá
            aquí para pagarla.
          </Text>
        </View>
      )}

      {invoices.length > 0 && (
        <>
          <Text style={styles.sectionTitle}>Facturas pendientes</Text>
          {invoices.map((inv) => (
            <View key={inv.id} style={styles.card}>
              <View style={styles.cardHead}>
                <View style={styles.cardHeadLeft}>
                  <Text style={styles.invoiceName}>{inv.name}</Text>
                  <Text style={styles.invoiceDate}>
                    Vence: {formatDate(inv.invoice_date_due)}
                  </Text>
                </View>
                <Text style={styles.invoiceAmount}>
                  {formatPrice(inv.amount_residual || 0)}
                </Text>
              </View>

              <View style={styles.badgeRow}>
                <View style={styles.badge}>
                  <Text style={styles.badgeText}>
                    {paymentStateLabel(inv.payment_state)}
                  </Text>
                </View>
                <Text style={styles.invoiceTotal}>
                  Total: {formatPrice(inv.amount_total || 0)}
                </Text>
              </View>

              <Text style={styles.payLabel}>Pagar con</Text>
              <View style={styles.providerRow}>
                {providers.length === 0 && (
                  <Text style={styles.noProviders}>
                    No hay pasarelas habilitadas. Contacta a atención al cliente.
                  </Text>
                )}
                {providers.map((p) => (
                  <TouchableOpacity
                    key={p.id}
                    style={styles.providerChip}
                    onPress={() => pay(inv, p)}
                  >
                    <Text style={styles.providerChipText} numberOfLines={1}>
                      {providerLabel(p)}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          ))}
        </>
      )}

      {history.length > 0 && (
        <>
          <Text style={styles.sectionTitle}>Pagos recientes</Text>
          {history.slice(0, 6).map((t) => (
            <View key={t.id} style={styles.historyRow}>
              <View style={styles.historyLeft}>
                <Text style={styles.historyRef} numberOfLines={1}>
                  {t.reference}
                </Text>
                <Text style={styles.historyDate}>
                  {providerName(providers, t.provider_id)}
                </Text>
              </View>
              <Text
                style={[
                  styles.historyAmount,
                  t.state === 'done' && styles.historyDone,
                  t.state === 'error' && styles.historyError,
                  t.state === 'draft' && styles.historyDraft,
                ]}
              >
                {formatPrice(t.amount || 0)} · {txStateLabel(t.state)}
              </Text>
            </View>
          ))}
        </>
      )}
    </ScrollView>
  );
}

// ------------------------------------------------------------
// Helpers
// ------------------------------------------------------------

function providerLabel(p) {
  if (p.code === PROVIDER_BDV) return '🏦 Botón BDV';
  if (p.code === 'bnc') return '🏦 Pago Móvil BNC';
  if (p.code === 'paypal') return '🅿️ PayPal';
  return `💳 ${p.display_name || p.code}`;
}

function providerName(providers, providerId) {
  if (!providerId) return '—';
  const p = providers.find((x) => x.id === providerId[0]);
  return p ? p.display_name : '—';
}

function txStateLabel(state) {
  switch (state) {
    case 'done':
      return 'Pagado';
    case 'error':
      return 'Fallido';
    case 'pending':
      return 'Procesando';
    case 'cancel':
      return 'Cancelado';
    default:
      return 'Pendiente';
  }
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.gray50 },
  content: { padding: 16, paddingBottom: 32 },
  title: { fontSize: 24, fontWeight: '800', color: COLORS.primary },
  subtitle: {
    fontSize: 13,
    color: COLORS.gray600,
    marginTop: 4,
    marginBottom: 18,
    lineHeight: 19,
  },
  errorBox: {
    backgroundColor: '#fee2e2',
    borderRadius: 10,
    padding: 12,
    marginBottom: 16,
  },
  errorText: { color: COLORS.danger, fontSize: 13 },
  emptyBox: {
    backgroundColor: COLORS.white,
    borderRadius: 14,
    padding: 24,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: COLORS.gray200,
  },
  emptyIcon: { fontSize: 40, marginBottom: 10 },
  emptyTitle: { fontSize: 16, fontWeight: '700', color: COLORS.dark },
  emptyText: {
    fontSize: 13,
    color: COLORS.gray600,
    textAlign: 'center',
    marginTop: 6,
    lineHeight: 19,
  },
  sectionTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: COLORS.primary,
    marginTop: 22,
    marginBottom: 10,
  },
  card: {
    backgroundColor: COLORS.white,
    borderRadius: 14,
    padding: 14,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: COLORS.gray200,
  },
  cardHead: { flexDirection: 'row', justifyContent: 'space-between' },
  cardHeadLeft: { flex: 1, marginRight: 10 },
  invoiceName: { fontSize: 15, fontWeight: '700', color: COLORS.dark },
  invoiceDate: { fontSize: 12, color: COLORS.gray500, marginTop: 2 },
  invoiceAmount: { fontSize: 16, fontWeight: '800', color: COLORS.accentDark },
  badgeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: 10,
  },
  badge: {
    backgroundColor: COLORS.accentLight,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  badgeText: { fontSize: 11, fontWeight: '700', color: COLORS.accentDark },
  invoiceTotal: { fontSize: 11, color: COLORS.gray500 },
  payLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: COLORS.gray600,
    marginTop: 14,
    marginBottom: 8,
    textTransform: 'uppercase',
  },
  providerRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  providerChip: {
    backgroundColor: COLORS.primary,
    paddingHorizontal: 14,
    paddingVertical: 9,
    borderRadius: 20,
  },
  providerChipText: { color: COLORS.white, fontSize: 12, fontWeight: '700' },
  noProviders: { fontSize: 12, color: COLORS.danger },
  historyRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: COLORS.white,
    borderRadius: 10,
    padding: 12,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: COLORS.gray200,
  },
  historyLeft: { flex: 1, marginRight: 10 },
  historyRef: { fontSize: 13, fontWeight: '600', color: COLORS.dark },
  historyDate: { fontSize: 11, color: COLORS.gray500, marginTop: 2 },
  historyAmount: { fontSize: 12, fontWeight: '700', color: COLORS.gray600 },
  historyDone: { color: COLORS.success },
  historyError: { color: COLORS.danger },
  historyDraft: { color: COLORS.warning },
});