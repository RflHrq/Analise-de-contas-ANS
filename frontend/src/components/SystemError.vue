<template>
  <div class="system-error-overlay">
    <div class="error-content text-center">
      <div class="icon-container mb-4">
        <div class="pulse-ring"></div>
        <span class="error-icon">⚠️</span>
      </div>
      
      <h2 class="display-5 fw-bold text-white mb-3">Sistema Indisponível</h2>
      
      <p class="lead text-light opacity-75 mb-4" style="max-width: 500px; margin: 0 auto;">
        Não foi possível conectar ao servidor de dados. Isso pode ser uma instabilidade temporária ou manutenção programada.
      </p>

      <button @click="reloadPage" class="btn btn-lg btn-light rounded-pill px-5 fw-bold shadow-lg hover-effect">
        <span v-if="!reloading">🔄 Tentar Novamente</span>
        <span v-else>Conectando...</span>
      </button>

      <div class="mt-4 text-white-50 small">
        Código do Erro: CONNECTION_REFUSED
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const reloading = ref(false);

const reloadPage = () => {
  reloading.value = true;
  // Pequeno delay para feedback visual antes do reload real
  setTimeout(() => {
    window.location.reload();
  }, 800);
};
</script>

<style scoped>
.system-error-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: radial-gradient(circle at center, #2c3e50 0%, #000000 100%);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(10px);
}

.error-content {
  animation: fadeIn 0.8s ease-out;
}

.icon-container {
  position: relative;
  width: 100px;
  height: 100px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: center;
}

.error-icon {
  font-size: 4rem;
  position: relative;
  z-index: 2;
}

.pulse-ring {
  position: absolute;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  border: 4px solid rgba(255, 193, 7, 0.5); /* Amarelo de alerta */
  animation: pulse 2s infinite;
}

.hover-effect {
  transition: transform 0.2s, box-shadow 0.2s;
}

.hover-effect:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(0,0,0,0.3);
}

@keyframes pulse {
  0% { transform: scale(0.8); opacity: 1; }
  100% { transform: scale(1.5); opacity: 0; }
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
