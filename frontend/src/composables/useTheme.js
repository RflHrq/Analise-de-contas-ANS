// src/composables/useTheme.js
import { ref, onMounted } from 'vue';

const isDarkMode = ref(false);

export function useTheme() {
    
    // Alterna o tema
    const toggleTheme = () => {
        isDarkMode.value = !isDarkMode.value;
        updateDOM();
    };

    // Atualiza o HTML e LocalStorage
    const updateDOM = () => {
        const theme = isDarkMode.value ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('user-theme', theme);
    };

    // Inicializa verificando preferência salva ou do sistema
    onMounted(() => {
        const savedTheme = localStorage.getItem('user-theme');
        if (savedTheme) {
            isDarkMode.value = savedTheme === 'dark';
        } else {
            // Verifica preferência do sistema operacional
            isDarkMode.value = window.matchMedia('(prefers-color-scheme: dark)').matches;
        }
        updateDOM();
    });

    return { isDarkMode, toggleTheme };
}