// ============================================================
// LoginScreen — Inicio de sesión con Odoo
// ============================================================

import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  Alert,
  ActivityIndicator,
  Linking,
} from 'react-native';
import { COLORS } from '../utils/constants';
import * as auth from '../services/auth';

export default function LoginScreen({ onLoginSuccess }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const handleLogin = async () => {
    if (!email.trim() || !password) {
      Alert.alert('Campos requeridos', 'Ingresa tu correo y contraseña');
      return;
    }

    setLoading(true);
    try {
      await auth.login(email.trim(), password);
      onLoginSuccess?.();
    } catch (err) {
      Alert.alert('Error', err.message || 'Credenciales inválidas');
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <View style={styles.logoSection}>
        <Text style={styles.logo}>
          Latin<Text style={styles.logoAccent}>Bien</Text>
        </Text>
        <Text style={styles.subtitle}>Tu tienda a crédito</Text>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Iniciar sesión</Text>
        <Text style={styles.cardSubtitle}>Usa tu cuenta de LatinBien.com</Text>

        <View style={styles.inputGroup}>
          <TextInput
            style={styles.input}
            placeholder="Correo electrónico"
            placeholderTextColor={COLORS.gray400}
            value={email}
            onChangeText={setEmail}
            keyboardType="email-address"
            autoCapitalize="none"
            autoCorrect={false}
            editable={!loading}
          />
        </View>

        <View style={styles.inputGroup}>
          <View style={styles.passwordRow}>
            <TextInput
              style={[styles.input, { flex: 1 }]}
              placeholder="Contraseña"
              placeholderTextColor={COLORS.gray400}
              value={password}
              onChangeText={setPassword}
              secureTextEntry={!showPassword}
              editable={!loading}
            />
            <TouchableOpacity
              style={styles.eyeBtn}
              onPress={() => setShowPassword(!showPassword)}
            >
              <Text style={styles.eyeText}>{showPassword ? '🙈' : '👁️'}</Text>
            </TouchableOpacity>
          </View>
        </View>

        <TouchableOpacity
          style={[styles.loginBtn, loading && styles.loginBtnDisabled]}
          onPress={handleLogin}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color={COLORS.white} />
          ) : (
            <Text style={styles.loginBtnText}>Ingresar</Text>
          )}
        </TouchableOpacity>

        <View style={styles.divider}>
          <View style={styles.dividerLine} />
          <Text style={styles.dividerText}>o</Text>
          <View style={styles.dividerLine} />
        </View>

        <TouchableOpacity
          style={styles.signupBtn}
          onPress={() => Linking.openURL('https://latinbien.com/web/signup')}
        >
          <Text style={styles.signupBtnText}>Crear cuenta nueva</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.forgotBtn}
          onPress={() =>
            Linking.openURL('https://latinbien.com/web/login?redirect=/my')
          }
        >
          <Text style={styles.forgotText}>¿Olvidaste tu contraseña?</Text>
        </TouchableOpacity>
      </View>

      <Text style={styles.footerText}>
        ¿Eres nuevo?{' '}
        <Text
          style={styles.footerLink}
          onPress={() => Linking.openURL('https://latinbien.com/web/signup')}
        >
          Regístrate aquí
        </Text>
      </Text>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.primary,
    justifyContent: 'center',
    padding: 24,
  },
  logoSection: {
    alignItems: 'center',
    marginBottom: 32,
  },
  logo: {
    fontSize: 36,
    fontWeight: '800',
    color: COLORS.white,
    letterSpacing: -1,
  },
  logoAccent: {
    color: COLORS.accent,
  },
  subtitle: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.6)',
    marginTop: 8,
  },
  card: {
    backgroundColor: COLORS.white,
    borderRadius: 20,
    padding: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.15,
    shadowRadius: 24,
    elevation: 10,
  },
  cardTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: COLORS.primary,
    marginBottom: 4,
  },
  cardSubtitle: {
    fontSize: 13,
    color: COLORS.gray500,
    marginBottom: 24,
  },
  inputGroup: {
    marginBottom: 16,
  },
  input: {
    backgroundColor: COLORS.gray50,
    borderWidth: 1.5,
    borderColor: COLORS.gray200,
    borderRadius: 10,
    padding: 14,
    fontSize: 15,
    color: COLORS.dark,
  },
  passwordRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.gray50,
    borderWidth: 1.5,
    borderColor: COLORS.gray200,
    borderRadius: 10,
  },
  eyeBtn: {
    padding: 14,
  },
  eyeText: {
    fontSize: 18,
  },
  loginBtn: {
    backgroundColor: COLORS.accent,
    borderRadius: 10,
    padding: 16,
    alignItems: 'center',
    marginTop: 8,
  },
  loginBtnDisabled: {
    opacity: 0.7,
  },
  loginBtnText: {
    color: COLORS.white,
    fontSize: 16,
    fontWeight: '700',
  },
  divider: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 20,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: COLORS.gray200,
  },
  dividerText: {
    marginHorizontal: 12,
    fontSize: 12,
    color: COLORS.gray400,
  },
  signupBtn: {
    borderWidth: 2,
    borderColor: COLORS.primary,
    borderRadius: 10,
    padding: 14,
    alignItems: 'center',
  },
  signupBtnText: {
    color: COLORS.primary,
    fontSize: 15,
    fontWeight: '600',
  },
  forgotBtn: {
    alignItems: 'center',
    marginTop: 16,
  },
  forgotText: {
    fontSize: 12,
    color: COLORS.gray500,
    textDecorationLine: 'underline',
  },
  footerText: {
    textAlign: 'center',
    marginTop: 24,
    fontSize: 13,
    color: 'rgba(255,255,255,0.7)',
  },
  footerLink: {
    color: COLORS.accent,
    fontWeight: '600',
    textDecorationLine: 'underline',
  },
});
