/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
      "./src/**/*.{html,js}", // Adjust to match your file structure
    ],
    theme: {
      extend: {
        keyframes: {
          typewriter: {
            '0%': { width: '0%' },
            '100%': { width: '100%' },
          },
          blink: {
            '0%': { borderColor: 'transparent' },
            '50%': { borderColor: 'black' },
          },
        },
        animation: {
          typewriter: 'typewriter 4s steps(40, end) 1s 1 normal both',
          blink: 'blink .75s step-end infinite',
        },
        fontFamily: {
          typewriter: ['"Courier New"', 'Courier', 'monospace'],
        },
      },
    },
    plugins: [],
  }
  