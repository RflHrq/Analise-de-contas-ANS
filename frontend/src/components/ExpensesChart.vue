<template>
  <div class="card shadow-sm h-100 glass-card">
    <div class="card-header fw-bold">📍 Distribuição de Despesas por UF (Top 10)</div>
    <div class="card-body">
      <div class="chart-container" style="position: relative; height: 300px; width: 100%;">
        <canvas ref="chartCanvas"></canvas>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue';
import Chart from 'chart.js/auto';

// Definição das propriedades recebidas
const props = defineProps({
  data: {
    type: Array,
    default: () => []
  }
});

// Referência ao elemento Canvas no DOM
const chartCanvas = ref(null);
let chartInstance = null;

/**
 * Função responsável por renderizar o gráfico de barras.
 * Destroi instância anterior se existir para evitar vazamento de memória.
 */
const renderChart = async () => {
  // Aguarda o DOM estar pronto e valida existência do canvas e dados
  await nextTick();
  if (!chartCanvas.value) return;
  if (!props.data || props.data.length === 0) return;

  // Limpa gráfico anterior
  if (chartInstance) {
    chartInstance.destroy();
  }

  // Prepara dados para o Chart.js
  const labels = props.data.map(d => d.uf);
  const values = props.data.map(d => d.total);

  // Criação da nova instância do gráfico
  chartInstance = new Chart(chartCanvas.value, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Despesas Totais (R$)',
        data: values,
        backgroundColor: 'rgba(13, 110, 253, 0.7)', // Azul Primário Bootstrap com transparência
        borderColor: 'rgba(13, 110, 253, 1)',      // Borda Sólida
        borderWidth: 1,
        borderRadius: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } }, // Remove legenda pois só tem 1 série
      scales: { 
        y: { 
          beginAtZero: true, 
          grid: { borderDash: [2, 2] } // Linha pontilhada no eixo Y
        } 
      }
    }
  });
};

// Monitora alterações na prop 'data' para atualizar o gráfico automaticamente
watch(() => props.data, renderChart, { deep: true });

// Renderiza o gráfico assim que o componente é montado
onMounted(renderChart);
</script>