// ============================================================
// ClubScreen — Club de membresía LatinBien
// ============================================================

import React from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Linking,
} from 'react-native';
import { COLORS, CLUB_BENEFITS } from '../utils/constants';

export default function ClubScreen() {
  const faqs = [
    {
      q: '¿Cuánto cuesta ser miembro?',
      a: 'Ser miembro del Club Latinbien es completamente gratis. No hay cuotas de afiliación ni costos de mantenimiento.',
    },
    {
      q: '¿Cómo accedo a los descuentos?',
      a: 'Presenta tu cédula o código de miembro en el comercio afiliado al pagar. El descuento se aplica automáticamente.',
    },
    {
      q: '¿Puedo subir de nivel?',
      a: 'Sí. A medida que construyes un historial de pagos puntuales, asciendes automáticamente de nivel.',
    },
  ];

  return (
    <ScrollView style={styles.container}>
      {/* Niveles */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>🏆 Niveles de Membresía</Text>
        <PlanCard
          name="🥉 Básico"
          initial="50%"
          features={['Crédito básico', '6 a 20 cuotas']}
        />
        <PlanCard
          name="🥈 Medio"
          initial="30%"
          features={['Crédito preferencial', 'Descuentos en comercios', 'Envío gratis', 'Puntos dobles']}
          popular
        />
        <PlanCard
          name="🥇 VIP"
          initial="20%"
          features={['Crédito premium', 'Descuentos en todos los comercios', 'Asesor 24/7', 'Puntos triples', 'Eventos VIP']}
          vip
        />
        <View style={styles.ctaRow}>
          <TouchableOpacity
            style={styles.ctaBtn}
            onPress={() => Linking.openURL('https://latinbien.com/web/signup')}
          >
            <Text style={styles.ctaBtnText}>⭐ Afiliarse</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.ctaOutline}
            onPress={() => Linking.openURL('https://latinbien.com/web/login')}
          >
            <Text style={styles.ctaOutlineText}>🔑 Iniciar sesión</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Beneficios */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>✨ Beneficios del Club</Text>
        <View style={styles.benefitsGrid}>
          {CLUB_BENEFITS.map((b, i) => (
            <View key={i} style={styles.benefitCard}>
              <Text style={styles.benefitIcon}>{b.icon}</Text>
              <Text style={styles.benefitTitle}>{b.title}</Text>
              <Text style={styles.benefitDesc}>{b.desc}</Text>
            </View>
          ))}
        </View>
      </View>

      {/* Comercios */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>📍 Comercios Afiliados</Text>
        <View style={styles.commerceGrid}>
          {[
            { icon: '🍝', name: 'Rest. La Nota', discount: '15% OFF', cat: 'Gastronomía' },
            { icon: '🏋️', name: 'Gimnasio Bi Fit', discount: '30% OFF', cat: 'Fitness' },
            { icon: '🅿️', name: 'Est. Rodeo Plaza', discount: '20% OFF', cat: 'Estacionamiento' },
            { icon: '💻', name: 'Tecnología Plus', discount: '10% OFF', cat: 'Tecnología' },
          ].map((c, i) => (
            <View key={i} style={styles.commerceCard}>
              <Text style={styles.commerceIcon}>{c.icon}</Text>
              <Text style={styles.commerceName}>{c.name}</Text>
              <Text style={styles.commerceDiscount}>{c.discount}</Text>
              <Text style={styles.commerceCat}>{c.cat}</Text>
            </View>
          ))}
        </View>
        <View style={styles.affiliateBanner}>
          <Text style={styles.affiliateText}>
            💡 ¿Tienes un comercio y quieres ser afiliado?
          </Text>
          <TouchableOpacity
            style={styles.affiliateBtn}
            onPress={() =>
              Linking.openURL('https://wa.me/584147348785?text=Quiero%20ser%20comercio%20afiliado')
            }
          >
            <Text style={styles.affiliateBtnText}>🤝 Ser afiliado</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Pasos */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>📋 ¿Cómo funciona?</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          {[
            { num: 1, title: 'Regístrate', desc: 'Crea tu cuenta gratis' },
            { num: 2, title: 'Activa tu membresía', desc: 'Selecciona tu nivel' },
            { num: 3, title: 'Compra y ahorra', desc: 'Usa tu crédito y descuentos' },
            { num: 4, title: 'Crece con nosotros', desc: 'Sube de nivel' },
          ].map((s, i) => (
            <View key={i} style={styles.stepCard}>
              <View style={styles.stepNum}>
                <Text style={styles.stepNumText}>{s.num}</Text>
              </View>
              <Text style={styles.stepTitle}>{s.title}</Text>
              <Text style={styles.stepDesc}>{s.desc}</Text>
            </View>
          ))}
        </ScrollView>
      </View>

      {/* FAQ */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>❓ Preguntas Frecuentes</Text>
        {faqs.map((faq, i) => (
          <FaqItem key={i} question={faq.q} answer={faq.a} />
        ))}
      </View>

      <TouchableOpacity
        style={styles.footerBtn}
        onPress={() => Linking.openURL('https://latinbien.com')}
      >
        <Text style={styles.footerBtnText}>🌐 Conocer más en latinbien.com</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

function PlanCard({ name, initial, features, popular, vip }) {
  return (
    <View style={[styles.planCard, popular && styles.planFeatured]}>
      {popular && (
        <View style={styles.badgePop}>
          <Text style={styles.badgePopText}>⭐ Más popular</Text>
        </View>
      )}
      {vip && (
        <View style={styles.badgeVip}>
          <Text style={styles.badgeVipText}>👑 VIP</Text>
        </View>
      )}
      <Text style={styles.planCardName}>{name}</Text>
      <Text style={styles.planCardInitial}>
        Inicial desde <Text style={{ color: COLORS.accent, fontWeight: '700', fontSize: 16 }}>{initial}</Text>
      </Text>
      <View style={styles.planFeaturesRow}>
        {features.map((f, i) => (
          <Text key={i} style={styles.planFeaturePill}>{f}</Text>
        ))}
      </View>
    </View>
  );
}

function FaqItem({ question, answer }) {
  const [open, setOpen] = React.useState(false);
  return (
    <TouchableOpacity
      style={styles.faqCard}
      onPress={() => setOpen(!open)}
      activeOpacity={0.7}
    >
      <View style={styles.faqHeader}>
        <Text style={styles.faqQuestion}>{question}</Text>
        <Text style={styles.faqIcon}>{open ? '−' : '+'}</Text>
      </View>
      {open && <Text style={styles.faqAnswer}>{answer}</Text>}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.gray50, padding: 16 },
  section: { marginBottom: 20 },
  sectionTitle: { fontSize: 18, fontWeight: '700', color: COLORS.primary, marginBottom: 12 },
  planCard: {
    backgroundColor: COLORS.white,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: COLORS.gray200,
    padding: 16,
    marginBottom: 10,
  },
  planFeatured: { borderColor: COLORS.accent },
  badgePop: {
    alignSelf: 'flex-start',
    backgroundColor: COLORS.accentLight,
    borderRadius: 100,
    paddingHorizontal: 10,
    paddingVertical: 2,
    marginBottom: 6,
  },
  badgePopText: { fontSize: 9, fontWeight: '700', color: COLORS.accentDark, textTransform: 'uppercase' },
  badgeVip: {
    alignSelf: 'flex-start',
    backgroundColor: COLORS.primaryUltra,
    borderRadius: 100,
    paddingHorizontal: 10,
    paddingVertical: 2,
    marginBottom: 6,
  },
  badgeVipText: { fontSize: 9, fontWeight: '700', color: COLORS.primary, textTransform: 'uppercase' },
  planCardName: { fontSize: 16, fontWeight: '700', color: COLORS.primary, marginBottom: 4 },
  planCardInitial: { fontSize: 13, color: COLORS.gray500, marginBottom: 8 },
  planFeaturesRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 6 },
  planFeaturePill: {
    fontSize: 11,
    color: COLORS.gray600,
    backgroundColor: COLORS.gray100,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 100,
  },
  ctaRow: { flexDirection: 'row', gap: 8, marginTop: 4 },
  ctaBtn: {
    flex: 1,
    backgroundColor: COLORS.accent,
    borderRadius: 8,
    padding: 12,
    alignItems: 'center',
  },
  ctaBtnText: { color: COLORS.white, fontWeight: '700', fontSize: 13 },
  ctaOutline: {
    flex: 1,
    borderWidth: 2,
    borderColor: COLORS.primary,
    borderRadius: 8,
    padding: 12,
    alignItems: 'center',
  },
  ctaOutlineText: { color: COLORS.primary, fontWeight: '600', fontSize: 13 },
  benefitsGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 10 },
  benefitCard: {
    width: '48%',
    backgroundColor: COLORS.white,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: COLORS.gray200,
    padding: 14,
    alignItems: 'center',
  },
  benefitIcon: { fontSize: 24 },
  benefitTitle: { fontSize: 12, fontWeight: '600', color: COLORS.primary, marginTop: 6, textAlign: 'center' },
  benefitDesc: { fontSize: 10, color: COLORS.gray500, marginTop: 2, textAlign: 'center' },
  commerceGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 10 },
  commerceCard: {
    width: '48%',
    backgroundColor: COLORS.gray100,
    borderRadius: 10,
    padding: 14,
    alignItems: 'center',
  },
  commerceIcon: { fontSize: 22 },
  commerceName: { fontSize: 12, fontWeight: '600', marginTop: 4, color: COLORS.dark },
  commerceDiscount: { fontSize: 12, fontWeight: '700', color: COLORS.accent, marginTop: 2 },
  commerceCat: { fontSize: 10, color: COLORS.gray400, marginTop: 2 },
  affiliateBanner: {
    backgroundColor: COLORS.primaryUltra,
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    marginTop: 12,
  },
  affiliateText: { fontSize: 12, color: COLORS.gray600, marginBottom: 8, textAlign: 'center' },
  affiliateBtn: {
    backgroundColor: COLORS.primary,
    borderRadius: 8,
    paddingVertical: 8,
    paddingHorizontal: 20,
  },
  affiliateBtnText: { color: COLORS.white, fontWeight: '600', fontSize: 12 },
  stepCard: {
    width: 130,
    backgroundColor: COLORS.white,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: COLORS.gray200,
    padding: 14,
    marginRight: 10,
    alignItems: 'center',
  },
  stepNum: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: COLORS.accent,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
  },
  stepNumText: { color: COLORS.white, fontWeight: '700', fontSize: 13 },
  stepTitle: { fontSize: 12, fontWeight: '600', color: COLORS.primary, textAlign: 'center' },
  stepDesc: { fontSize: 10, color: COLORS.gray500, marginTop: 2, textAlign: 'center' },
  faqCard: {
    backgroundColor: COLORS.white,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: COLORS.gray200,
    padding: 14,
    marginBottom: 8,
  },
  faqHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  faqQuestion: { fontSize: 13, fontWeight: '600', color: COLORS.dark, flex: 1 },
  faqIcon: { fontSize: 18, color: COLORS.accent, marginLeft: 8 },
  faqAnswer: { fontSize: 12, color: COLORS.gray600, marginTop: 8, lineHeight: 18 },
  footerBtn: {
    backgroundColor: COLORS.primary,
    borderRadius: 10,
    padding: 14,
    alignItems: 'center',
    marginBottom: 20,
  },
  footerBtnText: { color: COLORS.white, fontSize: 14, fontWeight: '600' },
});
