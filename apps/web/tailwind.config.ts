import type { Config } from 'tailwindcss';

const config: Config = {
  darkMode: 'class',
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
    './src/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        'background': '#0d1516',
        'surface': '#0d1516',
        'surface-dim': '#0d1516',
        'surface-bright': '#333a3c',
        'surface-container-lowest': '#080f11',
        'surface-container-low': '#151d1e',
        'surface-container': '#192122',
        'surface-container-high': '#242b2d',
        'surface-container-highest': '#2e3638',
        'surface-variant': '#2e3638',
        'on-surface': '#dce4e5',
        'on-surface-variant': '#bac9cc',
        'inverse-surface': '#dce4e5',
        'inverse-on-surface': '#2a3233',
        'on-background': '#dce4e5',
        'outline': '#849396',
        'outline-variant': '#3b494c',
        'surface-tint': '#00daf3',

        // Primary Accent (Electric Cyan)
        'primary': '#c3f5ff',
        'on-primary': '#00363d',
        'primary-container': '#00e5ff',
        'on-primary-container': '#00626e',
        'inverse-primary': '#006875',
        'primary-fixed': '#9cf0ff',
        'primary-fixed-dim': '#00daf3',
        'on-primary-fixed': '#001f24',
        'on-primary-fixed-variant': '#004f58',

        // Secondary Accent (Deep Violet)
        'secondary': '#cdbdff',
        'on-secondary': '#370096',
        'secondary-container': '#5203d5',
        'on-secondary-container': '#c0acff',
        'secondary-fixed': '#e8deff',
        'secondary-fixed-dim': '#cdbdff',
        'on-secondary-fixed': '#20005f',
        'on-secondary-fixed-variant': '#4f00d0',

        // Tertiary / Warning (Amber)
        'tertiary': '#ffeac0',
        'on-tertiary': '#3e2e00',
        'tertiary-container': '#fec931',
        'on-tertiary-container': '#6f5500',
        'tertiary-fixed': '#ffdf96',
        'tertiary-fixed-dim': '#f3bf26',
        'on-tertiary-fixed': '#251a00',
        'on-tertiary-fixed-variant': '#594400',

        // Error (Crimson Red)
        'error': '#ffb4ab',
        'on-error': '#690005',
        'error-container': '#93000a',
        'on-error-container': '#ffdad6',
      },
      spacing: {
        'unit': '4px',
        'gutter': '1px',
        'margin-compact': '8px',
        'panel-padding': '12px',
        'container-gap': '4px',
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
        'body-sm': ['Inter', 'sans-serif'],
        'headline-md': ['Inter', 'sans-serif'],
        'display-lg': ['Inter', 'sans-serif'],
        'label-xs': ['Inter', 'sans-serif'],
        'data-sm': ['JetBrains Mono', 'monospace'],
        'data-md': ['JetBrains Mono', 'monospace'],
        'data-lg': ['JetBrains Mono', 'monospace'],
      },
      fontSize: {
        'label-xs': ['10px', { lineHeight: '12px', letterSpacing: '0.05em', fontWeight: '700' }],
        'data-sm': ['11px', { lineHeight: '14px', fontWeight: '400' }],
        'body-sm': ['13px', { lineHeight: '18px', fontWeight: '400' }],
        'data-md': ['14px', { lineHeight: '20px', fontWeight: '500' }],
        'data-lg': ['18px', { lineHeight: '24px', letterSpacing: '-0.02em', fontWeight: '600' }],
        'headline-md': ['20px', { lineHeight: '28px', letterSpacing: '-0.01em', fontWeight: '600' }],
        'display-lg': ['32px', { lineHeight: '40px', letterSpacing: '-0.02em', fontWeight: '700' }],
      },
      borderRadius: {
        'none': '0px',
        'sm': '2px',
        DEFAULT: '2px',
        'md': '4px',
        'lg': '6px',
      },
      boxShadow: {
        'glow-primary': '0 0 15px rgba(0, 229, 255, 0.15)',
        'glow-primary-lg': '0 0 25px rgba(0, 229, 255, 0.3)',
        'glow-secondary': '0 0 15px rgba(82, 3, 213, 0.3)',
        'glow-tertiary': '0 0 15px rgba(254, 201, 49, 0.3)',
        'glow-error': '0 0 15px rgba(255, 180, 171, 0.3)',
      },
    },
  },
  plugins: [],
};

export default config;
