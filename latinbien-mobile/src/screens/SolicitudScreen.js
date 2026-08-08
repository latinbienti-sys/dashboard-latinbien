// ============================================================
// SolicitudScreen — Solicitud de compra a crédito (interno)
// ============================================================

import React, { useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  TextInput,
  Platform,
  KeyboardAvoidingView,
} from 'react-native';
import { COLORS } from '../utils/constants';
import { formatPrice } from '../utils/storage';

const CREDIT_LINES = [
  { id: 'clasico', label: 'Credi Clásico', initial: 50, desc: 'Inicial 50%' },
  { id: 'mas', label: 'Credi Más', initial: 40, desc: 'Inicial 40%' },
  { id: 'pro', label: 'Credi Pro', initial: 30, desc: 'Inicial 30%' },
  { id: 'club', label: 'Credi Club Premium', initial: 20, desc: 'Inicial 20%' },
];

export default function SolicitudScreen({ route }) {
  const { product, plan } = route.params || {};
  const [line, setLine] = useState(CREDIT_LINES[0].id);
  const [name, setName] = useState('');
  const [cedula, setCedula] = useState('');
  const [phone, setPhone] = useState('');
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const selected = CREDIT_LINES.find((l) => l.id === line);

  // Plan actualizado según la línea de crédito elegida
  const activePlan = product && plan
    ? (() => {
        const initialPct = selected.initial / 100;
        const cuota = Math.round(
          ((product.list_price * (1 - initialPct)) * 1.54) / (plan.numInstallments || 20)
        );
        const inicial = Math.round(product.list_price * initialPct);
        const total = inicial + cuota * (plan.numInstallments || 20);
        return { ...plan, cuota, inicial, total };
      })()
    : null;

  const valid =
    name.trim().length >= 3 &&
    cedula.trim().length >= 5 &&
    phone.trim().length >= 7 &&
    email.includes('@');

  const submit = () => {
    if (!valid) return;
    const msg = encodeURIComponent(
      `*Solicitud de crédito LatinBien*\nProducto: ${product?.name}\nLínea: ${selected.label} (${selected.desc})\nCuotas: ${plan?.numInstallments || 20} quincenales\nInicial: ${formatPrice(activePlan?.inicial)}\nCuota: ${formatPrice(activePlan?.cuota)}\n\nNombre: ${name}\nCédula: ${cedula}\nTeléfono: ${phone}\nEmail: ${email}`
    );
    if (Platform.OS === 'web' && typeof window !== 'undefined') {
      window.open(`https://wa.me/584247035927?text=${msg}`, '_blank');
    } else {
      // En nativo usamos Linking
      require('react-native').Linking.openURL(`https://wa.me/584247035927?text=${msg}`);
    }
    setSubmitted(true);
  };

  if (submitted) {
    return (
      <View style={styles.container}>
        <View style={styles.successBox}>
          <Text style={styles.successIcon}>✅</Text>
          <Text style={styles.successTitle}>Solicitud lista</Text>
          <Text style={styles.successText}>
            Abrimos WhatsApp con tu solicitud preparada. Envíala y un asesor te
            contactará para validar tu crédito.
          </Text>
          <TouchableOpacity
            style={styles.againBtn}
            onPress={() => {
              setSubmitted(false);
              setName('');
              setCedula('');
              setPhone('');
              setEmail('');
            }}
          >
            <Text style={styles.againText}>➕ Nueva solicitud</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  return (
    <KeyboardAvoidingView style={styles.container} behavior="padding">
      <ScrollView style={styles.container} contentContainerStyle={styles.content}>
        <View style={styles.header}>
          <Text style={styles.headerIcon}>📋</Text>
          <Text style={styles.headerTitle}>Solicitud de Crédito</Text>
          <Text style={styles.headerSubtitle}>
            Sin trámites largos. Elige tu línea y envía tus datos.
          </Text>
        </View>

        {/* Producto */}
        {product && (
          <View style={styles.card}>
            <Text style={styles.cardTitle}>Producto seleccionado</Text>
            <Text style={styles.productName}>{product.name}</Text>
            <Text style={styles.productPrice}>
              {formatPrice(product.list_price)} · a crédito
            </Text>
          </View>
        )}

        {/* Línea de crédito */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Elige tu línea de crédito</Text>
          {CREDIT_LINES.map((l) => (
            <TouchableOpacity
              key={l.id}
              style={[styles.lineRow, line === l.id && styles.lineRowActive]}
              onPress={() => setLine(l.id)}
            >
              <View style={styles.lineInfo}>
                <Text style={[styles.lineLabel, line === l.id && styles.lineLabelActive]}>
                  {l.label}
                </Text>
                <Text style={styles.lineDesc}>{l.desc}</Text>
              </View>
              <View style={[styles.radio, line === l.id && styles.radioActive]}>
                {line === l.id && <View style={styles.radioDot} />}
              </View>
            </TouchableOpacity>
          ))}
        </View>

        {/* Plan calculado */}
        {activePlan && (
          <View style={styles.card}>
            <Text style={styles.cardTitle}>Tu plan de pago</Text>
            <PlanRow label="Inicial" value={formatPrice(activePlan.inicial)} />
            <PlanRow label="Nº de cuotas" value={`${activePlan.numInstallments} quincenales`} />
            <PlanRow label="Cuota quincenal" value={formatPrice(activePlan.cuota)} bold />
            <PlanRow label="Total a crédito" value={formatPrice(activePlan.total)} />
            <Text style={styles.note}>
              Plan referencial: incluye 54% de costo administrativo (2.7% por quincena).
            </Text>
          </View>
        )}

        {/* Datos personales */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Tus datos</Text>
          <Field label="Nombre completo" value={name} onChange={setName} placeholder="Ej: María Pérez" />
          <Field label="Cédula" value={cedula} onChange={setCedula} placeholder="V-12345678" keyboardType="numeric" />
          <Field label="Teléfono / WhatsApp" value={phone} onChange={setPhone} placeholder="0412-1234567" keyboardType="phone-pad" />
          <Field label="Email" value={email} onChange={setEmail} placeholder="tucorreo@email.com" keyboardType="email-address" />
        </View>

        <TouchableOpacity
          style={[styles.submitBtn, !valid && styles.submitBtnDisabled]}
          onPress={submit}
          disabled={!valid}
        >
          <Text style={styles.submitBtnText}>📲 ENVIAR SOLICITUD POR WHATSAPP</Text>
        </TouchableOpacity>
        <Text style={styles.disclaimer}>
          Al enviar, un asesor de LatinBien validará tu crédito y te contactará.
        </Text>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

function Field({ label, value, onChange, placeholder, keyboardType }) {
  return (
    <View style={styles.field}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <TextInput
        style={styles.input}
        value={value}
        onChangeText={onChange}
        placeholder={placeholder}
        placeholderTextColor={COLORS.gray400}
        keyboardType={keyboardType || 'default'}
      />
    </View>
  );
}

function PlanRow({ label, value, bold }) {
  return (
    <View style={styles.planRow}>
      <Text style={[styles.planLabel, bold && styles.planLabelBold]}>{label}</Text>
      <Text style={[styles.planValue, bold && styles.planValueBold]}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.gray50 },
  content: { padding: 16, paddingBottom: 40 },
  header: { alignItems: 'center', marginBottom: 20 },
  headerIcon: { fontSize: 40, marginBottom: 8 },
  headerTitle: { fontSize: 22, fontWeight: '800', color: COLORS.primary },
  headerSubtitle: { fontSize: 13, color: COLORS.gray500, marginTop: 4, textAlign: 'center' },
  card: {
    backgroundColor: COLORS.white,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: COLORS.gray200,
    padding: 16,
    marginBottom: 12,
  },
  cardTitle: { fontSize: 15, fontWeight: '700', color: COLORS.dark, marginBottom: 10 },
  productName: { fontSize: 15, fontWeight: '600', color: COLORS.gray800 },
  productPrice: { fontSize: 13, color: COLORS.accent, fontWeight: '600', marginTop: 4 },
  lineRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: COLORS.gray200,
    marginBottom: 8,
    backgroundColor: COLORS.gray50,
  },
  lineRowActive: { borderColor: COLORS.primary, backgroundColor: '#EEF4FB' },
  lineInfo: { flex: 1 },
  lineLabel: { fontSize: 14, fontWeight: '600', color: COLORS.gray800 },
  lineLabelActive: { color: COLORS.primary },
  lineDesc: { fontSize: 12, color: COLORS.gray500, marginTop: 2 },
  radio: {
    width: 20,
    height: 20,
    borderRadius: 10,
    borderWidth: 2,
    borderColor: COLORS.gray300,
    justifyContent: 'center',
    alignItems: 'center',
  },
  radioActive: { borderColor: COLORS.primary },
  radioDot: { width: 10, height: 10, borderRadius: 5, backgroundColor: COLORS.primary },
  planRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 6,
  },
  planLabel: { fontSize: 13, color: COLORS.gray600 },
  planLabelBold: { fontWeight: '700', color: COLORS.dark },
  planValue: { fontSize: 13, color: COLORS.gray800, fontWeight: '600' },
  planValueBold: { fontSize: 15, fontWeight: '800', color: COLORS.accent },
  note: { fontSize: 11, color: COLORS.gray400, marginTop: 8, lineHeight: 15 },
  field: { marginBottom: 12 },
  fieldLabel: { fontSize: 12, fontWeight: '600', color: COLORS.gray600, marginBottom: 6 },
  input: {
    borderWidth: 1,
    borderColor: COLORS.gray200,
    borderRadius: 10,
    padding: 12,
    fontSize: 14,
    color: COLORS.dark,
    backgroundColor: COLORS.white,
  },
  submitBtn: {
    backgroundColor: '#25D366',
    borderRadius: 10,
    padding: 16,
    alignItems: 'center',
  },
  submitBtnDisabled: { opacity: 0.5 },
  submitBtnText: { color: COLORS.white, fontSize: 15, fontWeight: '800' },
  disclaimer: { fontSize: 11, color: COLORS.gray400, textAlign: 'center', marginTop: 12 },
  successBox: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  successIcon: { fontSize: 56, marginBottom: 12 },
  successTitle: { fontSize: 20, fontWeight: '800', color: COLORS.dark },
  successText: {
    fontSize: 14,
    color: COLORS.gray600,
    textAlign: 'center',
    marginTop: 8,
    lineHeight: 20,
  },
  againBtn: {
    marginTop: 20,
    borderWidth: 2,
    borderColor: COLORS.primary,
    borderRadius: 10,
    padding: 12,
    paddingHorizontal: 24,
  },
  againText: { color: COLORS.primary, fontWeight: '700', fontSize: 14 },
});
