// ============================================================
// PaymentScreen — Reportar pago desde la app
// ============================================================

import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  Linking,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { COLORS } from '../utils/constants';
import { getCurrentUser } from '../services/auth';

export default function PaymentScreen() {
  const [contract, setContract] = useState('');
  const [amount, setAmount] = useState('');
  const [reference, setReference] = useState('');
  const [method, setMethod] = useState('');
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [notes, setNotes] = useState('');
  const [sending, setSending] = useState(false);
  const [success, setSuccess] = useState(false);

  const methods = [
    'Transferencia bancaria',
    'Depósito en efectivo',
    'Punto de venta',
    'Pago móvil',
    'Zelle / Internacional',
    'Efectivo en tienda',
    'Otro',
  ];

  const handleSubmit = async () => {
    if (!contract.trim() || !amount.trim() || !reference.trim()) {
      Alert.alert('Campos requeridos', 'Completa contrato, monto y referencia');
      return;
    }

    setSending(true);
    try {
      const user = getCurrentUser();
      const userName = user?.name || user?.username || 'Cliente';

      const msg = encodeURIComponent(
        `📌 *REPORTE DE PAGO - LatinBien App*\n\n` +
        `👤 Cliente: ${userName}\n` +
        `📄 Contrato: ${contract.trim()}\n` +
        `💰 Monto: $${amount.trim()}\n` +
        `🔢 Ref: ${reference.trim()}\n` +
        `🏦 Método: ${method || 'No especificado'}\n` +
        `📅 Fecha: ${date}\n` +
        `${notes ? `📝 Notas: ${notes.trim()}\n` : ''}\n` +
        `✅ Reportado desde la app`
      );

      await Linking.openURL(`https://wa.me/584147348785?text=${msg}`);
      setSuccess(true);
    } catch (err) {
      Alert.alert('Error', 'No se pudo abrir WhatsApp. Intenta de nuevo.');
    } finally {
      setSending(false);
    }
  };

  if (success) {
    return (
      <View style={styles.successContainer}>
        <Text style={styles.successIcon}>✅</Text>
        <Text style={styles.successTitle}>¡Pago reportado con éxito!</Text>
        <Text style={styles.successText}>
          Hemos recibido tu reporte. El equipo de LatinBien lo verificará.
        </Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} keyboardShouldPersistTaps="handled">
      <Text style={styles.title}>💰 Reportar Pago</Text>
      <Text style={styles.subtitle}>
        Reporta el pago de tu cuota o anticipo para que sea registrado en tu
        cuenta.
      </Text>

      <View style={styles.form}>
        <View style={styles.inputGroup}>
          <Text style={styles.label}>Número de contrato</Text>
          <TextInput
            style={styles.input}
            placeholder="Ej: S000123"
            value={contract}
            onChangeText={setContract}
          />
        </View>

        <View style={styles.inputGroup}>
          <Text style={styles.label}>Monto pagado ($)</Text>
          <TextInput
            style={styles.input}
            placeholder="0.00"
            value={amount}
            onChangeText={setAmount}
            keyboardType="decimal-pad"
          />
        </View>

        <View style={styles.inputGroup}>
          <Text style={styles.label}>Referencia / N° de depósito</Text>
          <TextInput
            style={styles.input}
            placeholder="Ej: 123456789"
            value={reference}
            onChangeText={setReference}
          />
        </View>

        <View style={styles.inputGroup}>
          <Text style={styles.label}>Método de pago</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            <View style={styles.methodRow}>
              {methods.map((m) => (
                <TouchableOpacity
                  key={m}
                  style={[styles.methodChip, method === m && styles.methodChipActive]}
                  onPress={() => setMethod(m)}
                >
                  <Text
                    style={[
                      styles.methodChipText,
                      method === m && styles.methodChipTextActive,
                    ]}
                  >
                    {m}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </ScrollView>
        </View>

        <View style={styles.inputGroup}>
          <Text style={styles.label}>Fecha del pago</Text>
          <TextInput
            style={styles.input}
            value={date}
            onChangeText={setDate}
            placeholder="YYYY-MM-DD"
          />
        </View>

        <View style={styles.inputGroup}>
          <Text style={styles.label}>Notas adicionales (opcional)</Text>
          <TextInput
            style={[styles.input, styles.textArea]}
            placeholder="Cualquier detalle adicional..."
            value={notes}
            onChangeText={setNotes}
            multiline
            numberOfLines={3}
          />
        </View>

        <TouchableOpacity
          style={[styles.submitBtn, sending && { opacity: 0.7 }]}
          onPress={handleSubmit}
          disabled={sending}
        >
          {sending ? (
            <ActivityIndicator color={COLORS.white} />
          ) : (
            <Text style={styles.submitBtnText}>📩 Enviar reporte por WhatsApp</Text>
          )}
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.gray50, padding: 16 },
  title: { fontSize: 22, fontWeight: '700', color: COLORS.primary, marginBottom: 4 },
  subtitle: { fontSize: 13, color: COLORS.gray500, marginBottom: 20, lineHeight: 18 },
  form: {
    backgroundColor: COLORS.white,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: COLORS.gray200,
    padding: 20,
    marginBottom: 20,
  },
  inputGroup: { marginBottom: 16 },
  label: { fontSize: 13, fontWeight: '600', color: COLORS.gray700, marginBottom: 6 },
  input: {
    backgroundColor: COLORS.gray50,
    borderWidth: 1.5,
    borderColor: COLORS.gray200,
    borderRadius: 10,
    padding: 12,
    fontSize: 15,
    color: COLORS.dark,
  },
  textArea: { minHeight: 80, textAlignVertical: 'top' },
  methodRow: { flexDirection: 'row', gap: 8, paddingVertical: 4 },
  methodChip: {
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderRadius: 100,
    borderWidth: 1.5,
    borderColor: COLORS.gray200,
    backgroundColor: COLORS.white,
  },
  methodChipActive: { backgroundColor: COLORS.primary, borderColor: COLORS.primary },
  methodChipText: { fontSize: 12, color: COLORS.gray600, fontWeight: '500' },
  methodChipTextActive: { color: COLORS.white },
  submitBtn: {
    backgroundColor: COLORS.accent,
    borderRadius: 10,
    padding: 14,
    alignItems: 'center',
    marginTop: 8,
  },
  submitBtnText: { color: COLORS.white, fontSize: 15, fontWeight: '700' },
  successContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 48,
  },
  successIcon: { fontSize: 56, marginBottom: 16 },
  successTitle: { fontSize: 20, color: COLORS.success, fontWeight: '700', marginBottom: 8, textAlign: 'center' },
  successText: { fontSize: 14, color: COLORS.gray500, textAlign: 'center', lineHeight: 20 },
});
