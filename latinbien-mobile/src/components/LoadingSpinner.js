// ============================================================
// LoadingSpinner — Componente de carga
// ============================================================

import React from 'react';
import { View, ActivityIndicator, Text, StyleSheet } from 'react-native';
import { COLORS } from '../utils/constants';

export default function LoadingSpinner({ message = 'Cargando...' }) {
  return (
    <View style={styles.container}>
      <ActivityIndicator size="large" color={COLORS.accent} />
      <Text style={styles.text}>{message}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  text: {
    marginTop: 12,
    fontSize: 14,
    color: COLORS.gray500,
  },
});
