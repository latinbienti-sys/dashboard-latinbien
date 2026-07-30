// ============================================================
// ProductCard — Tarjeta de producto para catálogo y home
// ============================================================

import React from 'react';
import {
  View,
  Text,
  Image,
  TouchableOpacity,
  StyleSheet,
  Dimensions,
  Linking,
} from 'react-native';
import { COLORS } from '../utils/constants';
import { getProductImageUrl } from '../services/api';
import { formatPrice } from '../utils/storage';

const { width } = Dimensions.get('window');
const CARD_WIDTH = (width - 48) / 2;

export default function ProductCard({ product, onAddToCart }) {
  const imgUrl = getProductImageUrl(product.id);

  const handlePress = () => {
    const url = product.website_url || `https://latinbien.com/shop/product/${product.id}`;
    Linking.openURL(url);
  };

  return (
    <TouchableOpacity style={styles.card} onPress={handlePress} activeOpacity={0.7}>
      <Image
        source={{ uri: imgUrl }}
        style={styles.image}
        resizeMode="contain"
        defaultSource={{ uri: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=' }}
      />
      <View style={styles.info}>
        <Text style={styles.name} numberOfLines={2}>
          {product.name}
        </Text>
        <Text style={styles.price}>{formatPrice(product.list_price)}</Text>
        {product.default_code && (
          <Text style={styles.sku}>Cód: {product.default_code}</Text>
        )}
      </View>
      {onAddToCart && (
        <TouchableOpacity
          style={styles.addBtn}
          onPress={(e) => {
            e.stopPropagation?.();
            onAddToCart(product);
          }}
        >
          <Text style={styles.addBtnText}>+</Text>
        </TouchableOpacity>
      )}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    width: CARD_WIDTH,
    backgroundColor: COLORS.white,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: COLORS.gray200,
    overflow: 'hidden',
    marginBottom: 12,
    position: 'relative',
  },
  image: {
    width: '100%',
    aspectRatio: 1,
    backgroundColor: COLORS.white,
  },
  info: {
    padding: 10,
  },
  name: {
    fontSize: 13,
    fontWeight: '500',
    color: COLORS.gray800,
    lineHeight: 17,
    marginBottom: 4,
  },
  price: {
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.accent,
  },
  sku: {
    fontSize: 11,
    color: COLORS.gray400,
    marginTop: 2,
  },
  addBtn: {
    position: 'absolute',
    bottom: 8,
    right: 8,
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: COLORS.accent,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 4,
    elevation: 3,
  },
  addBtnText: {
    color: COLORS.white,
    fontSize: 20,
    fontWeight: '600',
    lineHeight: 22,
  },
});
