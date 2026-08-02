// ============================================================
// AppNavigator — Navegación principal (Tabs + Stack)
// ============================================================

import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { COLORS } from '../utils/constants';
import { initAuth, isAuthenticated, onAuthChange } from '../services/auth';
import { getCart, saveCart } from '../utils/storage';

// Screens
import LoginScreen from '../screens/LoginScreen';
import HomeScreen from '../screens/HomeScreen';
import CatalogScreen from '../screens/CatalogScreen';
import CartScreen from '../screens/CartScreen';
import CreditScreen from '../screens/CreditScreen';
import ClubScreen from '../screens/ClubScreen';
import ProfileScreen from '../screens/ProfileScreen';
import OrdersScreen from '../screens/OrdersScreen';
import PaymentScreen from '../screens/PaymentScreen';
import ProductDetailScreen from '../screens/ProductDetailScreen';

const Tab = createBottomTabNavigator();
const Stack = createNativeStackNavigator();

// Iconos para tabs
const TAB_ICONS = {
  Home: '🏠',
  Catalog: '🛍️',
  Cart: '🛒',
  Profile: '👤',
};

function TabIcon({ label, focused, badge }) {
  const icon = TAB_ICONS[label] || '📄';
  return (
    <View style={tabIconStyles.container}>
      <Text style={[tabIconStyles.icon, focused && tabIconStyles.active]}>
        {icon}
      </Text>
      {badge != null && badge > 0 && (
        <View style={tabIconStyles.badge}>
          <Text style={tabIconStyles.badgeText}>
            {badge > 99 ? '99+' : badge}
          </Text>
        </View>
      )}
    </View>
  );
}

const tabIconStyles = StyleSheet.create({
  container: { position: 'relative', alignItems: 'center', justifyContent: 'center' },
  icon: { fontSize: 22 },
  active: { transform: [{ scale: 1.1 }] },
  badge: {
    position: 'absolute',
    top: -4,
    right: -8,
    backgroundColor: COLORS.danger,
    minWidth: 16,
    height: 16,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 3,
  },
  badgeText: { color: COLORS.white, fontSize: 9, fontWeight: '700' },
});

export default function AppNavigator() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [initializing, setInitializing] = useState(true);
  const [cart, setCart] = useState([]);

  // Inicializar auth y carrito
  useEffect(() => {
    (async () => {
      await initAuth();
      setIsLoggedIn(isAuthenticated());
      const savedCart = await getCart();
      setCart(savedCart || []);
      setInitializing(false);
    })();
  }, []);

  // Escuchar cambios de auth
  useEffect(() => {
    const unsub = onAuthChange((user) => {
      setIsLoggedIn(!!user);
    });
    return unsub;
  }, []);

  // Persistir carrito
  useEffect(() => {
    saveCart(cart);
  }, [cart]);

  const addToCart = useCallback((product) => {
    setCart((prev) => {
      const existing = prev.find((item) => item.id === product.id);
      if (existing) {
        return prev.map((item) =>
          item.id === product.id ? { ...item, qty: (item.qty || 1) + 1 } : item
        );
      }
      return [
        ...prev,
        {
          id: product.id,
          name: product.name,
          price: product.list_price || 0,
          qty: 1,
        },
      ];
    });
  }, []);

  const updateCartQty = useCallback((productId, delta) => {
    setCart((prev) =>
      prev
        .map((item) =>
          item.id === productId
            ? { ...item, qty: Math.max(1, (item.qty || 1) + delta) }
            : item
        )
    );
  }, []);

  const removeFromCart = useCallback((productId) => {
    setCart((prev) => prev.filter((item) => item.id !== productId));
  }, []);

  const clearCart = useCallback(() => {
    setCart([]);
  }, []);

  const cartCount = cart.reduce((sum, item) => sum + (item.qty || 1), 0);

  if (initializing) {
    return (
      <View style={styles.splash}>
        <Text style={styles.splashLogo}>
          Latin<Text style={styles.splashAccent}>Bien</Text>
        </Text>
      </View>
    );
  }

  if (!isLoggedIn) {
    return <LoginScreen onLoginSuccess={() => setIsLoggedIn(true)} />;
  }

  // Componente para las tabs principales
  function MainTabs() {
    return (
      <Tab.Navigator
        screenOptions={({ route }) => ({
          tabBarIcon: ({ focused }) => (
            <TabIcon
              label={route.name}
              focused={focused}
              badge={route.name === 'Cart' ? cartCount : undefined}
            />
          ),
          tabBarActiveTintColor: COLORS.primary,
          tabBarInactiveTintColor: COLORS.gray400,
          tabBarStyle: styles.tabBar,
          tabBarLabelStyle: styles.tabLabel,
          headerStyle: styles.header,
          headerTitleStyle: styles.headerTitle,
          headerTintColor: COLORS.primary,
        })}
      >
        <Tab.Screen name="Home" options={{ title: 'Inicio' }}>
          {(props) => (
            <HomeScreen {...props} onAddToCart={addToCart} />
          )}
        </Tab.Screen>
        <Tab.Screen name="Catalog" options={{ title: 'Catálogo' }}>
          {(props) => (
            <CatalogScreen {...props} onAddToCart={addToCart} />
          )}
        </Tab.Screen>
        <Tab.Screen name="Cart" options={{ title: 'Carrito' }}>
          {() => (
            <CartScreen
              cart={cart}
              onUpdateQty={updateCartQty}
              onRemove={removeFromCart}
              onClear={clearCart}
            />
          )}
        </Tab.Screen>
        <Tab.Screen
          name="Profile"
          options={{ title: 'Perfil' }}
        >
          {(props) => (
            <ProfileScreen
              {...props}
              onLogout={() => setIsLoggedIn(false)}
            />
          )}
        </Tab.Screen>
      </Tab.Navigator>
    );
  }

  return (
    <NavigationContainer>
      <Stack.Navigator
        screenOptions={{
          headerStyle: styles.header,
          headerTitleStyle: styles.headerTitle,
          headerTintColor: COLORS.primary,
          headerBackTitleVisible: false,
        }}
      >
        <Stack.Screen
          name="MainTabs"
          component={MainTabs}
          options={{ headerShown: false }}
        />
        <Stack.Screen
          name="Orders"
          component={OrdersScreen}
          options={{ title: 'Mis Contratos' }}
        />
        <Stack.Screen
          name="Credit"
          component={CreditScreen}
          options={{ title: 'Líneas de Crédito' }}
        />
        <Stack.Screen
          name="Club"
          component={ClubScreen}
          options={{ title: 'Club LatinBien' }}
        />
        <Stack.Screen
          name="Payment"
          component={PaymentScreen}
          options={{ title: 'Reportar Pago' }}
        />
        <Stack.Screen
          name="ProductDetail"
          component={ProductDetailScreen}
          options={{ title: 'Detalle del Producto' }}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
}

const styles = StyleSheet.create({
  splash: {
    flex: 1,
    backgroundColor: COLORS.primary,
    justifyContent: 'center',
    alignItems: 'center',
  },
  splashLogo: {
    fontSize: 42,
    fontWeight: '800',
    color: COLORS.white,
    letterSpacing: -1,
  },
  splashAccent: { color: COLORS.accent },
  tabBar: {
    backgroundColor: COLORS.white,
    borderTopWidth: 1,
    borderTopColor: COLORS.gray200,
    paddingTop: 4,
    height: 60,
  },
  tabLabel: { fontSize: 10, fontWeight: '500' },
  header: {
    backgroundColor: COLORS.white,
    elevation: 1,
    shadowOpacity: 0,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.primary,
  },
});
