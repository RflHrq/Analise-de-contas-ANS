import { createApp } from 'vue'
import App from './App.vue'

// Importações de Estilo e Frameworks
import 'bootstrap/dist/css/bootstrap.min.css' // CSS do Bootstrap
import 'bootstrap'                            // Scripts JavaScript do Bootstrap (Modais, Tooltips, etc)

// Importações de Estilos Personalizados da Aplicação
import './assets/dark-theme.css' // Definições de variáveis de tema (Dark/Light)
import './style.css'             // Estilos globais e componentes customizados (Glass Card, Overlays)

// Inicialização da Aplicação Vue
createApp(App).mount('#app')