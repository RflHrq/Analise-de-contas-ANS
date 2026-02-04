<template>
  <div class="card border-0 shadow-sm mb-5 glass-card">
    <div class="card-header bg-primary bg-opacity-10 border-0 pt-3 pb-2">
      <div class="d-flex justify-content-between align-items-center">
        <div class="text-start">
          <h5 class="fw-bold text-primary mb-1">🏆 Clube da Consistência</h5>
          <p class="mb-0 small text-white opacity-75">Operadoras que superaram a média de mercado em 2+ trimestres (Top 50).</p>
        </div>
        <span class="badge bg-primary rounded-pill">{{ totalCompanies }} Empresas</span>
      </div>
    </div>
    
    <div class="card-body bg-transparent">
      <!-- Layout em Masonry (Tijolinhos) -->
      <div class="masonry-wrapper">
        
        <div class="masonry-item" v-for="(companies, state) in groupedData" :key="state">
          <div class="card border-0 shadow-sm mb-3 glass-card">
            <div class="card-header fw-bold border-bottom-0 d-flex justify-content-between align-items-center">
              <span>📍 {{ state || 'Indefinido' }}</span>
              <span class="badge bg-secondary bg-opacity-10 text-white rounded-pill">{{ companies.length }}</span>
            </div>
            <div class="card-body p-0">
              <ul class="list-group list-group-flush">
                <li v-for="comp in companies" :key="comp.razao_social" class="list-group-item bg-transparent border-light py-2">
                  <div class="d-flex align-items-start gap-2">
                    <span class="text-warning mt-1" style="font-size: 0.8rem;">★</span>
                    <div class="text-start" style="line-height: 1.2;">
                      <span class="d-block small fw-bold">{{ comp.razao_social }}</span>
                      <small class="text-muted" style="font-size: 0.7rem;">
                        {{ comp.qtd_trimestres_acima }} trimestres acima
                      </small>
                    </div>
                  </div>
                </li>
              </ul>
            </div>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps(['list']);

// Calcula o total de empresas na lista
const totalCompanies = computed(() => props.list ? props.list.length : 0);

// Agrupa os dados por UF (Estado) para exibição em colunas
const groupedData = computed(() => {
  if (!props.list) return {};
  
  const groups = {};
  props.list.forEach(item => {
    const uf = item.uf || 'Outros';
    if (!groups[uf]) {
      groups[uf] = [];
    }
    groups[uf].push(item);
  });
  
  // Ordena os grupos alfabeticamente pela chave do estado
  return Object.keys(groups).sort().reduce(
    (obj, key) => { 
      obj[key] = groups[key]; 
      return obj;
    }, 
    {}
  );
});
</script>

<style scoped>
/* =========================================
   Layout Masonry (Estilo Pinterest)
   Permite colunas dinâmicas que se encaixam
   ========================================= */
.masonry-wrapper {
    column-count: 1; /* Mobile: 1 Coluna */
    column-gap: 1rem;
}

/* Tablet: 2 Colunas */
@media (min-width: 768px) {
    .masonry-wrapper {
        column-count: 2;
    }
}

/* Desktop: 3 Colunas */
@media (min-width: 1200px) {
    .masonry-wrapper {
        column-count: 3;
    }
}

/* Evita quebra do card entre colunas */
.masonry-item {
    break-inside: avoid; 
    margin-bottom: 0.5rem;
}
</style>