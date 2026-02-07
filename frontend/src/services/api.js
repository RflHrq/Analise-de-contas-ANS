import axios from 'axios';

// Configuração da instância do Axios para comunicação com a API Backend
const baseURL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api';
console.log('🔌 Conectando à API em:', baseURL); // Debug para verificar em produção

const api = axios.create({
    baseURL: baseURL, // URL via variável de ambiente (Vercel) ou Local
    timeout: 10000,   // Timeout de 10 segundos
});

export default {
    /**
     * Obtém os dados completos do Dashboard (Storytelling).
     * Retorna métricas macro, gráficos geográficos, top movers, etc.
     */
    getDashboardData() {
        return api.get('/analytics/storytelling');
    },

    /**
     * Obtém a lista paginada de operadoras.
     * @param {number} page - Número da página atual
     * @param {number} limit - Limite de itens por página
     * @param {string} search - Termo de busca (opcional)
     */
    getOperators(page, limit, search) {
        return api.get('/operadoras', {
            params: { page, limit, search }
        });
    },

    /**
     * Obtém o detalhamento de despesas de uma operadora específica.
     * @param {string} cnpj - CNPJ da operadora
     */
    getOperatorExpenses(cnpj) {
        return api.get(`/operadoras/${cnpj}/despesas`);
    },

    /**
     * Envia uma pergunta para o Analista de IA.
     * @param {string} question - Pergunta em linguagem natural
     */
    askAI(question) {
        return api.post('/ai/ask', { question });
    }
};