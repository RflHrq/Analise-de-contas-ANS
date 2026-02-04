<template>
  <div class="card shadow-sm metric-card glass-card" :style="{ borderLeftColor: color }">
    <div class="card-body">
      <!-- Título do KPI (Ex: Receita Total) -->
      <h6 class="text-white opacity-75 text-uppercase small">{{ title }}</h6>
      
      <!-- Valor Formatado (Ex: R$ 1.500,00) -->
      <h3 class="fw-bold mb-0">{{ formattedValue }}</h3>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

// Definição das propriedades do componente
const props = defineProps({
  title: String,
  value: Number,
  color: { type: String, default: '#0d6efd' } // Azul como padrão
});

// Formata o valor numérico para Moeda Brasileira (BRL)
const formattedValue = computed(() => {
  if (props.value === null || props.value === undefined) return '...';
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(props.value);
});
</script>

<style scoped>
/* 
  Estilo Específico do Cartão de Métrica 
  Adiciona uma borda esquerda colorida e efeito de hover.
*/
.metric-card { 
  border-left: 4px solid; 
  transition: transform 0.2s; 
}

.metric-card:hover { 
  transform: translateY(-3px); /* Leve elevação ao passar o mouse */
}
</style>