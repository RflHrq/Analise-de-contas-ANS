<template>
  <div class="modal fade show" style="display: block; background: rgba(0,0,0,0.6);" tabindex="-1">
    <div class="modal-dialog modal-xl modal-dialog-centered modal-dialog-scrollable">
      <div class="modal-content border-0 shadow-lg glass-card" style="overflow: hidden; --glass-bg: var(--bg-card);">
        
        <!-- Cabeçalho do Modal -->
        <div class="modal-header bg-primary text-white">
          <div>
            <h5 class="modal-title fw-bold">{{ operator.razao_social }}</h5>
            <small class="opacity-75">Detalhamento Contábil (ANS)</small>
          </div>
          <button type="button" class="btn-close btn-close-white" @click="$emit('close')"></button>
        </div>
        
        <div class="modal-body p-4">
          <!-- Cartão de Resumo da Operadora -->
          <div class="card mb-3 border-0 shadow-sm glass-card">
            <div class="card-body">
              <div class="row text-center">
                <div class="col-md-3 border-end">
                    <small class="text-muted d-block text-uppercase">CNPJ</small> 
                    <strong class="font-monospace fs-5">{{ formatCNPJ(operator.cnpj) }}</strong>
                </div>
                <div class="col-md-3 border-end">
                    <small class="text-muted d-block text-uppercase">Registro ANS</small> 
                    <strong class="fs-5">{{ operator.registro_ans }}</strong>
                </div>
                <div class="col-md-3 border-end">
                    <small class="text-muted d-block text-uppercase">UF</small> 
                    <strong class="fs-5">{{ operator.uf || 'N/A' }}</strong>
                </div>
                <div class="col-md-3">
                    <small class="text-muted d-block text-uppercase">Total Consolidado</small> 
                    <strong class="text-success fs-4">{{ formatMoney(totalConsolidado) }}</strong>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Tabela de Detalhamento de Despesas -->
          <div class="card border-0 shadow-sm glass-card">
             <div class="card-header fw-bold d-flex justify-content-between">
                <span>Demonstrativo de Eventos Indenizáveis</span>
                <span class="badge bg-secondary">{{ expenses.length }} lançamentos</span>
             </div>
             <div class="card-body p-0">
                <!-- Loading State -->
                <div v-if="loading" class="text-center py-5">
                    <div class="spinner-border text-primary"></div>
                    <p class="mt-2 text-muted">Interpretando Plano de Contas...</p>
                </div>
                
                <!-- Tabela de Dados -->
                <table v-else class="table table-hover mb-0 table-sm align-middle text-white" style="font-size: 0.9rem;">
                    <thead class="border-bottom">
                        <tr>
                            <th style="width: 10%">Período</th>
                            <th style="width: 10%">Conta</th>
                            <th style="width: 20%">Produto (4º Dígito)</th> <th style="width: 20%">Evento (5º Dígito)</th>  <th style="width: 25%">Descrição Detalhada</th>
                            <th style="width: 15%" class="text-end">Valor</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="(d, i) in expenses" :key="i">
                            <td>
                                <span class="badge bg-secondary bg-opacity-25 text-white border border-secondary border-opacity-25">
                                    {{ d.ano }}/{{ d.trimestre }}
                                </span>
                            </td>
                            
                            <td class="font-monospace fw-bold text-info">{{ d.conta_contabil }}</td>
                            
                            <td>
                                <span class="badge bg-info bg-opacity-10 text-info border border-info border-opacity-25">
                                    {{ resolveProduct(d.conta_contabil) }}
                                </span>
                            </td>
                            
                            <td class="fw-bold" style="font-size: 0.85rem;">
                                {{ resolveEventType(d.conta_contabil) }}
                            </td>
                            
                            <td class="small opacity-75">{{ d.descricao || '-' }}</td>
                            
                            <td class="text-end fw-bold">{{ formatMoney(d.valor) }}</td>
                        </tr>
                         <tr v-if="expenses.length === 0">
                            <td colspan="6" class="text-center py-4 opacity-50">
                                Nenhum registro financeiro encontrado.
                            </td>
                        </tr>
                    </tbody>
                </table>
             </div>
          </div>
        </div>

        <div class="modal-footer border-top-0">
            <button class="btn btn-secondary" @click="$emit('close')">Fechar</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import api from '../services/api';

// Definição de Props e Emits
const props = defineProps(['operator']);
const emit = defineEmits(['close']);

// Estado Reativo
const expenses = ref([]);
const loading = ref(true);

// Utilitários de Formatação
const formatMoney = (val) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);

const formatCNPJ = (cnpj) => {
    if (!cnpj) return 'N/A';
    const clean = cnpj.replace(/\D/g, '');
    return clean.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, "$1.$2.$3/$4-$5");
};

// Calcula o total consolidado das despesas listadas
const totalConsolidado = computed(() => {
    return expenses.value.reduce((acc, item) => acc + (item.valor || 0), 0);
});

// =========================================================================
// 🧠 LÓGICA DE INTERPRETAÇÃO DO PLANO DE CONTAS (ANS)
// Baseada na estrutura do código da conta contábil (Ex: 4.1.1.X.Y)
// =========================================================================

// Mapeamento do 4º Dígito (Identificação do Produto)
const PRODUCT_MAP = {
    '1': 'Médico-Hospitalar',
    '2': 'Odontológica',
    '5': 'Corresp. Médico-Hospitalar',
    '6': 'Corresp. Odontológica'
};

// Mapeamento do 5º Dígito (Tipo de Evento)
// Distinto para Médico e Odontológico
const EVENT_MAP_MEDICAL = {
    '1': 'Consultas Médicas',
    '2': 'Exames',
    '3': 'Terapias',
    '4': 'Internações',
    '5': 'Outros Atend. Ambulatoriais',
    '6': 'Demais Despesas',
    '7': 'SUS',
    '8': 'Operações Exterior',
    '9': 'Sucursais Exterior'
};

const EVENT_MAP_DENTAL = {
    '1': 'Procedimentos Odontológicos',
    '6': 'Demais Despesas',
    '7': 'SUS',
    '8': 'Operações Exterior',
    '9': 'Sucursais Exterior'
};

/**
 * Resolve o nome do Produto baseado no 4º dígito da conta contábil.
 */
const resolveProduct = (conta) => {
    if (!conta || conta.length < 4) return 'Desconhecido';
    const digit4 = conta.charAt(3); // Índice 3 é o 4º caractere
    return PRODUCT_MAP[digit4] || 'Outros Produtos';
};

/**
 * Resolve o Tipo de Evento baseado no 5º dígito e no contexto (Médico vs Odonto).
 */
const resolveEventType = (conta) => {
    if (!conta || conta.length < 5) return '-';
    
    const digit4 = conta.charAt(3);
    const digit5 = conta.charAt(4); // Índice 4 é o 5º caractere

    // Contexto Médico (1 ou 5)
    if (digit4 === '1' || digit4 === '5') {
        return EVENT_MAP_MEDICAL[digit5] || 'Outros Eventos';
    }
    
    // Contexto Odontológico (2 ou 6)
    if (digit4 === '2' || digit4 === '6') {
        return EVENT_MAP_DENTAL[digit5] || 'Outros Eventos';
    }

    return 'Não Classificado';
};

// Busca os dados detalhados ao montar o componente
onMounted(async () => {
    try {
        const res = await api.getOperatorExpenses(props.operator.cnpj);
        expenses.value = res.data;
    } catch (e) {
        console.error("Erro ao carregar detalhes:", e);
    } finally {
        loading.value = false;
    }
});
</script>