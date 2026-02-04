<template>
  <div class="card border-0 shadow-sm h-100 glass-card">
    <div class="card-header fw-bold border-bottom-0 pt-3">
      🗺️ Top 10 UFs: Volume vs Ticket Médio
    </div>

    <div class="card-body pb-0"> <div class="row h-100">
        <!-- Gráfico de Volume Total (Esquerda) -->
        <div class="col-md-6 border-end">
            <h6 class="text-center text-primary small fw-bold mb-3">Ranking por Volume Total (R$)</h6>
            <div style="height: 250px; position: relative;">
                <canvas ref="volumeCanvas"></canvas>
            </div>
        </div>

        <!-- Gráfico de Ticket Médio (Direita) -->
        <div class="col-md-6">
            <h6 class="text-center text-danger small fw-bold mb-3">Ranking por Ticket Médio (R$)</h6>
            <div style="height: 250px; position: relative;">
                <canvas ref="mediaCanvas"></canvas>
            </div>
        </div>
      </div>
    </div>

    <div class="card-footer bg-transparent border-top-0 pt-0 pb-3 text-center">
        <small class="text-white opacity-75 fst-italic">
            * Ambos os rankings consideram os 10 estados com maior movimentação financeira.
        </small>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick, onUnmounted } from 'vue';
import Chart from 'chart.js/auto';

// Props recebidas do pai
const props = defineProps(['data']);

// Referências aos elementos Canvas do DOM
const volumeCanvas = ref(null);
const mediaCanvas = ref(null);

// Instâncias do Chart.js para controle
let volumeChart = null;
let mediaChart = null;

// Utilitários de Formatação
const formatCompact = (val) => new Intl.NumberFormat('pt-BR', { notation: "compact", compactDisplay: "short" }).format(val);
const formatMoney = (val) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);

/**
 * Helper seguro para obter variáveis CSS do tema atual (root).
 * @param {string} name - Nome da variável CSS (ex: --chart-text-color)
 */
const getCssVar = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

/**
 * Renderiza (ou re-renderiza) os gráficos.
 * Lida com a destruição de instâncias antigas e adaptação ao tema atual.
 */
const render = async () => {
    // Aguarda montagem do DOM
    await nextTick();
    if (!props.data || !volumeCanvas.value || !mediaCanvas.value) return;

    // Remove gráficos anteriores antes de criar novos
    if (volumeChart) volumeChart.destroy();
    if (mediaChart) mediaChart.destroy();

    // --- PREPARAÇÃO DOS DADOS ---
    const dataByVolume = [...props.data]; 
    const dataByMedia = [...props.data].sort((a, b) => b.media_por_operadora - a.media_por_operadora);

    // Recupera cores do tema atual (Deep CSS integration)
    const textColor = getCssVar('--chart-text-color') || '#64748b';
    const gridColor = getCssVar('--chart-grid-color') || 'rgba(0, 0, 0, 0.05)';

    // Configuração Comum (Theme Aware) para ambos os gráficos
    const commonOptions = {
        indexAxis: 'y', // Gráfico Horizontal
        responsive: true,
        maintainAspectRatio: false,
        color: textColor,
        borderColor: gridColor,
        plugins: {
            legend: { display: false },
            tooltip: {
                backgroundColor: 'rgba(30, 30, 30, 0.8)',
                titleColor: '#fff',
                bodyColor: 'rgba(255, 255, 255, 0.9)',
                borderColor: 'rgba(255, 255, 255, 0.2)',
                borderWidth: 1,
                callbacks: { label: (ctx) => formatMoney(ctx.raw) }
            }
        },
        scales: {
            x: {
                ticks: { 
                    callback: (val) => formatCompact(val), 
                    font: { size: 10 },
                    color: textColor
                },
                grid: { 
                    color: gridColor,
                    borderDash: [4, 4] 
                }
            },
            y: {
                grid: { display: false },
                ticks: { 
                    color: textColor,
                    font: { weight: '600' } 
                }
            }
        }
    };

    // --- RENDERIZAÇÃO ---

    // 1. Gráfico Esquerda (Azul - Volume Total)
    volumeChart = new Chart(volumeCanvas.value, {
        type: 'bar',
        data: {
            labels: dataByVolume.map(d => d.uf),
            datasets: [{
                label: 'Volume',
                data: dataByVolume.map(d => d.total_despesas),
                backgroundColor: getCssVar('--chart-bar-volume') || 'rgba(13, 110, 253, 0.7)',
                borderRadius: 4
            }]
        },
        options: commonOptions
    });

    // 2. Gráfico Direita (Vermelho - Ticket Médio)
    mediaChart = new Chart(mediaCanvas.value, {
        type: 'bar',
        data: {
            labels: dataByMedia.map(d => d.uf),
            datasets: [{
                label: 'Média',
                data: dataByMedia.map(d => d.media_por_operadora),
                backgroundColor: getCssVar('--chart-bar-media') || 'rgba(220, 53, 69, 0.7)',
                borderRadius: 4
            }]
        },
        options: commonOptions
    });
};

/* --- CICLO DE VIDA E REATIVIDADE --- */
let observer;

onMounted(() => {
    render();
    
    // Observer: Escuta a troca de classe/tema no elemento <html> (data-theme)
    // Se o usuário trocar Light <-> Dark, os gráficos redesenham com as novas cores.
    observer = new MutationObserver(() => {
        render();
    });
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
});

onUnmounted(() => {
    if (observer) observer.disconnect();
});

// Re-renderiza se os dados vindos do backend mudarem
watch(() => props.data, render, { deep: true });
</script>