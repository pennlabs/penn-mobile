/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx}',
    './components/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        'work-sans': ['"Work Sans"', 'sans-serif'],
      },
      colors: {
        white: '#ffffff',
        yellow: '#F2C94C',
        orange: '#f2994a',
        lightRed: '#EED4D4',
        red: '#EB9387',
        darkRed: '#AE2727',
        purple: '#a98abf',
        lightBlue: '#d3e3f5',
        mediumBlue: '#2175cb',
        imageBlue: '#2D9CDB',
        navBackground: '#ffffff',
        navProfileBackground: '#D3E3F566',
        gray: '#999999',
        lighterGray: '#e5e5e5',
        lightGray: '#bdbdbd',
        darkGray: '#828282',
        lightGreen: '#D4EEDF',
        green: '#3faa6d',
      },
    },
  },
  plugins: [],
}
