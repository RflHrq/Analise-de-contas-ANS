<template>
    <Teleport to="body">
      <div v-if="loading" class="loading-overlay">
          <div class="spinner-border text-primary mb-2" style="width: 3rem; height: 3rem;" role="status"></div>
          <p class="text-muted fw-bold">Carregando dados financeiros...</p>
      </div>
    </Teleport>
  <div class="container py-5">
    
    <div class="d-flex justify-content-between align-items-end mb-5">
        <div class="text-start">
            <div class="d-flex align-items-center gap-2 mb-1">
                <span style="font-size: 1.5rem;">📊</span>
                <h2 class="fw-bold mb-0" style="letter-spacing: -1px;">Analise de contas da ANS</h2>
            </div>
            <p class="text-muted mb-0 small">Dashboard com dados de Despesas com Eventos/Sinistros</p>
        </div>
        
        <div class="d-flex align-items-center gap-3">
            <button class="btn btn-sm border rounded-pill px-3 d-flex align-items-center gap-2" 
                    @click="toggleTheme"
                    :class="isDarkMode ? 'btn-outline-light' : 'btn-outline-dark'">
                <span v-if="isDarkMode">☀️ Light Mode</span>
                <span v-else>🌙 Dark Mode</span>
            </button>

            <div v-if="loading" class="spinner-border text-primary spinner-border-sm"></div>
            <div v-if="!loading && !error" class="badge bg-primary bg-opacity-10 text-primary border border-primary border-opacity-25 px-3 py-2">
                🟢 Live Data
            </div>
        </div>
    </div>

    <div v-if="dashboardData">
        <KPIGrid :macro="dashboardData.macro" />

        <div class="row g-3 mb-4">
            <div class="col-md-8">
                <GeoEfficiencyChart :data="dashboardData.geo_eficiencia" />
            </div>
            <div class="col-md-4">
                <TopMovers :list="dashboardData.top_movers" />
            </div>
        </div>

        <ConsistencyClub :list="dashboardData.consistencia" />
    </div>

    <h4 class="fw-bold mb-3 mt-5">🔎 Caderno de Exploração</h4>
    <OperatorsTable 
        :list="operadoras" 
        :loading="tableLoading" 
        :page="page"
        :totalPages="totalPages"
        :totalRecords="totalRecords"
        @search="handleSearch"
        @changePage="changePage"
        @select="selectedOp = $event"
    />

    <OperatorModal 
        v-if="selectedOp" 
        :operator="selectedOp" 
        @close="selectedOp = null" 
    />

    <AIChatWidget />
    </div>

</template>

<script setup>
import { ref, onMounted } from 'vue';
import api from './services/api';
import { useTheme } from './composables/useTheme';

// Importação dos Componentes da Aplicação
import KPIGrid from './components/KPIGrid.vue';
import TopMovers from './components/TopMovers.vue';
import GeoEfficiencyChart from './components/GeoEfficiencyChart.vue';
import OperatorsTable from './components/OperatorsTable.vue';
import OperatorModal from './components/OperatorModal.vue';
import ConsistencyClub from './components/ConsistencyClub.vue';
import AIChatWidget from './components/AIChatWidget.vue';

// Gerenciamento de Tema (Dark/Light)
const { isDarkMode, toggleTheme } = useTheme();

// Estado da Aplicação
const loading = ref(true);
const tableLoading = ref(false);
const error = ref(false);
const dashboardData = ref(null);
const operadoras = ref([]);

// Paginação e Filtros da Tabela
const page = ref(1);
const totalPages = ref(1);
const totalRecords = ref(0);
const searchQuery = ref('');
const selectedOp = ref(null);

// Carregamento Inicial de Dados
onMounted(async () => {
    try {
        const dashRes = await api.getDashboardData();
        dashboardData.value = dashRes.data;
        await loadOperators();
    } catch (e) {
        console.error(e);
        error.value = true;
    } finally {
        loading.value = false;
    }
});

// Função para carregar lista de operadoras
const loadOperators = async () => {
    tableLoading.value = true;
    try {
        const res = await api.getOperators(page.value, 10, searchQuery.value);
        operadoras.value = res.data.data;
        page.value = res.data.page;
        totalRecords.value = res.data.total;
        totalPages.value = Math.ceil(res.data.total / 10);
    } finally {
        tableLoading.value = false;
    }
};

// Manipuladores de Eventos da Tabela
const handleSearch = (term) => { searchQuery.value = term; page.value = 1; loadOperators(); };
const changePage = (p) => { page.value = p; loadOperators(); };
</script>