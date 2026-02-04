<template>
  <div class="ai-widget-container">
    
    <!-- Janela do Chat -->
    <div v-if="isOpen" class="card glass-card chat-window d-flex flex-column" style="--glass-bg: var(--bg-card);">

      <!-- Cabeçalho -->
      <div class="card-header bg-transparent d-flex justify-content-between align-items-center py-3">
        <div class="d-flex align-items-center gap-2">
          <span class="fs-4">🤖</span>
          <div class="text-start">
            <h6 class="mb-0 fw-bold">Analista IA da ANS</h6>
            <small class="text-muted" style="font-size: 0.7rem;">Powered by Llama 3 & Groq</small>
          </div>
        </div>
        <button class="btn btn-sm btn-link text-reset text-decoration-none" @click="isOpen = false">✕</button>
      </div>

      <!-- Corpo do Chat (Mensagens) -->
      <div class="card-body overflow-auto flex-grow-1 p-3" ref="chatBody">
        <!-- Estado Inicial (Vazio) -->
        <div v-if="messages.length === 0" class="text-center text-muted mt-5">
          <p class="mb-2">👋 Olá! Sou sua IA de dados.</p>
          <small>Pergunte algo como:<br>"Qual o total de despesas da Unimed?"<br>"Top 5 gastos por estado"</small>
        </div>

        <!-- Lista de Mensagens -->
        <div v-for="(msg, i) in messages" :key="i" class="mb-3 d-flex" :class="msg.isUser ? 'justify-content-end' : 'justify-content-start'">
          <div class="p-3 rounded-3 shadow-sm" :class="msg.isUser ? 'bg-primary text-white msg-user' : 'chat-response-ai'">
            
            <!-- Texto da Mensagem -->
            <p class="mb-0 small" v-if="msg.text">{{ msg.text }}</p>
            
            <!-- Tabela de Dados (se houver) -->
            <div v-if="msg.data && msg.data.length > 0" class="mt-2">
              <div class="table-responsive rounded border" style="max-height: 200px;">
                <table class="table table-sm mb-0 small" style="font-size: 0.75rem;">
                  <thead>
                    <tr>
                      <th v-for="key in Object.keys(msg.data[0])" :key="key">{{ key }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(row, idx) in msg.data" :key="idx">
                      <td v-for="val in row" :key="val">{{ formatVal(val) }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <!-- Mostra o SQL gerado para transparência -->
              <small class="d-block mt-1 text-muted fst-italic" style="font-size: 0.65rem;">
                SQL: {{ msg.sql }}
              </small>
            </div>

             <!-- Mensagem de Erro -->
             <p v-if="msg.error" class="mb-0 small text-danger">⚠️ {{ msg.error }}</p>

          </div>
        </div>
        
        <!-- Indicador de "Pensando..." -->
        <div v-if="isThinking" class="text-start">
           <span class="badge bg-secondary animate-pulse">Digitando SQL...</span>
        </div>
      </div>

      <!-- Rodapé (Input) -->
      <div class="card-footer bg-transparent p-2">
        <form @submit.prevent="sendMessage" class="d-flex gap-2">
          <input v-model="userInput" type="text" class="form-control form-control-sm chat-input" placeholder="Faça uma pergunta aos dados..." :disabled="isThinking">
          <button type="submit" class="btn btn-sm btn-primary" :disabled="!userInput || isThinking">➤</button>
        </form>
      </div>
    </div>

    <!-- Botão de Abrir/Fechar Widget -->
    <button class="btn btn-primary rounded-circle shadow-lg ai-launcher" @click="isOpen = !isOpen">
      <span class="fs-4">✨</span>
    </button>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue';
import axios from 'axios';

// Estado das Mensagens
const messages = ref([]);

// Constantes e Refs de Controle de Interface
const isOpen = ref(false);
const userInput = ref('');
const isThinking = ref(false);
const chatBody = ref(null);

/**
 * Formata valores numéricos (moeda compacta) para exibição nas tabelas da IA.
 */
const formatVal = (val) => {
    if (typeof val === 'number') {
        if (val > 1000) return new Intl.NumberFormat('pt-BR', { notation: "compact", maximumFractionDigits: 1 }).format(val);
        return val;
    }
    return val;
}

/**
 * Envia a pergunta do usuário para o backend (Agente SQL).
 */
const sendMessage = async () => {
    if (!userInput.value.trim()) return;

    const question = userInput.value;
    
    // 1. Adiciona pergunta à interface imediatamente
    messages.value.push({ isUser: true, text: question });
    userInput.value = '';
    isThinking.value = true;
    scrollToBottom();

    try {
        // 2. Chama API Backend (Analista SQL)
        const res = await axios.post('http://127.0.0.1:8000/api/ai/ask', { question });
        
        const result = res.data;

        if (result.error) {
            messages.value.push({ isUser: false, error: result.error });
        } else {
            // Sucesso: Renderiza os dados retornados
            messages.value.push({ 
                isUser: false, 
                text: `Encontrei ${result.count} resultados:`,
                data: result.data,
                sql: result.sql 
            });
        }
    } catch (e) {
        messages.value.push({ isUser: false, error: "Erro de conexão com o cérebro da IA." });
    } finally {
        isThinking.value = false;
        scrollToBottom();
    }
};

/**
 * Rola o chat para a última mensagem.
 */
const scrollToBottom = async () => {
    await nextTick();
    if (chatBody.value) chatBody.value.scrollTop = chatBody.value.scrollHeight;
};
</script>

<style scoped>
/* Container fixo no canto da tela */
.ai-widget-container {
    position: fixed;
    bottom: 30px;
    right: 30px;
    z-index: 9999;
    font-family: 'Inter', sans-serif;
}

/* Botão Flutuante (Launcher) */
.ai-launcher {
    width: 60px;
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: transform 0.2s;
}
.ai-launcher:hover { transform: scale(1.1); }

/* Janela Principal do Chat */
.chat-window {
    position: absolute;
    bottom: 80px;
    right: 0;
    width: 380px;
    height: 500px;
    
    /* Layout */
    border-radius: 16px;
    overflow: hidden;
    animation: slideUp 0.3s ease-out;
}

/* Balão do Usuário (O da IA usa classe global .chat-response-ai) */
.msg-user { border-bottom-right-radius: 0; max-width: 85%; }

/* Animação de Entrada */
@keyframes slideUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Scrollbar Personalizada */
::-webkit-scrollbar { width: 6px; }

/* Scrollbar Light Mode */
::-webkit-scrollbar-thumb { 
    background: #cbd5e1; 
    border-radius: 3px; 
}

/* Scrollbar Dark Mode */
:global([data-theme="dark"]) ::-webkit-scrollbar-thumb {
    background: #475569 !important;
}

/* Input de Texto do Chat */
.chat-input {
    background-color: #ffffff;
    color: #334155;
    border-color: #dee2e6;
}

.chat-input::placeholder {
    color: #94a3b8;
}

/* Input Dark Mode */
:global([data-theme="dark"]) .chat-input {
    background-color: rgba(15, 23, 42, 0.6) !important;
    color: #ffffff !important;
    border-color: rgba(255, 255, 255, 0.2) !important;
}

:global([data-theme="dark"]) .chat-input::placeholder {
    color: rgba(255, 255, 255, 0.5);
}
</style>