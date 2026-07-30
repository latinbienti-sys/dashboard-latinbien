// ============================================================
// CatalogScreen — Catálogo de productos con búsqueda y filtros
// ============================================================

import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  Text,
  TextInput,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
} from 'react-native';
import { COLORS } from '../utils/constants';
import {
  getFeaturedProducts,
  getCategories,
  getProductsByCategory,
  searchProducts,
} from '../services/api';
import ProductCard from '../components/ProductCard';

export default function CatalogScreen({ route, onAddToCart }) {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [activeCat, setActiveCat] = useState(0);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(true);

  const loadProducts = useCallback(async (catId = 0, searchQuery = '') => {
    setLoading(true);
    try {
      let result;
      if (searchQuery) {
        result = await searchProducts(searchQuery, 30);
      } else if (catId === 0) {
        result = await getFeaturedProducts(50);
      } else {
        result = await getProductsByCategory(catId, 50);
      }
      setProducts(result || []);
    } catch (_) {
      setProducts([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    getCategories()
      .then((cats) => setCategories(cats || []))
      .catch(() => {});
    loadProducts(0);
  }, [loadProducts]);

  useEffect(() => {
    if (route?.params?.categoryId) {
      setActiveCat(route.params.categoryId);
      loadProducts(route.params.categoryId);
    }
  }, [route?.params?.categoryId, loadProducts]);

  const handleSearch = () => {
    loadProducts(activeCat, query.trim());
  };

  const handleCategoryPress = (catId) => {
    setActiveCat(catId);
    setQuery('');
    loadProducts(catId);
  };

  const renderItem = ({ item }) => (
    <View style={{ width: '48%' }}>
      <ProductCard product={item} onAddToCart={onAddToCart} />
    </View>
  );

  return (
    <View style={styles.container}>
      {/* Search */}
      <View style={styles.searchBar}>
        <TextInput
          style={styles.searchInput}
          placeholder="Buscar productos..."
          placeholderTextColor={COLORS.gray400}
          value={query}
          onChangeText={setQuery}
          onSubmitEditing={handleSearch}
          returnKeyType="search"
        />
        <TouchableOpacity style={styles.searchBtn} onPress={handleSearch}>
          <Text style={styles.searchBtnText}>Buscar</Text>
        </TouchableOpacity>
      </View>

      {/* Categories */}
      <FlatList
        horizontal
        showsHorizontalScrollIndicator={false}
        data={[{ id: 0, name: '🌟 Todos' }, ...categories]}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={styles.catList}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={[
              styles.catPill,
              activeCat === item.id && styles.catPillActive,
            ]}
            onPress={() => handleCategoryPress(item.id)}
          >
            <Text
              style={[
                styles.catPillText,
                activeCat === item.id && styles.catPillTextActive,
              ]}
            >
              {item.name}
            </Text>
          </TouchableOpacity>
        )}
      />

      {/* Products */}
      {loading ? (
        <View style={styles.loading}>
          <ActivityIndicator size="large" color={COLORS.accent} />
        </View>
      ) : (
        <FlatList
          data={products}
          keyExtractor={(item) => String(item.id)}
          numColumns={2}
          contentContainerStyle={styles.list}
          columnWrapperStyle={styles.row}
          ListEmptyComponent={
            <View style={styles.empty}>
              <Text style={styles.emptyIcon}>📦</Text>
              <Text style={styles.emptyTitle}>No hay productos</Text>
              <Text style={styles.emptyText}>Intenta con otra búsqueda</Text>
            </View>
          }
          renderItem={renderItem}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.gray50 },
  searchBar: {
    flexDirection: 'row',
    padding: 12,
    backgroundColor: COLORS.white,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.gray200,
    gap: 8,
  },
  searchInput: {
    flex: 1,
    backgroundColor: COLORS.gray50,
    borderRadius: 8,
    padding: 10,
    fontSize: 14,
    borderWidth: 1.5,
    borderColor: COLORS.gray200,
    color: COLORS.dark,
  },
  searchBtn: {
    backgroundColor: COLORS.accent,
    borderRadius: 8,
    paddingHorizontal: 16,
    justifyContent: 'center',
  },
  searchBtnText: { color: COLORS.white, fontWeight: '600', fontSize: 13 },
  catList: { paddingHorizontal: 12, paddingVertical: 8, gap: 8 },
  catPill: {
    paddingVertical: 8,
    paddingHorizontal: 18,
    borderRadius: 100,
    borderWidth: 1.5,
    borderColor: COLORS.gray200,
    backgroundColor: COLORS.white,
  },
  catPillActive: {
    backgroundColor: COLORS.primary,
    borderColor: COLORS.primary,
  },
  catPillText: { fontSize: 13, color: COLORS.gray600, fontWeight: '500' },
  catPillTextActive: { color: COLORS.white },
  loading: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  list: { padding: 12 },
  row: { justifyContent: 'space-between' },
  empty: { alignItems: 'center', padding: 48 },
  emptyIcon: { fontSize: 48, opacity: 0.5 },
  emptyTitle: { fontSize: 16, color: COLORS.gray600, marginTop: 12 },
  emptyText: { fontSize: 13, color: COLORS.gray400, marginTop: 4 },
});
