<template>
  <div class="row g-3 mb-4">
    <!-- Loop para renderizar cada cartão de KPI -->
    <div class="col-md-3" v-for="(kpi, idx) in kpis" :key="idx">
        <div class="card h-100 overflow-hidden glass-card" 
             :style="`--glass-bg: linear-gradient(135deg, ${kpi.color}44 0%, ${kpi.color}11 100%); border-left: 4px solid ${kpi.color};`">
            <div class="card-body position-relative z-1 d-flex flex-column justify-content-center">
                <small class="text-uppercase fw-bold opacity-75" style="font-size: 0.7rem;">{{ kpi.title }}</small>
                <div class="mt-2">
                    <!-- Valores numéricos sem quebra de linha -->
                    <h3 class="fw-bold mb-0 text-nowrap">{{ kpi.value }}</h3>
                    <small class="opacity-75" style="font-size: 0.75rem;">{{ kpi.subtitle }}</small>
                </div>
            </div>
            <!-- Barra de destaque inferior com brilho (Accento Visual) -->
            <div class="position-absolute bottom-0 start-0 w-100" :style="`height: 2px; background: ${kpi.color}; box-shadow: 0 0 10px ${kpi.color}`"></div>
        </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps(['macro']);

// Utilitário para formatação monetária compacta (ex: R$ 1,5 mi)
const formatMoney = (v) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', notation: 'compact' }).format(v);

// Computed Property que transforma os dados brutos (macro) em objetos de display para o template
const kpis = computed(() => {
    const m = props.macro;
    
    // Calcula se a tendência é positiva (para definir cor verde/vermelha)
    const isPos = m.tendencia_trimestral_percentual >= 0;
    
    return [
        { 
            title: 'Volume Geral de Mercado', 
            value: formatMoney(m.total_despesas), 
            subtitle: 'Movimentação Total', 
            color: '#3b82f6' 
        },
        { 
            title: 'Ticket Médio (Benchmark)', 
            value: formatMoney(m.media_por_operadora), 
            subtitle: 'Média por Operadora', 
            color: '#f59e0b' 
        },
        { 
            title: 'Empresas Ativas', 
            value: m.total_operadoras_ativas, 
            subtitle: 'Operadoras Analisadas', 
            color: '#8b5cf6' 
        },
        { 
            title: 'Tendência Geral', 
            value: (isPos ? '+' : '') + m.tendencia_trimestral_percentual.toFixed(1) + '%', 
            subtitle: 'Variação Trimestral (QoQ)', 
            color: isPos ? '#10b981' : '#ef4444' 
        }
    ];
});
</script>

<style scoped>
/* Ajustes de cor de texto para garantir contraste em fundos escuros/glass */
.text-secondary {
    color: #9ca3af !important;
}
.text-muted {
    color: #6b7280 !important;
}
</style>