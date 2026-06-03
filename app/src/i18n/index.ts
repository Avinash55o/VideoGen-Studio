import i18n from 'i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import { initReactI18next } from 'react-i18next';
import en from './locales/en/translation.json';

export const SUPPORTED_LANGUAGES = [
  { code: 'en', label: 'English' },
] as const;

export type LanguageCode = (typeof SUPPORTED_LANGUAGES)[number]['code'];

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: en },
    },
    fallbackLng: 'en',
    supportedLngs: SUPPORTED_LANGUAGES.map((l) => l.code),
    load: 'currentOnly',
    interpolation: { escapeValue: false },
    react: { useSuspense: false },
    detection: {
      order: ['localStorage', 'navigator'],
      lookupLocalStorage: 'videogen:lang',
      caches: ['localStorage'],
    },
  });

export default i18n;
