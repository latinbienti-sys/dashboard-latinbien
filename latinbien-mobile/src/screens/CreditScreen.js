// ============================================================
// CreditScreen — Líneas de crédito
// ============================================================

import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Linking,
} from 'react-native';
import { COLORS, CREDIT_PLANS } from '../utils/constants';
import { getCreditLines } from '../services/api';
import { isAuthenticated } from '../services/auth';
import { getStatusLabel } from '../utils/storage';

export default function CreditScreen() {
  const [creditLines, setCreditLines] = useState([]);

  useEffect(() => {
    if (isAuthenticated()) {
      getCreditLines()
        .then((lines) => setCreditLines(lines || []))
        .catch(() => {});
    }
  }, []);

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.pageTitle}>💳 Líneas de Crédito</Text>

      {CREDIT_PLANS.map((plan) => (
        <View
          key={plan.id}
          style={[styles.planCard, plan.popular && styles.planFeatured]}
        >
          {plan.popular && (
            <View style={styles.popularBadge}>
              <Text style={styles.popularText}>⭐ Más popular</Text>
            </View>
          )}
          {plan.vip && (
            <View style={styles.vipBadge}>
              <Text style={styles.vipText}>👑 VIP</Text>
            </View>
          )}
          <Text style={styles.planName}>{plan.name}</Text>
          <Text style={styles.planInitial}>
            Inicial desde{' '}
            <Text style={styles.planInitialHighlight}>{plan.initial}%</Text>
          </Text>
          <View style={styles.planFeatures}>
            <Text style={styles.planFeature}>{plan.installments}</Text>
            {plan.features.map((f, i) => (
              <Text key={i} style={styles.planFeature}>
                {f}
              </Text>
            ))}
          </View>
        </View>
      ))}

      <TouchableOpacity
        style={styles.moreBtn}
        onPress={() => Linking.openURL('https://latinbien.com/lineas-de-credito')}
      >
        <Text style={styles.moreBtnText}>Más información →</Text>
      </TouchableOpacity>

      {creditLines.length > 0 && (
        <View style={styles.myLinesSection}>
          <Text style={styles.myLinesTitle}>Mis líneas activas</Text>
          {creditLines.map((line) => (
            <View key={line.id} style={styles.lineCard}>
              <Text style={styles.lineName}>
                {line.name || 'Línea de crédito'}
              </Text>
              <Text style={styles.lineStatus}>
                Estado: {getStatusLabel(line.state)}
              </Text>
              <View style={styles.lineStats}>
                <Text style={styles.lineStat}>
                  Disponible:{' '}
                  <Text style={{ color: COLORS.success }}>
                    ${Number(line.available_credit || 0).toFixed(2)}
                  </Text>
                </Text>
                <Text style={styles.lineStat}>
                  Límite:{' '}
                  <Text style={{ color: COLORS.dark }}>
                    ${Number(line.credit_limit || 0).toFixed(2)}
                  </Text>
                </Text>
              </View>
            </View>
          ))}
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.gray50, padding: 16 },
  pageTitle: { fontSize: 22, fontWeight: '700', color: COLORS.primary, marginBottom: 16 },
  planCard: {
    backgroundColor: COLORS.white,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: COLORS.gray200,
    padding: 20,
    marginBottom: 12,
  },
  planFeatured: {
    borderColor: COLORS.accent,
    shadowColor: COLORS.accent,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  popularBadge: {
    alignSelf: 'flex-start',
    backgroundColor: COLORS.accentLight,
    borderRadius: 100,
    paddingHorizontal: 12,
    paddingVertical: 3,
    marginBottom: 8,
  },
  popularText: { fontSize: 10, fontWeight: '700', color: COLORS.accentDark, textTransform: 'uppercase' },
  vipBadge: {
    alignSelf: 'flex-start',
    backgroundColor: COLORS.primaryUltra,
    borderRadius: 100,
    paddingHorizontal: 12,
    paddingVertical: 3,
    marginBottom: 8,
  },
  vipText: { fontSize: 10, fontWeight: '700', color: COLORS.primary, textTransform: 'uppercase' },
  planName: { fontSize: 18, fontWeight: '700', color: COLORS.primary, marginBottom: 4 },
  planInitial: { fontSize: 14, color: COLORS.gray500, marginBottom: 10 },
  planInitialHighlight: { fontSize: 18, color: COLORS.accent, fontWeight: '700' },
  planFeatures: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  planFeature: {
    fontSize: 12,
    color: COLORS.gray600,
    backgroundColor: COLORS.gray100,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 100,
  },
  moreBtn: {
    backgroundColor: COLORS.primary,
    borderRadius: 10,
    padding: 14,
    alignItems: 'center',
    marginBottom: 20,
  },
  moreBtnText: { color: COLORS.white, fontSize: 14, fontWeight: '600' },
  myLinesSection: { marginBottom: 20 },
  myLinesTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.primary,
    marginBottom: 12,
  },
  lineCard: {
    backgroundColor: COLORS.white,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: COLORS.gray200,
    padding: 16,
    marginBottom: 10,
  },
  lineName: { fontSize: 15, fontWeight: '600', color: COLORS.primary, marginBottom: 4 },
  lineStatus: { fontSize: 13, color: COLORS.gray500, marginBottom: 8 },
  lineStats: { flexDirection: 'row', justifyContent: 'space-between' },
  lineStat: { fontSize: 13, color: COLORS.gray600 },
});
