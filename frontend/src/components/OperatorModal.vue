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
                            <th style="width: 20%">Classificação (4º Dígito)</th> <th style="width: 20%">Produto (5º Dígito)</th>  <th style="width: 25%">Descrição Detalhada</th>
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
                                    {{ decodeExpenseCode(d.conta_contabil).label4 }}
                                </span>
                            </td>
                            
                            <td class="fw-bold" style="font-size: 0.85rem;">
                                {{ decodeExpenseCode(d.conta_contabil).label5 }}
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
// LÓGICA DE INTERPRETAÇÃO DO PLANO DE CONTAS (ANS)
// Baseada na estrutura do código da conta contábil (Ex: 4.1.1.X.Y)
// =========================================================================

// 1. MAPEAMENTO DE CONTEXTO (3º Dígito)
const CONTEXTS = {
    '1': { label: 'Avisados', type: 'sinistro' },
    '4': { label: 'IBNR (Não Avisados)', type: 'ibnr' },
    '5': { label: 'Resseguro', type: 'seguro_resseguro' },
    '6': { label: 'Seguro', type: 'seguro_resseguro' }
};

// 2. MAPEAMENTOS ESPECÍFICOS POR CONTEXTO
const MAPS = {
    // Para 411 (Avisados), o 4º dígito é a Modalidade
    modality: {
        '1': 'Proc. (Fee-for-service)',
        '2': 'Capitation',
        '3': 'Orçamento Global',
        '4': 'Pacote',
        '5': 'Rateio',
        '6': 'Rede Indireta',
        '7': 'Reembolso',
        '8': 'SUS',
        '9': 'Outras Formas'
    },
    // Para 415/416, o 4º dígito é o Tipo de Custo
    subType: {
        '1': 'Prêmios',
        '2': 'Outras Despesas'
    },
    // O 5º dígito é quase sempre o Produto
    product: {
        '1': 'Médico-Hospitalar',
        '2': 'Odontológica'
    }
};

/**
 * Decodifica o código contábil seguindo a hierarquia ANS.
 * Retorna objetos prontos para o template.
 */
const decodeExpenseCode = (conta) => {
    if (!conta) return { label4: '-', label5: '-' };
    
    // Remove pontos para garantir acesso posicional correto (Ex: 4.1.1... -> 411...)
    const clean = conta.replace(/\D/g, '');
    if (clean.length < 5) return { label4: 'Inválido', label5: 'Inválido' };

    const digit3 = clean.charAt(2); // Contexto
    const digit4 = clean.charAt(3); // Modalidade/Subtipo
    const digit5 = clean.charAt(4); // Produto

    const context = CONTEXTS[digit3];
    
    let label4 = 'Não Classificado';
    let label5 = MAPS.product[digit5] || 'Outros Produtos';

    if (context) {
        if (context.type === 'sinistro') {
            // Se for Sinistro (411), 4º dígito é Modalidade
            label4 = MAPS.modality[digit4] || 'Outra Modalidade';
        } else if (['ibnr', 'seguro_resseguro'].includes(context.type)) {
            // Se for IBNR ou Seguro (414, 415, 416), 4º dígito é Subtipo
            label4 = MAPS.subType[digit4] || 'Outros Custos';
        }
    }

    return { label4, label5 };

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