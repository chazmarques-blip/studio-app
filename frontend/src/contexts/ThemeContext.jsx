import { createContext, useContext, useEffect, useState, useCallback } from 'react';

const ThemeContext = createContext({ theme: 'light', toggle: () => {}, set: () => {} });

// NOTE: dark mode is currently a partial implementation (only Sidebar + AppHeader have
// dark: variants — all studio content uses light-mode-only colors). Forcing 'light'
// globally until full dark-mode support is rolled out across DirectedStudio, StudioPage,
// BookStudio, BookEditorPage, etc.
const FORCE_LIGHT = true;

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState('light');

  useEffect(() => {
    const root = document.documentElement;
    // Always remove the `dark` class while FORCE_LIGHT is active, so any stale
    // localStorage `studiox_theme=dark` from previous sessions is cleaned up.
    root.classList.remove('dark');
    if (!FORCE_LIGHT && theme === 'dark') root.classList.add('dark');
  }, [theme]);

  const toggle = useCallback(() => {
    if (FORCE_LIGHT) return; // no-op until dark mode is fully implemented
    setTheme((t) => (t === 'dark' ? 'light' : 'dark'));
  }, []);
  const set = useCallback((t) => {
    if (FORCE_LIGHT) { setTheme('light'); return; }
    setTheme(t === 'dark' ? 'dark' : 'light');
  }, []);

  return (
    <ThemeContext.Provider value={{ theme, toggle, set, forceLight: FORCE_LIGHT }}>
      {children}
    </ThemeContext.Provider>
  );
}

export const useTheme = () => useContext(ThemeContext);
