// ============================================================
// LatinBien Mobile — App Entry Point
// ============================================================

import React, { Component } from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import AppNavigator from './src/navigation/AppNavigator';
import { COLORS } from './src/utils/constants';

// ErrorBoundary global: si algo falla, mostramos un mensaje
// en vez de una pantalla blanca (útil en producción web/nativa)
class ErrorBoundary extends Component {
  state = { hasError: false, message: '' };

  static getDerivedStateFromError(error) {
    return { hasError: true, message: error?.message || String(error) };
  }

  componentDidCatch(error, info) {
    console.error('ErrorBoundary capturó:', error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <View style={styles.errorContainer}>
          <Text style={styles.errorEmoji}>😵</Text>
          <Text style={styles.errorTitle}>Ocurrió un error</Text>
          <Text style={styles.errorMsg}>
            {this.state.message || 'Error inesperado'}
          </Text>
          <TouchableOpacity
            style={styles.errorBtn}
            onPress={() => this.setState({ hasError: false, message: '' })}
          >
            <Text style={styles.errorBtnText}>Reintentar</Text>
          </TouchableOpacity>
        </View>
      );
    }
    return this.props.children;
  }
}

const styles = StyleSheet.create({
  errorContainer: {
    flex: 1,
    backgroundColor: COLORS.primary,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  errorEmoji: { fontSize: 48, marginBottom: 12 },
  errorTitle: { fontSize: 20, fontWeight: '800', color: COLORS.white, marginBottom: 8 },
  errorMsg: {
    fontSize: 13,
    color: 'rgba(255,255,255,0.8)',
    textAlign: 'center',
    marginBottom: 20,
  },
  errorBtn: {
    backgroundColor: COLORS.accent,
    paddingVertical: 12,
    paddingHorizontal: 28,
    borderRadius: 8,
  },
  errorBtnText: { color: COLORS.white, fontWeight: '700', fontSize: 14 },
});

export default function App() {
  return (
    <SafeAreaProvider>
      <StatusBar style="auto" />
      <ErrorBoundary>
        <AppNavigator />
      </ErrorBoundary>
    </SafeAreaProvider>
  );
}
