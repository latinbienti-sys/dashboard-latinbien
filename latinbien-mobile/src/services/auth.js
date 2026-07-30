// ============================================================
// LatinBien Mobile — Auth Service
// ============================================================

import AsyncStorage from '@react-native-async-storage/async-storage';
import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';
import { STORAGE_KEYS } from '../utils/constants';
import * as api from './api';

// En web, usar AsyncStorage. En nativo, SecureStore para datos sensibles
const setSecureItem = async (key, value) => {
  try {
    if (Platform.OS === 'web') {
      await AsyncStorage.setItem(key, value);
    } else {
      await SecureStore.setItemAsync(key, value);
    }
  } catch (_) {
    // Fallback
    await AsyncStorage.setItem(key, value);
  }
};

const getSecureItem = async (key) => {
  try {
    if (Platform.OS === 'web') {
      return await AsyncStorage.getItem(key);
    }
    return await SecureStore.getItemAsync(key);
  } catch (_) {
    return await AsyncStorage.getItem(key);
  }
};

const removeSecureItem = async (key) => {
  try {
    if (Platform.OS === 'web') {
      await AsyncStorage.removeItem(key);
    } else {
      await SecureStore.deleteItemAsync(key);
    }
  } catch (_) {
    await AsyncStorage.removeItem(key);
  }
};

// ============================================================

let _currentUser = null;
let _listeners = [];

function notifyListeners(user) {
  _listeners.forEach((fn) => {
    try {
      fn(user);
    } catch (_) {}
  });
}

export function onAuthChange(fn) {
  _listeners.push(fn);
  return () => {
    _listeners = _listeners.filter((f) => f !== fn);
  };
}

export async function initAuth() {
  try {
    const stored = await getSecureItem(STORAGE_KEYS.SESSION);
    if (stored) {
      _currentUser = JSON.parse(stored);
      if (_currentUser?.partner_id) {
        api.setPartnerId(_currentUser.partner_id);
      }
    }
  } catch (_) {
    _currentUser = null;
  }
  return _currentUser;
}

async function persistUser(user) {
  _currentUser = user;
  if (user) {
    await setSecureItem(STORAGE_KEYS.SESSION, JSON.stringify(user));
    if (user.partner_id) {
      api.setPartnerId(user.partner_id);
    }
  } else {
    await removeSecureItem(STORAGE_KEYS.SESSION);
    api.setPartnerId(null);
  }
  notifyListeners(user);
}

export async function checkSession() {
  try {
    const info = await api.getSessionInfo();
    if (info && info.uid) {
      const user = {
        uid: info.uid,
        name: info.name || 'Usuario',
        username: info.username || '',
        partner_id: info.partner_id,
        db: info.db,
      };
      await persistUser(user);
      return user;
    }
  } catch (_) {}
  await persistUser(null);
  return null;
}

export async function login(login, password) {
  const result = await api.login(login, password);
  if (result?.uid) {
    const user = {
      uid: result.uid,
      name: result.name || login,
      username: result.username || login,
      partner_id: result.partner_id,
      db: result.db,
    };
    await persistUser(user);
    return user;
  }
  throw new Error('Credenciales inválidas');
}

export async function logout() {
  try {
    await api.logout();
  } catch (_) {}
  await persistUser(null);
}

export function getCurrentUser() {
  return _currentUser;
}

export function isAuthenticated() {
  return _currentUser !== null && !!_currentUser.uid;
}

export function getPartnerId() {
  return _currentUser?.partner_id || null;
}
