/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        vault: {
          bg: 'var(--bg-primary)',
          card: 'var(--bg-card)',
          sidebar: 'var(--bg-sidebar)',
          hover: 'var(--bg-hover)',
          text: 'var(--text-primary)',
          'text-secondary': 'var(--text-secondary)',
          'text-muted': 'var(--text-muted)',
          accent: 'var(--accent)',
          'accent-hover': 'var(--accent-hover)',
          'accent-light': 'var(--accent-light)',
          success: 'var(--success)',
          'success-light': 'var(--success-light)',
          danger: 'var(--danger)',
          'danger-light': 'var(--danger-light)',
          warning: 'var(--warning)',
          'warning-light': 'var(--warning-light)',
          border: 'var(--border)',
          'border-light': 'var(--border-light)',
        },
      },
      fontFamily: {
        display: ['Playfair Display', 'Georgia', 'serif'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        'vault-sm': 'var(--shadow-sm)',
        'vault-md': 'var(--shadow-md)',
        'vault-lg': 'var(--shadow-lg)',
      },
      borderRadius: {
        'vault': '16px',
        'vault-sm': '12px',
        'vault-xs': '8px',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-in': 'slideIn 0.3s ease-out',
        'scale-in': 'scaleIn 0.2s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideIn: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(0)' },
        },
        scaleIn: {
          '0%': { transform: 'scale(0.95)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
