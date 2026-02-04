<template>
  <div class="card shadow-sm glass-card">
    <div class="card-header py-3">
      <div class="row g-3 align-items-center">
        <div class="col-md-6 text-center text-md-start">
          <h5 class="mb-0 fw-bold">Caderno de Operadoras</h5>
        </div>
        <div class="col-md-6">
          <!-- Campo de Busca -->
          <div class="input-group">
            <span class="input-group-text bg-transparent border-end-0">🔍</span>
            <input 
              type="text" 
              class="form-control border-start-0 ps-0 bg-transparent" 
              placeholder="Buscar por Razão Social ou CNPJ..." 
              v-model="localSearch" 
              @keyup.enter="doSearch"
            >
            <button class="btn btn-primary" @click="doSearch" :disabled="loading">
               {{ loading ? '...' : 'Buscar' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Tabela com Scroll Vertical Fixo -->
    <div class="card-body p-0 position-relative overflow-auto" style="height: 550px;">
        <!-- Loading Overlay Local -->
        <div v-if="loading" class="position-absolute w-100 h-100 bg-dark bg-opacity-75 d-flex justify-content-center align-items-center" style="z-index: 10;">
            <div class="spinner-border text-primary"></div>
        </div>

        <table class="table table-hover align-middle mb-0 text-white">
            <thead class="table-dark bg-transparent">
                <tr>
                    <th style="width: 15%">Registro ANS</th>
                    <th style="width: 20%">CNPJ</th>
                    <th style="width: 50%">Razão Social</th>
                    <th class="text-center" style="width: 15%">Ações</th>
                </tr>
            </thead>
            <tbody>
                <tr v-for="op in list" :key="op.registro_ans" class="border-secondary">
                    <td><span class="badge bg-secondary">{{ op.registro_ans }}</span></td>
                    <td class="font-monospace small opacity-75">{{ op.cnpj }}</td>
                    <td class="fw-bold text-start">{{ op.razao_social }}</td>
                    <td class="text-center">
                        <button class="btn btn-sm btn-outline-primary" @click="$emit('select', op)">
                            Ver Histórico
                        </button>
                    </td>
                </tr>
                <tr v-if="!loading && list.length === 0">
                    <td colspan="4" class="text-center py-4 text-white opacity-50">
                        Nenhum registro encontrado para sua busca.
                    </td>
                </tr>
            </tbody>
        </table>
    </div>

    <!-- Paginação -->
    <div class="card-footer d-flex justify-content-between align-items-center py-3">
        <span class="text-muted small">
            Página <strong>{{ page }}</strong> de <strong>{{ totalPages }}</strong> (Total: {{ totalRecords }})
        </span>
        <nav>
            <ul class="pagination pagination-sm mb-0">
                <li class="page-item" :class="{ disabled: page === 1 }">
                    <button class="page-link" @click="$emit('changePage', page - 1)">Anterior</button>
                </li>
                <li class="page-item disabled"><span class="page-link">{{ page }}</span></li>
                <li class="page-item" :class="{ disabled: page >= totalPages }">
                    <button class="page-link" @click="$emit('changePage', page + 1)">Próximo</button>
                </li>
            </ul>
        </nav>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

// Definição de Propriedades da Tabela
const props = defineProps({
  list: Array,
  loading: Boolean,
  page: Number,
  totalPages: Number,
  totalRecords: Number
});

// Eventos emitidos para o componente pai (App.vue)
const emit = defineEmits(['search', 'changePage', 'select']);

// Estado local da busca
const localSearch = ref('');

// Dispara a busca
const doSearch = () => {
  emit('search', localSearch.value);
};
</script>

<style scoped>
/* Adaptação de cores dos inputs para funcionar bem no tema Glass/Dark */
.form-control, .input-group-text {
  color: inherit !important; 
}
.form-control::placeholder {
  color: inherit !important;
  opacity: 0.5;
}
</style>