<template>
  <div class="card h-100 glass-card overflow-hidden">
    <div class="card-header pt-3 fw-bold">
        📊 Top Movers (Crescimento)
    </div>
    <div class="card-body p-0 text-start">
        <ul class="list-group list-group-flush">
            <li v-for="(item, index) in list" :key="index" class="list-group-item d-flex justify-content-between align-items-center py-3">
                <div class="d-flex align-items-center gap-3" style="flex: 1; min-width: 0;" :title="item.razao_social">
                    <span class="text-muted font-monospace small">0{{ index + 1 }}</span>
                    <div class="d-flex flex-column text-truncate">
                        <div class="fw-bold small text-white text-truncate">
                            {{ item.razao_social }}
                        </div>
                        <!-- Valor formatado sem quebra de linha -->
                        <small class="text-secondary text-nowrap" style="font-size: 0.7rem;">
                           {{ formatMoney(item.total_final) }}
                        </small>
                    </div>
                </div>
                <!-- Badge de Percentual de Crescimento -->
                <span class="badge bg-success bg-opacity-10 text-success border border-success border-opacity-25 rounded-pill">
                    +{{ item.crescimento_percentual }}%
                </span>
            </li>
        </ul>
    </div>
  </div>
</template>

<script setup>
// Recebe a lista de operadoras com maior crescimento
defineProps(['list']);

// Formata valores monetários de forma compacta (ex: 1 mi)
const formatMoney = (v) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', notation: 'compact' }).format(v);
</script>