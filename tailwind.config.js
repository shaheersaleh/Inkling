/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/templates/**/*.html",
    "./app/static/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        'lapis_lazuli': { 
          DEFAULT: '#2f6690', 
          100: '#09141c', 
          200: '#122839', 
          300: '#1c3c55', 
          400: '#255172', 
          500: '#2f6690', 
          600: '#3e87bf', 
          700: '#6da5d0', 
          800: '#9ec3e0', 
          900: '#cee1ef' 
        }, 
        'cerulean': { 
          DEFAULT: '#3a7ca5', 
          100: '#0c1921', 
          200: '#173242', 
          300: '#234b64', 
          400: '#2f6485', 
          500: '#3a7ca5', 
          600: '#569ac4', 
          700: '#80b3d2', 
          800: '#aacce1', 
          900: '#d5e6f0' 
        }, 
        'platinum': { 
          DEFAULT: '#d9dcd6', 
          100: '#2b2f28', 
          200: '#575e50', 
          300: '#828c78', 
          400: '#adb4a7', 
          500: '#d9dcd6', 
          600: '#e0e3de', 
          700: '#e8eae6', 
          800: '#f0f1ee', 
          900: '#f7f8f7' 
        }, 
        'indigo_dye': { 
          DEFAULT: '#16425b', 
          100: '#040d12', 
          200: '#091a24', 
          300: '#0d2736', 
          400: '#123448', 
          500: '#16425b', 
          600: '#256f9a', 
          700: '#3f9bd0', 
          800: '#7fbce0', 
          900: '#bfdeef' 
        }, 
        'sky_blue': { 
          DEFAULT: '#81c3d7', 
          100: '#102c34', 
          200: '#215768', 
          300: '#31839c', 
          400: '#4ba9c6', 
          500: '#81c3d7', 
          600: '#99cedf', 
          700: '#b2dbe7', 
          800: '#cce7ef', 
          900: '#e5f3f7' 
        }
      },
      fontFamily: {
        'apricot': ['Apricot', 'serif'],
        'sans': ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif']
      },
      backgroundImage: {
        'gradient-inkling': 'linear-gradient(135deg, #16425b, #2f6690, #3a7ca5, #81c3d7, #d9dcd6)',
        'gradient-inkling-reverse': 'linear-gradient(135deg, #d9dcd6, #81c3d7, #3a7ca5, #2f6690, #16425b)',
        'gradient-inkling-horizontal': 'linear-gradient(90deg, #16425b, #2f6690, #3a7ca5, #81c3d7, #d9dcd6)'
      },
      borderRadius: {
        'full': '9999px',
      }
    },
  },
  plugins: [],
}
