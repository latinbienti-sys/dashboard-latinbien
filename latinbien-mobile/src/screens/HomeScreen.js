// ============================================================
// HomeScreen — Pantalla de inicio con resumen y destacados
// ============================================================

import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  RefreshControl,
  Linking,
  Alert,
  Platform,
} from 'react-native';
import { COLORS } from '../utils/constants';
import { getFeaturedProducts, getCategories, getCreditLines, getSessionInfo } from '../services/api';
import { isAuthenticated } from '../services/auth';
import { formatPrice } from '../utils/storage';
import ProductCard from '../components/ProductCard';
import LoadingSpinner from '../components/LoadingSpinner';

export default function HomeScreen({ navigation, onAddToCart }) {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [creditLine, setCreditLine] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [debugLog, setDebugLog] = useState([]);

  const addDebug = (msg) => setDebugLog(prev => [...prev.slice(-9), msg]);

  const loadData = useCallback(async () => {
    // Verificar sesión primero
    try {
      const info = await getSessionInfo();
      addDebug(`Sesión: OK (uid=${info?.uid}, session_id=${info?.session_id ? 'SÍ' : 'NO'})`);
    } catch (e) {
      addDebug(`Sesión: ERROR - ${e.message}`);
    }
    addDebug('Cargando productos...');
    try {
      const prods = await getFeaturedProducts(10);
      addDebug(`Productos: ${prods?.length || 0} registros`);
      if (prods?.length > 0) addDebug(`1er: ${prods[0].name}`);
      setProducts(prods || []);
    } catch (e) {
      addDebug(`ERROR productos: ${e.message}`);
      setProducts([]);
    }
    addDebug('Cargando categorías...');
    try {
      const cats = await getCategories();
      addDebug(`Categorías: ${cats?.length || 0} registros`);
      setCategories(cats || []);
    } catch (e) {
      addDebug(`ERROR categorías: ${e.message}`);
      setCategories([]);
    }
    if (isAuthenticated()) {
      addDebug('Cargando crédito...');
      try {
        const lines = await getCreditLines();
        addDebug(`Crédito: ${lines?.length || 0} líneas`);
        if (lines?.length > 0) setCreditLine(lines[0]);
      } catch (e) {
        addDebug('Crédito: no disponible');
      }
    }
    addDebug('Carga completa');
  }, []);

  useEffect(() => {
    loadData().finally(() => setLoading(false));
  }, [loadData]);

  const onRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  if (loading) return <LoadingSpinner />;

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[COLORS.accent]} />
      }
    >
      {/* Debug panel */}
      {debugLog.length > 0 && (
        <View style={styles.debugBox}>
          <Text style={styles.debugTitle}>🔍 Debug API</Text>
          {debugLog.map((m, i) => (
            <Text key={i} style={[styles.debugLine, m.includes('ERROR') && { color: '#ef4444', fontWeight: '700' }]}>
              {m}
            </Text>
          ))}
        </View>
      )}
      {/* Banner */}
      <View style={styles.banner}>
        <Text style={styles.bannerTitle}>🏆 ¡Bienvenido a LatinBien!</Text>
        <Text style={styles.bannerText}>
          Compra a crédito con iniciales desde 20% y hasta 20 cuotas.
        </Text>
        <TouchableOpacity
          style={styles.bannerBtn}
          onPress={() => Linking.openURL('https://latinbien.com/shop')}
        >
          <Text style={styles.bannerBtnText}>Ver catálogo</Text>
        </TouchableOpacity>
      </View>

      {/* Credit Summary */}
      {creditLine && (
        <View style={styles.creditCard}>
          <Text style={styles.creditLabel}>💳 Crédito Disponible</Text>
          <Text style={styles.creditAmount}>
            ${Number(creditLine.available_credit || 0).toFixed(2)}
          </Text>
          <View style={styles.creditFooter}>
            <View style={styles.creditStat}>
              <Text style={styles.creditStatNum}>
                ${Number(creditLine.credit_limit || 0).toFixed(2)}
              </Text>
              <Text style={styles.creditStatLabel}>Límite</Text>
            </View>
            <View style={styles.creditStat}>
              <Text style={[styles.creditStatNum, { color: COLORS.accent }]}>
                {creditLine.state === 'approved' ? '✅ Activo' : '⏳ Pendiente'}
              </Text>
              <Text style={styles.creditStatLabel}>Estado</Text>
            </View>
          </View>
        </View>
      )}

      {/* Categories */}
      <View style={styles.sectionHeader}>
        <Text style={styles.sectionTitle}>Categorías</Text>
        <TouchableOpacity onPress={() => navigation?.navigate('Catalog')}>
          <Text style={styles.seeAll}>Ver todo →</Text>
        </TouchableOpacity>
      </View>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.catScroll}>
        {categories.slice(0, 10).map((cat) => (
          <TouchableOpacity
            key={cat.id}
            style={styles.catPill}
            onPress={() => navigation?.navigate('Catalog', { categoryId: cat.id })}
          >
            <Text style={styles.catPillText}>{cat.name}</Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* Featured Products */}
      <View style={styles.sectionHeader}>
        <Text style={styles.sectionTitle}>Destacados</Text>
        <TouchableOpacity onPress={() => navigation?.navigate('Catalog')}>
          <Text style={styles.seeAll}>Ver más →</Text>
        </TouchableOpacity>
      </View>
      <View style={styles.productGrid}>
        {products.map((p) => (
          <ProductCard
            key={p.id}
            product={p}
            onAddToCart={onAddToCart}
            onPress={(prod) => navigation?.navigate('ProductDetail', { product: prod })}
          />
        ))}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.gray50,
  },
  debugBox: {
    backgroundColor: '#1a1a2e',
    borderRadius: 8,
    padding: 10,
    margin: 16,
    marginBottom: 0,
  },
  debugTitle: {
    fontSize: 11,
    color: '#888',
    fontWeight: '700',
    textTransform: 'uppercase',
    marginBottom: 6,
  },
  debugLine: {
    fontSize: 11,
    color: '#0f0',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    lineHeight: 16,
  },
  banner: {
    backgroundColor: COLORS.primary,
    borderRadius: 16,
    padding: 24,
    margin: 16,
    position: 'relative',
    overflow: 'hidden',
  },
  bannerTitle: {
    fontSize: 20,
    fontWeight: '800',
    color: COLORS.white,
    marginBottom: 8,
  },
  bannerText: {
    fontSize: 13,
    color: 'rgba(255,255,255,0.85)',
    marginBottom: 16,
    lineHeight: 18,
  },
  bannerBtn: {
    backgroundColor: COLORS.accent,
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 8,
    alignSelf: 'flex-start',
  },
  bannerBtnText: {
    color: COLORS.white,
    fontWeight: '600',
    fontSize: 13,
  },
  creditCard: {
    backgroundColor: COLORS.primary,
    borderRadius: 16,
    padding: 20,
    marginHorizontal: 16,
    marginBottom: 12,
  },
  creditLabel: {
    fontSize: 11,
    color: 'rgba(255,255,255,0.6)',
    textTransform: 'uppercase',
    letterSpacing: 1.5,
    marginBottom: 8,
  },
  creditAmount: {
    fontSize: 28,
    fontWeight: '800',
    color: COLORS.white,
    marginBottom: 16,
  },
  creditFooter: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  creditStat: {
    alignItems: 'center',
  },
  creditStatNum: {
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.white,
  },
  creditStatLabel: {
    fontSize: 10,
    color: 'rgba(255,255,255,0.5)',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginTop: 2,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingTop: 20,
    paddingBottom: 8,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.primary,
  },
  seeAll: {
    fontSize: 13,
    color: COLORS.accent,
    fontWeight: '600',
  },
  catScroll: {
    paddingLeft: 12,
    marginBottom: 4,
  },
  catPill: {
    backgroundColor: COLORS.white,
    borderWidth: 1.5,
    borderColor: COLORS.gray200,
    borderRadius: 100,
    paddingVertical: 8,
    paddingHorizontal: 18,
    marginHorizontal: 4,
  },
  catPillText: {
    fontSize: 13,
    color: COLORS.gray600,
    fontWeight: '500',
  },
  productGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingHorizontal: 12,
    justifyContent: 'space-between',
  },
});
