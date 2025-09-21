import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './app/**/*.{ts,tsx,js,jsx,mdx}',
    './components/**/*.{ts,tsx,js,jsx,mdx}',
    './pages/**/*.{ts,tsx,js,jsx,mdx}',
    './src/**/*.{ts,tsx,js,jsx,mdx}',
    // Also scan the parent repo for shared components
    '../components/**/*.{ts,tsx,js,jsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        googleBlue: '#1A73E8',
      },
      borderRadius: {
        'xl': '1rem',
        '2xl': '1.25rem',
        '3xl': '1.5rem',
      },
      boxShadow: {
        'md3': '0 1px 3px rgba(0,0,0,0.08)'
      },
      animation: {
        bounce: 'bounce 1s infinite',
      },
    },
  },
  plugins: [],
}
export default config
