![Badge Status](http://img.shields.io/static/v1?label=STATUS&message=EM%20DESENVOLVIMENTO&color=GREEN&style=for-the-badge)
![Badge HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)
![Badge CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)
![Badge JS](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
![Badge Python](https://img.shields.io/badge/Python-3.11.6-007acc?style=for-the-badge&logo=python&logoColor=white)
![Badge PostgreSQL](https://img.shields.io/badge/PostgreSQL-16.1-316bad?style=for-the-badge&logo=postgresql&logoColor=white)
![Badge FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-007acc?style=for-the-badge&logo=fastapi&logoColor=white)
![Badge Vue.js](https://img.shields.io/badge/Vue.js-3.4.15-41b883?style=for-the-badge&logo=vue.js&logoColor=white)
![Badge Chart.js](https://img.shields.io/badge/Chart.js-4.4.0-2c3e50?style=for-the-badge&logo=chart.js&logoColor=white)
![Badge AI](https://img.shields.io/badge/AI-Chat-007acc?style=for-the-badge&logo=ai&logoColor=white)

# SISTEMA DE ANÁLISE DE DESPESAS DA ANS

O sistema foi projetado para realizar a integração, processamento, análise e visualização de dados públicos da **Agência Nacional de Saúde Suplementar (ANS)**, com foco em despesas assistenciais de operadoras de planos de saúde.

A solução implementada abrange desde a coleta automatizada de dados através de *web scraping* até a construção de uma interface web interativa com recursos avançados de análise, incluindo inteligência artificial para consultas em linguagem natural. O projeto foi desenvolvido utilizando **Python** para o backend e processamento de dados, **PostgreSQL** para armazenamento, **FastAPI** para a camada de API REST, e **Vue.js** para o frontend.

![Dashboard Preview](docs/Dashboard.png)

---

## PARTE 1: INTEGRAÇÃO COM API DE DADOS ABERTOS DA ANS

### 1.1 ACESSO À API E IDENTIFICAÇÃO DE TRIMESTRES

O sistema implementa um módulo de *web scraping* robusto localizado no arquivo `scraper.py` que realiza o acesso automatizado ao portal de dados abertos da ANS. A implementação utiliza a biblioteca `HttpClient` com headers customizados que simulam um navegador real através do parâmetro `User-Agent`. Esta técnica foi necessária para evitar bloqueios automáticos do servidor da ANS que retornam erros HTTP 403 (Forbidden) ou 406 (Not Acceptable) quando detectam requisições automatizadas.

O processo de identificação dos três últimos trimestres disponíveis é realizado através do método `get_top_quarters_files` com o parâmetro `limit=3`, pois o cliente solicitou que fossem considerados apenas os três últimos trimestres disponíveis. O algoritmo executa um crawling hierárquico na estrutura de diretórios do portal: primeiro identifica todos os links de anos disponíveis (exemplo: `2024/`, `2025/`), ordena-os de forma decrescente para priorizar os dados mais recentes, e então navega dentro de cada pasta anual para localizar os arquivos ZIP correspondentes aos trimestres.

A resiliência a variações de nomenclatura foi implementada através de expressões regulares (Regex) sofisticadas no método `_detect_quarter`. O sistema utiliza padrões como `r'(\d)t(\d{4})'` que conseguem identificar trimestres independentemente do formato do nome do arquivo. Isso permite que o sistema funcione corretamente tanto com nomes como `1T2024.zip` quanto `2024_01_demonstracoes.zip` ou outras variações encontradas nos dados históricos da ANS.

### 1.2 PROCESSAMENTO E EXTRAÇÃO DE ARQUIVOS

O fluxo de download e extração foi projetado para ser completamente automatizado e eficiente em termos de uso de recursos computacionais. O método `download_file` implementado no `scraper.py` utiliza streaming de dados para evitar carregar arquivos ZIP inteiros na memória RAM de uma só vez. Após o download via stream, o sistema invoca imediatamente o `FileHandler.extract_zip` para realizar a descompactação, mantendo o processo fluido e com baixo consumo de memória.

A identificação de conteúdo relevante (despesas) é realizada no módulo `consolidator.py` através de um filtro rigoroso baseado nas contas contábeis. O sistema aplica a lógica `chunk["Conta"].str.startswith("4")` que seleciona apenas registros cujo código de conta começa com o dígito "4". Este prefixo, conforme o padrão contábil da ANS, identifica exclusivamente **Despesas Assistenciais**, descartando automaticamente registros de passivos, ativos e receitas que não são relevantes para a análise proposta.

O desafio técnico de normalização de formatos heterogêneos foi resolvido através de uma abordagem multi-camadas implementada no `consolidator.py`. O sistema primeiro executa a detecção de encoding através do método `_detect_encoding`, que testa automaticamente `UTF-8` e `CP1252` (Windows Latin-1), os dois formatos mais comuns em arquivos governamentais brasileiros. Em seguida, o método `_identify_separator` utiliza a biblioteca `csv.Sniffer` para descobrir automaticamente se o arquivo utiliza vírgula, ponto-e-vírgula ou tabulação como separador de campos. Por fim, a padronização numérica remove pontos de milhares e converte vírgulas decimais para o formato ponto antes da conversão para `float`, garantindo que o banco de dados receba sempre valores numéricos válidos.

### 1.3 TRADE-OFF TÉCNICO: PROCESSAMENTO INCREMENTAL

Uma das decisões técnicas mais importantes do projeto foi a escolha entre **processamento em memória** versus **processamento incremental**. A decisão foi pelo processamento incremental através de *chunks* (blocos de dados), uma estratégia também conhecida como *streaming processing*.

A justificativa para esta escolha é fundamentada no volume de dados: os arquivos da ANS frequentemente contêm milhões de linhas, especialmente quando incluem dados detalhados de lançamentos contábeis. Carregar um arquivo CSV de 2GB inteiro na memória usando `pd.read_csv` no modo padrão poderia causar erro **OOM (Out of Memory)**, travando a máquina ou o processo.

A implementação utiliza o parâmetro `chunksize=CHUNK_SIZE` do Pandas, configurado para 50.000 linhas por bloco. O código itera sobre os chunks sequencialmente, processando cada um independentemente e salvando em modo `append` no arquivo CSV final. Este approach garante que o script consuma uma quantidade constante e baixa de memória RAM, independentemente do tamanho total do arquivo de entrada, permitindo que o sistema processe datasets de qualquer tamanho em hardware modesto.

### 1.4 CONSOLIDAÇÃO E ANÁLISE DE INCONSISTÊNCIAS

A consolidação dos dados de múltiplos trimestres em um único arquivo CSV é realizada através do padrão Append implementado no `etl/consolidator.py`. O script itera sobre todos os arquivos CSV e TXT extraídos dos ZIPs baixados e vai adicionando bloco a bloco no arquivo final `consolidado_despesas.csv` usando o modo `mode='a'` do Pandas.

A estrutura de colunas do arquivo final foi padronizada conforme especificado: `CNPJ`, `RazaoSocial`, `Trimestre`, `Ano` e `ValorDespesas`. Esta padronização é controlada através da variável `FINAL_COLUMNS` definida em `config.py`. Durante o processamento, o sistema renomeia as colunas originais dos arquivos da ANS (que podem ter nomes como `VL_SALDO_FINAL`) para os nomes padronizados, descartando todas as demais colunas irrelevantes. As colunas Trimestre e Ano são injetadas automaticamente pelo sistema baseando-se no nome do arquivo ZIP de origem, garantindo rastreabilidade temporal dos dados.

O tratamento de inconsistências foi implementado seguindo três categorias principais de problemas identificados durante a análise exploratória dos dados:

#### Inconsistência A: CNPJs Duplicados com Razões Sociais Diferentes

O sistema assume que a Receita Federal e o Cadastro de Operadoras (CADOP) da ANS são as fontes autoritativas da verdade. A implementação no módulo `etl/enrichment.py` ignora completamente a Razão Social que vem nos arquivos CSV financeiros, pois estes são campos de texto livre propensos a erros de digitação e variações ortográficas. O sistema, deixa em branco esses campos (CNPJ e Razão Social) e realiza um JOIN com o arquivo oficial CADOP (exigido nas proximas etapas propostas pelo cliente), sobrescrevendo todas as razões sociais pela versão oficial e padronizada. Como resultado, todos os registros de um mesmo CNPJ ficam com a Razão Social idêntica, eliminando variações como "UNIMED BH", "Unimed Belo Horizonte", "UNIMED BELO HORIZONTE COOP", etc.

#### Inconsistência B: Valores Zerados ou Negativos

Valores zerados são eliminados fisicamente do dataset através do filtro `df_final = df_final[df_final["Valor Despesas"] != 0]` implementado na linha 114 do `etl/consolidator.py`. Esta decisão reduz drasticamente o tamanho do arquivo final sem perda de informação analítica, já que a ausência de despesa é semanticamente equivalente a não ter a linha no arquivo.

Valores negativos, por outro lado, são mantidos integralmente. Esta decisão foi tomada porque na contabilidade de operadoras de saúde, valores negativos representam estornos de provisões, recuperações de despesas ou ajustes de exercícios anteriores. Remover esses lançamentos distorceria o saldo contábil final real da operadora, violando princípios de integridade contábil. A conversão de formato numérico é robusta, transformando strings no padrão brasileiro "1.234,56" para o formato `float` padrão `1234.56`.

#### Inconsistência C: Trimestres com Formatos de Data Inconsistentes

O sistema adota uma abordagem pragmática ignorando completamente as colunas de data presentes dentro dos arquivos CSV. Estas colunas frequentemente vêm vazias, malformadas ou em formatos inconsistentes como `dd/mm/yy` versus `yyyy-mm-dd`. Em vez disso, o sistema confia na estrutura de diretórios e nos nomes de arquivos como metadados externos. O `scraper.py` analisa padrões de URL para extrair os metadados corretos de Ano e Trimestre antes mesmo de baixar o arquivo. O `consolidator.py` então injeta essas colunas explicitamente durante o processamento, através do método `_extract_date_info`.

A compactação final do arquivo consolidado é realizada automaticamente ao término do processamento. O sistema utiliza a classe `FileCompressor` para criar o arquivo `consolidado_despesas.zip` no diretório `data/processed/`, conforme especificado nos requisitos do teste.

---

## PARTE 2: TRANSFORMAÇÃO E VALIDAÇÃO DE DADOS

### 2.1 VALIDAÇÃO DE CNPJ E ESTRATÉGIAS DE TRATAMENTO

A validação de CNPJ foi implementada seguindo o algoritmo oficial de **Módulo 11** da Receita Federal. O código está localizado em `utils/validators.py` na classe `CNPJValidator.validate`. O processo de validação segue três etapas: primeiro remove todos os caracteres não numéricos usando expressão regular `re.sub(r'\D', '')`, depois verifica se o resultado tem exatamente 14 dígitos e se não é uma sequência repetida inválida como "11111111111111", e finalmente calcula e compara os dois dígitos verificadores usando o algoritmo de Módulo 11.

A aplicação prática desta validação ocorre no módulo `etl/enrichment.py`, onde o sistema cria uma coluna booleana `CNPJ_Valido` para cada registro do dataset. Esta abordagem foi escolhida cuidadosamente através de uma análise de *trade-offs* técnicos.

#### Trade-off: Soft Validation versus Hard Validation

A decisão foi pela **Soft Validation**, também conhecida como *Flagging*. Ao invés de descartar (DROP) registros com CNPJ inválido, o sistema os mantém no banco de dados mas marca-os com a flag `CNPJ_Valido = False`. Esta escolha foi fundamentada em dois pilares:

1.  **Integridade contábil**: se registros com CNPJ inválido fossem simplesmente descartados, o saldo contábil total do trimestre não bateria com os valores oficiais publicados pela ANS. Para um sistema financeiro de auditoria, é preferível ter um dado com "metadado sujo" do que ter um "dado faltante" que distorce totais e médias.
2.  **Rastreabilidade e auditoria**: mantendo os registros marcados, analistas podem posteriormente executar queries específicas como `SELECT * FROM despesas WHERE CNPJ_Valido = FALSE` para investigar a origem do erro e potencialmente corrigi-lo através de cruzamento com outras bases de dados, em vez de simplesmente ocultar o problema.

### 2.2 VALIDAÇÃO DE VALORES NUMÉRICOS

A validação de valores numéricos é realizada durante a fase de consolidação no módulo `etl/consolidator.py`. O sistema implementa um pipeline de transformação que primeiro realiza conversão segura de string para float, tratando apropriadamente os formatos brasileiros de números (vírgula como separador decimal e ponto como separador de milhares).

Valores zerados (`0.00`) são removidos fisicamente do dataset através do filtro já mencionado. Esta decisão de design otimiza o armazenamento e performance de queries analíticas posteriores.

Quanto aos valores negativos, um *trade-off* importante foi considerado. A especificação do teste solicita "valores numéricos positivos", o que poderia sugerir que negativos deveriam ser filtrados ou convertidos para positivos através de `abs()`. No entanto, a decisão foi manter os valores negativos intactos. Na contabilidade regulatória da ANS, valores negativos em contas de despesa representam lançamentos contábeis legítimos como estornos de provisões técnicas, recuperações de despesas de exercícios anteriores, ou ajustes de reclassificação. Forçar todos os valores a serem positivos (seja descartando negativos ou aplicando valor absoluto) fraudaria o balancete contábil e violaria princípios de fidelidade aos dados fonte. Portanto, o critério "positivo" foi interpretado no contexto contábil apropriado, mantendo a integridade dos dados financeiros.

### 2.3 VALIDAÇÃO DE RAZÃO SOCIAL

A validação de Razão Social implementa uma estratégia de **Enriquecimento com Fallback em múltiplos níveis**, localizada no módulo `etl/enrichment.py`. O sistema segue uma hierarquia de fontes de dados: primeiro tenta buscar a Razão Social oficial do Cadastro de Operadoras (CADOP) através do JOIN pela chave `RegistroANS`; se não encontrar correspondência no cadastro (operadora inativa ou liquidada), utiliza a Razão Social que vem no arquivo financeiro original; se esta também estiver nula ou vazia, preenche com o valor padrão "OPERADORA INATIVA/DESCONHECIDA".

Esta abordagem garante que nenhuma linha no banco de dados final tenha `razao_social = NULL` ou string vazia, o que facilitaria problemas em queries SQL, indexação de texto e visualizações no dashboard frontend.

### 2.4 ENRIQUECIMENTO DE DADOS COM CADOP

O processo de enriquecimento cruza os dados financeiros consolidados com o cadastro oficial de operadoras ativas da ANS. A implementação está no módulo `etl/enrichment.py` e começa com o download automatizado do arquivo `Relatorio_cadop.csv` diretamente do portal de dados abertos da ANS através do método `download_cadastro()`. Para contornar problemas comuns de certificados SSL expirados em portais governamentais, o sistema utiliza `verify=False` na requisição HTTP.

#### Decisão Técnica: RegistroANS como Chave Primária

Uma decisão técnica importante foi utilizar `RegistroANS` como chave de JOIN ao invés de CNPJ, apesar da especificação do teste mencionar CNPJ. Esta decisão foi fundamentada em três argumentos técnicos:

1.  **Integridade referencial**: o RegistroANS é a chave primária (PK) imutável no ecossistema da ANS. Cada operadora recebe um número de registro único que não muda durante toda sua existência, mesmo se houver mudança de razão social, endereço ou até mesmo CNPJ (em casos de mudanças societárias ou aberturas de filiais).
2.  **Robustez de matching**: o CNPJ nos arquivos CSV frequentemente vem em formatos variados - com pontos, barras e hífens em alguns arquivos, e sem formatação em outros (apenas 14 dígitos). Fazer JOIN por string de CNPJ é propenso a falhas silenciosas onde registros que deveriam fazer match não fazem devido a diferenças de formatação. O RegistroANS, sendo um identificador numérico curto, elimina este problema.
3.  **Performance**: identificadores numéricos são mais eficientes para indexação e operações de JOIN em bancos de dados relacionais do que strings longas. O código implementa `pd.merge(df_despesas, df_ops, on='RegistroANS', how='left')`.

O resultado do JOIN adiciona três colunas ao dataset: `RegistroANS` (que já existia mas é limpo e padronizado), `Modalidade` (tipo de operadora: cooperativa médica, medicina de grupo, seguradora, etc.) e `UF` (estado de registro da operadora).

#### Tratamento de Registros Sem Match

O sistema utiliza **LEFT JOIN**, uma escolha deliberada para preservar a completude dos dados financeiros. Operadoras que enviaram balancete contábil mas não estão no arquivo de operadoras ativas geralmente foram liquidadas, tiveram registro cancelado ou foram fundidas/incorporadas recentemente. O LEFT JOIN mantém esses registros financeiros no dataset final, mas preenche as lacunas com valores padrão que não quebram o sistema de Business Intelligence: Razão Social recebe "OPERADORA INATIVA/DESCONHECIDA", UF recebe "ND" (Não Definido), e Modalidade recebe "Desconhecida".

#### Tratamento de Duplicatas no Cadastro

O arquivo CADOP ocasionalmente contém linhas duplicadas ou sujas. Antes de realizar o JOIN, o sistema executa `drop_duplicates(subset=['RegistroANS'])` no DataFrame de operadoras, mantendo apenas a primeira ocorrência de cada RegistroANS. Isso garante a unicidade da dimensão e evita explosão cartesiana durante o JOIN, que causaria duplicação artificial de linhas de despesa.

#### Trade-off: Processamento em Memória versus Banco de Dados

Para o processo de JOIN e enriquecimento, a estratégia escolhida foi **Processamento em Memória usando Pandas**, ao invés de carregar os dados em um banco de dados temporário. Esta decisão foi baseada em três fatores:

1.  **Volume de dados (Small/Medium Data)**: O arquivo de cadastro (tabela dimensão) é minúsculo, contendo aproximadamente 1.000 operadoras ativas. O arquivo de despesas (tabela fato) para 3 trimestres, embora grande em número absoluto de linhas, ainda cabe confortavelmente na memória RAM de servidores modernos ou mesmo laptops de desenvolvimento (alguns gigabytes).
2.  **Performance de desenvolvimento**: Implementar o JOIN no Pandas é ordens de magnitude mais rápido de desenvolver e testar do que subir uma instância temporária de PostgreSQL ou MySQL, carregar os dados via COPY, executar o JOIN via SQL, e exportar o resultado.
3.  **Eficiência computacional (Broadcast Join)**: Como a tabela da direita (Operadoras) é pequena, o Pandas executa o merge de forma extremamente eficiente, similar a um *Broadcast Hash Join* em sistemas de processamento distribuído como Spark. A tabela pequena é mantida em memória como uma hash table, e cada linha da tabela grande é processada uma única vez.

A alternativa descartada de usar banco de dados seria mais robusta para volumes massivos (escala de terabytes), mas adicionaria overhead desnecessário de I/O disco para esta escala de problema.

### 2.5 AGREGAÇÃO COM MÚLTIPLAS ESTRATÉGIAS

A agregação de dados implementa uma estratégia sofisticada de **Two-Pass Aggregation** (Dupla Agregação) no módulo `etl/aggregator.py`. Esta abordagem foi necessária para calcular corretamente as estatísticas solicitadas.

#### Passo 1: Pré-agregação Trimestral

Antes de calcular médias e desvios padrão, o sistema precisa garantir que existe um valor único por operadora por trimestre. Isso porque os dados brutos contêm múltiplos lançamentos contábeis (linhas) para cada operadora em cada trimestre. O código executa:

```python
df_trimestral = df.groupby(['RegistroANS', 'RazaoSocial', 'UF', 'Modalidade', 'Ano', 'Trimestre'])['Valor Despesas'].sum().reset_index()
```

Este agrupamento cria uma visão sumarizada onde cada linha representa o total de despesas de uma operadora específica em um trimestre específico.

#### Passo 2: Estatísticas Finais

Com os dados pré-agregados, o sistema então calcula todas as métricas solicitadas em uma única passada usando a função `agg` do Pandas:

```python
stats = df_trimestral.groupby(['RegistroANS', 'RazaoSocial', 'UF', 'Modalidade'])['Despesa_Trimestral'].agg(
    Total_Despesas='sum',
    Media_Trimestral='mean',
    Desvio_Padrao='std'
)
```

O `Total_Despesas` representa a soma de todos os trimestres para cada operadora. A `Media_Trimestral` calcula a média de despesas por trimestre, permitindo identificar o "ritmo" médio de gastos da operadora. O `Desvio_Padrao` mede a volatilidade dos gastos, identificando operadoras com comportamento errático versus operadoras com despesas estáveis.

Uma normalização importante é aplicada ao desvio padrão: operadoras que têm dados em apenas um trimestre retornam `NaN` para esta métrica (pois não há variação calculável). O código trata isso preenchendo com `0.0`, indicando variação nula por falta de dados históricos suficientes.

#### Ordenação do Ranking

A ordenação dos resultados é feita através de `stats.sort_values(by='Total_Despesas', ascending=False)`, criando um ranking das operadoras de maior para menor gasto total.

#### Trade-off: Estratégia de Ordenação

A decisão foi utilizar **In-Memory Sort** usando o algoritmo Quicksort nativo do Pandas. A justificativa é que a agregação reduz drasticamente o volume de dados: de milhões de linhas (lançamentos contábeis individuais) para aproximadamente 1.000 linhas (uma por operadora). Ordenar 1.000 ou até 100.000 linhas em memória é instantâneo (menos de 10 milissegundos) em qualquer CPU moderna. Implementar ordenação externa (Merge Sort em disco) ou delegar para um banco de dados seria *over-engineering* que aumentaria a complexidade de manutenção sem ganho prático de performance nesta escala.

#### Persistência e Entrega

O resultado final é salvo em `despesas_agregadas.csv` conforme definido em `config.py`. O código usa `encoding='utf-8-sig'` para garantir que acentuações em nomes de empresas sejam renderizados corretamente ao abrir no Microsoft Excel. O arquivo é então automaticamente compactado em `Teste_Rafael_Henrique_dos_Santos_Simao.zip` através da classe `FileCompressor`, gerando o arquivo final de entrega na pasta `data/processed/`.

---

## PARTE 3: BANCO DE DADOS E ANÁLISE

### 3.1 MODELAGEM E DECISÕES DE SCHEMA

O banco de dados foi implementado em **PostgreSQL** seguindo uma arquitetura híbrida de **Star Schema** (Schema Estrela), balanceando performance de escrita e leitura. A modelagem consiste em uma tabela dimensão `operadoras` contendo dados cadastrais únicos e imutáveis de cada operadora, e uma tabela fato `despesas_eventos` contendo os lançamentos contábeis detalhados com chave estrangeira `registro_ans` apontando para a dimensão.

#### Trade-off: Normalização versus Desnormalização

A decisão de usar Star Schema ao invés de uma tabela única desnormalizada foi fundamentada em três aspectos:

1.  **Armazenamento eficiente**: Em uma tabela desnormalizada, campos como endereço, razão social completa e modalidade seriam repetidos milhões de vezes (uma cópia para cada lançamento contábil). Com a normalização, esses dados são armazenados uma única vez na tabela dimensão, com apenas um inteiro (RegistroANS) sendo repetido na tabela fato.
2.  **Integridade referencial**: A normalização garante que mudanças cadastrais (como correção de endereço) sejam propagadas automaticamente para todas as análises, através do mecanismo de chave estrangeira.
3.  **Performance analítica**: Queries típicas de BI como "total de despesas por UF" executam JOINs muito eficientes entre fato e dimensão graças aos índices apropriados, sem perder a capacidade de drill-down até o detalhe transacional.

#### Trade-off: Tipos de Dados Monetários

Para valores monetários, a escolha foi `NUMERIC(18,2)` ao invés de `FLOAT` ou `INTEGER` (centavos). Esta decisão é crítica para sistemas financeiros: tipos de ponto flutuante como `FLOAT` possuem problemas de precisão binária inerentes (exemplo clássico: `0.1 + 0.2 != 0.3` em aritmética de ponto flutuante). Para garantir que cada centavo seja contabilizado exatamente, `NUMERIC`/`DECIMAL` é obrigatório. A precisão de 18 dígitos inteiros e 2 decimais suporta valores de até 999 trilhões de reais com precisão de centavos, mais que suficiente para qualquer operadora individual.

A alternativa de armazenar valores como `INTEGER` representando centavos (ex: R$ 100,00 = 10000) seria tecnicamente viável e até mais performática, mas adiciona complexidade de conversão em todas as queries e aumenta risco de bugs em cálculos de divisão.

#### Trade-off: Representação Temporal

Para datas, a decisão foi usar `ano` (INTEGER) e `trimestre` (INTEGER) como colunas separadas ao invés de um campo `DATE`. A justificativa é semântica: a ANS publica dados com granularidade trimestral, não diária. Armazenar uma data fake como `2024-01-01` para representar "1º Trimestre de 2024" seria semanticamente incorreto e causaria confusão em análises. Índices compostos do tipo `CREATE INDEX idx_eventos_tempo ON despesas_eventos(ano, trimestre)` oferecem performance excelente para queries de série temporal.

### 3.2 IMPORTAÇÃO DE DADOS E TRATAMENTO DE INCONSISTÊNCIAS

A estratégia de carga de dados utiliza Pandas + SQLAlchemy ao invés de comandos SQL brutos como `COPY`. Esta abordagem foi escolhida por três motivos: tratamento automático de encoding (UTF-8-sig), capacidade de aplicar transformações complexas antes da inserção, e portabilidade entre diferentes bancos de dados (PostgreSQL, MySQL, SQLite) sem alterar código.

O módulo `etl/database_loader.py` implementa o pipeline de carga. Antes da inserção no banco, o código trata três categorias de inconsistências:

1.  **Valores NULL em campos obrigatórios** são ou preenchidos com defaults semânticos (exemplo: `UF=ND`, `Modalidade=Desconhecida`) ou causam rejeição da linha com log de erro para auditoria posterior.
2.  **Strings em campos numéricos** são limpadas através de expressões regulares que removem caracteres não numéricos e convertem separadores decimais (`.replace(',', '.')`), seguido de conversão segura com tratamento de exceção.
3.  **Datas em formatos inconsistentes** são evitadas através da estratégia de usar Ano e Trimestre inteiros, eliminando completamente o problema de parsing de formatos de data ambíguos.

### 3.3 QUERIES ANALÍTICAS IMPLEMENTADAS

As queries solicitadas foram implementadas em SQL puro no arquivo `database/queries.sql` e são executadas dinamicamente pela API REST através do módulo `api/main.py`.

#### Query 1: Top 5 Crescimento Percentual

Esta query identifica as operadoras com maior crescimento de despesas entre o primeiro e último trimestre analisado. O desafio técnico mencionado na especificação era tratar operadoras com dados faltantes. A solução implementada utiliza INNER JOIN entre duas CTEs: `despesas_inicio` (primeiro trimestre) e `despesas_fim` (último trimestre). O efeito prático é que apenas operadoras que existiam e operavam em ambos os períodos são consideradas no ranking. Isso evita calcular crescimentos infinitos (divisão por zero quando o trimestre inicial não existe) ou crescimentos irreais de operadoras entrantes que aparecem apenas no último trimestre. A query então calcula `((valor_fim - valor_inicio) / valor_inicio) * 100` para obter o crescimento percentual.

#### Query 2: Distribuição por UF com Média Correta

Esta query lista os 5 estados com maiores despesas totais e adicionalmente calcula a média de despesas por operadora em cada UF. Um detalhe técnico importante é a definição de "média": não é a média simples de todas as linhas contábeis (que seria dominada por operadoras com muitos lançamentos), mas sim o "ticket médio" que representa total do estado dividido pelo número de operadoras distintas. A implementação usa `SUM(valor_despesas) / COUNT(DISTINCT registro_ans)` para obter esta métrica de forma eficiente em uma única passada sobre os dados.

#### Query 3: Consistência Acima da Média

Esta query identifica operadoras que se mantiveram acima da média de mercado em pelo menos 2 dos 3 trimestres analisados. A implementação utiliza CTEs (Common Table Expressions) para legibilidade e manutenibilidade. O fluxo da query é: primeiro calcula totais por operadora por trimestre em uma CTE `metricas`, depois calcula a média de mercado de cada trimestre em outra CTE `medias_mercado`, então cruza via JOIN e cria uma flag binária (1 ou 0) indicando se a operadora ficou acima da média naquele trimestre, e finalmente agrupa por operadora e filtra com `HAVING SUM(flag) >= 2`. Esta abordagem com CTEs é mais legível e performática que subqueries aninhadas, pois o otimizador do PostgreSQL pode materializar as CTEs e reutilizá-las eficientemente.

#### Trade-off: CTEs versus Subqueries

A escolha de CTEs ao invés de subqueries aninhadas foi baseada em três fatores: legibilidade (cada CTE tem um nome semântico que documenta sua função), manutenibilidade (é fácil testar cada CTE isoladamente durante desenvolvimento), e performance (PostgreSQL 12+ otimiza CTEs de forma inteligente, materializando quando necessário).

---

## PARTE 4: API REST E INTERFACE WEB

### 4.1 ARQUITETURA BACKEND

#### Framework: FastAPI

A decisão de utilizar **FastAPI** ao invés de Flask foi fundamentada em quatro pilares técnicos:

1.  **Performance assíncrona**: FastAPI é construído sobre Starlette e o padrão ASGI (*Asynchronous Server Gateway Interface*), permitindo lidar com centenas de requisições HTTP simultâneas sem bloquear a thread principal. Isso é crítico quando múltiplos usuários acessam o dashboard simultaneamente, cada um carregando vários gráficos que fazem requisições paralelas à API.
2.  **Type safety e validação automática**: O uso massivo de Pydantic através dos schemas definidos em `api/schemas.py` reduz drasticamente bugs de tipo. Cada endpoint tem seus parâmetros de entrada e saída validados automaticamente, convertidos para os tipos corretos, e rejeitando requisições mal-formadas com mensagens de erro descritivas antes mesmo de executar a lógica de negócio.
3.  **Documentação automática**: FastAPI gera nativamente uma interface Swagger UI acessível em `/docs` e uma interface ReDoc em `/redoc`. Esta documentação é atualizada automaticamente quando o código muda, servindo como documentação viva para a equipe de frontend e economizando horas de escrita manual de especificações.
4.  **Performance**: Benchmarks independentes mostram FastAPI sendo 2-3x mais rápido que Flask em workloads típicos de API REST, especialmente quando há I/O de banco de dados envolvido.

#### Estratégia de Paginação: Offset-based

A implementação de paginação utiliza o padrão Offset-based através de parâmetros de query `?page=1&limit=10`. Embora Cursor-based pagination seja mais performática para "infinite scroll" em datasets massivos (bilhões de linhas), Offset-based é ideal para interfaces de tabelas/grids administrativas onde o usuário quer navegar diretamente para uma página específica (exemplo: "ir para página 5").

A justificativa técnica é escala: com aproximadamente 1.000 operadoras ativas, o custo de performance do `OFFSET` no PostgreSQL é desprezível (menos de 1ms adicional), e a facilidade de implementação no frontend Vue.js é superior. O PostgreSQL otimiza queries com OFFSET pequenos usando o índice da chave primária.

#### Estratégia de Cache: Queries em Tempo Real

Para o endpoint de estatísticas `/api/analytics/storytelling`, a decisão foi por cálculo em tempo real usando queries SQL otimizadas ao invés de pré-computação ou cache. A justificativa é frequência de atualização: os dados são carregados trimestralmente (baixa frequência de escrita), então o banco PostgreSQL consegue responder agregações complexas em milissegundos devido à indexação correta.

A vantagem desta abordagem é garantir que o dashboard sempre mostre o estado atual exato dos dados, sem problemas de cache invalidado (*stale data*). A tabela pré-agregada `despesas_agregadas` existe no banco e pode ser usada para relatórios estáticos exportáveis, mas para interatividade do dashboard, a query dinâmica provou-se suficientemente performática.

#### Estrutura de Resposta da API: Dados + Metadados

Todas as respostas paginadas seguem o padrão de envelope com metadados:

```json
{
  "total": 1032,
  "page": 1,
  "limit": 10,
  "data": [...]
}
```

Esta decisão foi tomada porque para construir uma paginação robusta no frontend (mostrando "Página 1 de 50" e desabilitando o botão "Próximo" na última página), o cliente precisa saber o total de registros disponíveis. Retornar apenas o array de dados forçaria o frontend a "adivinhar" se existe uma próxima página através de heurísticas (exemplo: se recebeu menos itens que o limit, provavelmente acabou), degradando a experiência do usuário.

### 4.2 ROTAS IMPLEMENTADAS

Além das rotas básicas solicitadas, a API foi expandida para suportar um dashboard profissional:

*   `GET /api/operadoras`: Listagem paginada com suporte a busca textual através do parâmetro `search`. Implementa busca *fuzzy* usando `ILIKE` do PostgreSQL que procura o termo tanto no CNPJ quanto na Razão Social.
*   `GET /api/operadoras/{cnpj}`: Retorna os dados cadastrais completos de uma operadora específica (Razão Social, Modalidade, UF, etc).
*   `GET /api/operadoras/{cnpj}/despesas`: Drill-down detalhado mostrando todos os lançamentos contábeis históricos de uma operadora específica, permitindo análise granular.
*   `GET /api/estatisticas`: Retorna estatísticas agregadas globais do sistema, incluindo total de despesas, média por operadora, top 5 maiores despesas e distribuição por UF.
*   `GET /api/analytics/storytelling`: Endpoint agregador turbinado que retorna todas as métricas necessárias para o dashboard em uma única requisição HTTP: KPIs macro (volume total de mercado, ticket médio, número de operadoras ativas), Top Movers (operadoras com maior crescimento percentual), distribuição geográfica por estado, e clube de consistência (operadoras que se mantiveram acima da média). Esta abordagem de "fat endpoint" reduz o número de round-trips HTTP, melhorando a performance percebida do dashboard.
*   `POST /api/ai/ask`: Endpoint experimental de chatbot que aceita perguntas em linguagem natural e as converte em queries SQL através de um modelo de linguagem.

### 4.3 INTERFACE VUE.JS

#### Estratégia de Busca: Server-Side

A implementação da busca/filtro envia o termo digitado para o backend através do parâmetro `?search=TERMO` após um *debounce* de 300ms. Esta decisão foi tomada por escalabilidade: filtrar 1.000 ou 1 milhão de registros no PostgreSQL usando índices de texto é instantâneo, enquanto filtrar no cliente (baixando todo o dataset para o navegador) seria inaceitável em conexões móveis 4G e impossível para datasets maiores. O debounce evita enviar uma requisição a cada tecla pressionada, agrupando a digitação em uma única query.

#### Gerenciamento de Estado: Composables

Ao invés de usar Vuex ou Pinia (stores globais), o sistema utiliza **Composables** (Vue 3 Composition API) para compartilhamento de estado. A justificativa é que a aplicação é dividida em páginas independentes (Dashboard, Listagem, Detalhes) onde o estado é majoritariamente local da view. Composables leves permitem reutilizar lógica (exemplo: fetch de dados com loading e error handling) sem o boilerplate e complexidade de manter uma store global gigante.

#### Performance de Renderização: Server-Side Pagination

A tabela renderiza apenas 10-20 linhas no DOM por vez, com o restante dos dados permanecendo no servidor. Esta estratégia garante que a interface permaneça fluida (60 FPS) mesmo que o banco contenha milhões de registros, pois o navegador nunca é sobrecarregado com manipulação de DOM massivo.

#### Tratamento de Erros e Estados de Loading

A implementação utiliza variáveis reativas (`isLoading`, `error`) para controlar a UI durante requisições assíncronas. Durante o loading, são exibidos *skeleton screens* ou *spinners*, evitando que o usuário interaja com uma tela vazia. Erros de rede são tratados através de interceptors do Axios, mostrando toasts informativos. Estados de dados vazios ("Nenhum resultado encontrado para 'X'") possuem UIs dedicadas que instruem o usuário a modificar o filtro, ao invés de mostrar apenas uma tabela em branco que deixa o usuário confuso.

### 4.4 COMPONENTES DE VISUALIZAÇÃO

O dashboard é composto por seis componentes principais que oferecem diferentes níveis de profundidade analítica:

*   **KPI Grid (Métricas Macro)**: Exibe quatro cartões destacados mostrando Volume Geral de Mercado (soma total de despesas de todas operadoras), Ticket Médio (benchmark calculado como média de gasto por operadora, servindo de régua comparativa), Empresas Ativas (contagem de operadoras que reportaram dados), e Tendência Geral (percentual de crescimento em relação ao trimestre anterior com indicador visual colorido).
*   **Geo Efficiency Chart (Análise Geográfica)**: Gráfico de barras duplas que compara Volume Total por estado (barras azuis) versus Ticket Médio estadual (barras vermelhas). Permite identificar estados pequenos com custos desproporcionalmente altos versus estados grandes com eficiência operacional superior.
*   **Top Movers (Crescimento)**: Lista ranqueada das operadoras com maior crescimento percentual de despesas entre primeiro e último trimestre do período analisado. Identifica empresas em expansão agressiva ou experimentando explosão de custos que merecem investigação detalhada.
*   **Consistency Club (Elite de Estabilidade)**: Componente estilo Pinterest (*masonry layout*) que exibe operadoras que ficaram acima da média de mercado em pelo menos 2 dos 3 trimestres. Representa empresas robustas e financeiramente consistentes. O agrupamento visual por estado facilita análise regional.
*   **Operators Table (Explorador Principal)**: Tabela completa, paginada e pesquisável contendo todas as operadoras. Implementa busca textual *fuzzy* estilo Google que procura simultaneamente em CNPJ e Razão Social. Serve como ponto de entrada principal para drill-down em operadoras específicas.
*   **Operator Modal (Drill-Down Granular)**: Modal de detalhamento que abre ao clicar em qualquer operadora. Exibe dados cadastrais completos (CNPJ, Registro ANS, UF, Modalidade) e tabela de eventos contábeis com tradução automática dos códigos de conta para nomes legíveis (transformando "4.1.1.4" em "Internações - Médico-Hospitalar"), permitindo análise até o nível de lançamento individual.

### 4.5 DOCUMENTAÇÃO DA API

Foi criada uma coleção completa no Postman (`API ANS Analytics.postman_collection.json`) contendo todos os endpoints com exemplos de requisições e descrições detalhadas. A coleção está organizada em cinco seções principais: Listar Operadoras (com demonstração de paginação e busca), Detalhes da Operadora e Despesas, Estatísticas Gerais, Dashboard Storytelling, e Chatbot IA. Cada requisição inclui descrições dos parâmetros aceitos e exemplos de payloads de resposta.

---

## PARTE 5: FUNCIONALIDADES EXTRAS IMPLEMENTADAS

### 5.1 MODO IA: TEXT-TO-SQL CHATBOT

O sistema implementa um chatbot capaz de responder perguntas em linguagem natural sobre os dados, localizado em `api/services/ai_analyst.py`. Implementa uma arquitetura de Engenharia de Software Assistida por LLM (Large Language Model). O sistema não utiliza um modelo treinado especificamente com dados da ANS, mas sim um modelo de propósito geral que atua como tradutor inteligente de linguagem natural para SQL, usando uma técnica simplificada de **RAG (Retrieval-Augmented Generation)**.

#### Arquitetura do Sistema

O fluxo completo funciona em quatro estágios:

5.1.1. **Estágio 1 - Definição do Esquema**: Quando o usuário envia uma pergunta como "Qual operadora gastou mais em São Paulo?", o backend não envia apenas essa frase para a IA. O sistema primeiro injeta um Manual Técnico Completo através de um System Prompt armazenado na constante `DB_SCHEMA`.

Este manual contém três componentes críticos:

*   **Mapeamento de Tabelas**: Define todas as entidades disponíveis no banco de dados, explicando que existe uma tabela operadoras (dimensão) e uma tabela despesas_eventos (fato), com seus respectivos relacionamentos.
*   **Dicionário de Dados**: Lista detalhadamente cada coluna disponível (registro_ans, valor_despesas, uf, modalidade, ano, trimestre), especificando tipos de dados, constraints e significado semântico de cada campo.
*   **Regras de Negócio e Boas Práticas SQL**: Instrui explicitamente a IA sobre padrões obrigatórios. Exemplos extraídos do código real:

    *   "Sempre use JOIN através da chave registro_ans para relacionar tabelas"
    *   "Para agregações financeiras, utilize SUM(d.valor_despesas) com cast para NUMERIC"
    *   "Filtros geográficos devem usar a coluna operadoras.uf em formato de sigla (ex: 'SP', 'RJ')"

5.1.2. **Estágio 2 - Geração de SQL via Groq Cloud**: O sistema utiliza a API da Groq executando o modelo Llama 3.1 (70B parâmetros), escolhido por sua capacidade superior de raciocínio lógico e geração de código estruturado.
Input Completo: System Prompt (contexto do banco) + Pergunta do Usuário (intenção semântica)
Processamento Neural: O Llama 3 analisa a pergunta em linguagem natural, identifica entidades mencionadas (ex: "São Paulo" → uf='SP'), infere operações necessárias (ex: "maior" → ORDER BY DESC LIMIT 1), e sintetiza uma query SQL PostgreSQL válida.

5.1.3. **Estágio 3 - Blindagem de Segurança (Firewall de Queries)**: Antes de executar o SQL gerado, o sistema passa por uma camada de validação de segurança no Python para evitar ataques ou erros:

**Whitelist de Comandos:** Aceita apenas queries que iniciam com `SELECT` ou `WITH` (CTEs). Qualquer outro comando é rejeitado imediatamente.

**Blacklist de Palavras Perigosas:** Bloqueia 100% de comandos destrutivos através de regex case-insensitive que detecta: `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `CREATE`, `TRUNCATE`, `GRANT`, `REVOKE`, `EXEC`, `EXECUTE`.

**Sanitização Anti-Injeção:** Remove tentativas de SQL Injection através da detecção de múltiplos statements (bloqueio de `;` seguido de comando) e validação de estrutura sintática.

**Análise de Complexidade:** Impõe limites de timeout (5 segundos) para prevenir queries maliciosas que tentam consumir recursos computacionais (ex: produtos cartesianos sem JOIN condition).

5.1.4. **Estágio 4 - Execução Segura**: A query aprovada é executada no banco de dados usando uma conexão com usuário `reader` que possui apenas permissões de leitura (SELECT). Os resultados são formatados em JSON e retornados para o frontend, onde são exibidos em formato tabular legível. Se o resultado estiver vazio, o sistema retorna uma mensagem amigável explicando que não encontrou dados, em vez de um erro técnico.

#### Exemplos de Uso

**Pergunta**: "Qual operadora teve o maior crescimento em 2024?"

**SQL Gerado**:

```sql
SELECT o.razao_social,
       ((MAX(CASE WHEN d.trimestre=4 THEN d.valor_despesas END) -
         MAX(CASE WHEN d.trimestre=1 THEN d.valor_despesas END)) /
         MAX(CASE WHEN d.trimestre=1 THEN d.valor_despesas END)) * 100 as crescimento
FROM operadoras o
JOIN despesas_eventos d ON o.registro_ans = d.registro_ans
WHERE d.ano = 2024
GROUP BY o.razao_social
ORDER BY crescimento DESC
LIMIT 1;
```

**Pergunta**: "Quantas operadoras existem no Rio Grande do Sul?"

**SQL Gerado**:

```sql
SELECT COUNT(*) as total
FROM operadoras
WHERE uf = 'RS';
```

Esta funcionalidade democratiza o acesso aos dados, permitindo que usuários não técnicos façam análises complexas sem conhecer SQL.

### 5.2 INTERPRETAÇÃO AUTOMÁTICA DE CÓDIGOS CONTÁBEIS

Os arquivos brutos da ANS contêm despesas codificadas em um sistema hierárquico de contas contábeis. Essas contas são representadas por códigos numéricos (exemplo: `4.1.1.4.03.01`), para descobir o significado de cada código é preciso consultar a tabela de contas contábeis da ANS, que pode ser visualizada em uma planilha disponilizada pela própria ANS nesse site: https://www.gov.br/ans/pt-br/arquivos/assuntos/espaco-da-operadora-de-plano-de-saude/aplicativos-ans/diops/financeiro/2025/DIOPSXML_Financeiro_2025.xlsx/view. Na aba Balancete Despesa da planilha de nome DIOPSXML_Financeiro_2025.xlsx, é possível encontrar o significado de cada código. Armazenar a descrição textual de cada código em banco de dados para cada lançamento seria extremamente redundante (milhões de repetições da string).

#### Solução: Decoding On-Demand no Frontend

A implementação em `frontend/src/components/OperatorModal.vue` nas constantes `CONTEXTS`, `MAPS.modality`, `MAPS.subType`, `MAPS.product` decodifica os códigos apenas no momento da renderização visual. O banco armazena apenas o código numérico, e o Vue.js interpreta seu significado através de mapas de tradução.

#### Lógica dos Dígitos Contábeis

A ANS padroniza as contas do Grupo 4 (Despesas) com uma lógica hierárquica onde o significado dos dígitos muda conforme o contexto:

*   **1º dígito** (sempre 4): Identifica o grupo (Despesas)
*   **3º dígito (Contexto)**: Define a natureza do lançamento
    *   `1`: Avisados (Sinistros)
    *   `4`: IBNR (Não Avisados)
    *   `5`: Resseguro
    *   `6`: Seguro
*   **4º dígito (Classificação)**: O significado depende do contexto (3º dígito)
    *   Para **Avisados (1)**: Indica a **Modalidade** (Fee-for-service, Capitation, Reembolso, SUS...)
    *   Para **IBNR/Outros**: Indica o **Subtipo** (Prêmios, Outras Despesas)
*   **5º dígito (Produto)**: Indica o segmento
    *   `1`: Médico-Hospitalar
    *   `2`: Odontológico

#### Implementação em JavaScript

O código Vue.js implementa esta lógica hierárquica na função `decodeExpenseCode`:

```javascript
/* 1. Mapeamento de Contexto (3º Dígito) */
const CONTEXTS = {
    '1': { label: 'Avisados', type: 'sinistro' },
    '4': { label: 'IBNR', type: 'ibnr' },
    // ...
};

/* 2. Decodificação Hierárquica */
const decodeExpenseCode = (conta) => {
    const digit3 = conta.charAt(2); // Contexto
    const digit4 = conta.charAt(3); // Classificação
    const digit5 = conta.charAt(4); // Produto

    // Lógica condicional baseada no contexto
    if (CONTEXTS[digit3].type === 'sinistro') {
        label4 = MAPS.modality[digit4]; // Ex: SUS, Reembolso
    } else {
        label4 = MAPS.subType[digit4];  // Ex: Prêmios
    }
    
    // ...
};



const resolveProduct = (conta) => {
    const digit4 = conta.charAt(3);
    return PRODUCT_MAP[digit4] || 'Não Classificado';
};

const resolveEvent = (conta) => {
    const digit4 = conta.charAt(3);
    const digit5 = conta.charAt(4);
    
    if (digit4 === '1') {
        return EVENT_MAP_MEDICAL[digit5] || 'Médico NE';
    }
    if (digit4 === '2') {
        return EVENT_MAP_DENTAL[digit5] || 'Odonto NE';
    }
    return 'Não Especificado';
};
```

Esta abordagem permite que o Dashboard Modal exiba tabelas altamente legíveis ("Consultas Médicas: R$ 1.234.567,89") ao invés de códigos crípticos ("4.1.1.1: R$ 1.234.567,89"), sem inflar o tamanho do banco de dados com repetições textuais.

### 5.3 DARK MODE COMPLETO COM GLASSMORPHISM

O sistema implementa um modo escuro profissional que vai além de simples inversão de cores, oferecendo uma experiência visual coesa através de um Design System baseado em **Glassmorphism** (efeito de vidro translúcido).

#### Arquitetura do Sistema de Temas

O gerenciamento de temas é centralizado em um Composable reutilizável `frontend/src/composables/useTheme.js` que implementa três funcionalidades principais:

1.  **Detecção automática de preferência do sistema operacional**: Ao abrir o site pela primeira vez, o código verifica se o Windows/Mac/Linux do usuário está configurado em modo escuro através da API `window.matchMedia('(prefers-color-scheme: dark)')`. Se positivo, o site inicializa automaticamente em dark mode.
2.  **Persistência de preferência do usuário**: Quando o usuário clica no botão de toggle, a escolha é salva em `localStorage`. Isso garante que ao recarregar a página (F5) ou retornar dias depois, o site lembre da preferência individual.
3.  **Controle global via atributo de dados**: O composable injeta o atributo `data-theme="dark"` ou `data-theme="light"` na tag `<html>` raiz do documento. Este atributo serve como "switch mestre" para todo o CSS da aplicação.

#### Design System: Glassmorphism Adaptativo

A estilização implementada em `frontend/src/style.css` cria dois estados visuais distintos:

*   No **Light Mode**, os cartões de interface utilizam a classe `.glass-card` com background branco opaco, bordas sutis e sombras suaves (drop-shadow), criando um visual corporativo clean e profissional.
*   No **Dark Mode**, a mesma classe `.glass-card` sofre transformação visual completa através do seletor CSS `[data-theme="dark"] .glass-card`. Os cartões se tornam semi-transparentes com `background: rgba(60, 60, 60, 0.4)` e recebem o efeito `backdrop-filter: blur(5px)` que cria desfoque do conteúdo atrás, imitando vidro fumê. O texto é forçado para branco usando `color: white !important` e as bordas ganham brilho sutil para definir contornos.

#### Sincronização de Gráficos via MutationObserver

O desafio técnico mais complexo foi sincronizar os gráficos **Chart.js** com o tema. Gráficos renderizados em Canvas HTML5 não respondem automaticamente a mudanças de CSS. Se o usuário alternasse para dark mode, os gráficos permaneceriam com eixos pretos em fundo preto (invisíveis).

A solução implementada em `frontend/src/components/GeoEfficiencyChart.vue` utiliza a API `MutationObserver` do JavaScript. Este observador "vigia" a tag `<html>` aguardando mudanças no atributo `data-theme`. Quando detecta uma mudança:

1.  Destroi a instância atual do gráfico Chart.js
2.  Recalcula as cores apropriadas baseado no novo tema (exemplo: cor dos eixos muda de `#333` para `#fff`)
3.  Recria o gráfico instantaneamente com a nova paleta de cores

Este processo acontece em menos de 100ms, sendo imperceptível para o usuário, que vê uma transição suave e profissional entre os modos claro e escuro.

#### Paleta de Cores por Tema

A paleta foi cuidadosamente escolhida para garantir acessibilidade (contraste WCAG AA):

*   **Light Mode**: Backgrounds brancos (#FFFFFF), textos cinza escuro (#1F2937), acentos azuis (#3B82F6), bordas cinza claro (#E5E7EB).
*   **Dark Mode**: Backgrounds cinza carvão (#1F2937 e #111827), textos brancos (#FFFFFF) e cinza claro (#D1D5DB), acentos azuis mais brilhantes (#60A5FA), bordas cinza médio com transparência.

### 5.4 VISÃO GERAL DOS DASHBOARDS

O sistema oferece seis componentes de visualização que compõem um dashboard analítico profissional:

1.  **KPI Grid (Métricas Macro)**: Exibe quatro cartões destacados mostrando Volume Geral de Mercado (soma total de despesas de todas operadoras), Ticket Médio (benchmark calculado como média de gasto por operadora, servindo de régua comparativa), Empresas Ativas (contagem de operadoras que reportaram dados), e Tendência Geral (percentual de crescimento em relação ao trimestre anterior com indicador visual colorido).
2.  **Geo Efficiency Chart (Análise Geográfica)**: Gráfico de barras duplas que compara Volume Total por estado (barras azuis) versus Ticket Médio estadual (barras vermelhas). Permite identificar estados pequenos com custos desproporcionalmente altos versus estados grandes com eficiência operacional superior.
3.  **Top Movers (Crescimento)**: Lista ranqueada das operadoras com maior crescimento percentual de despesas entre primeiro e último trimestre do período analisado. Identifica empresas em expansão agressiva ou experimentando explosão de custos que merecem investigação detalhada.
4.  **Consistency Club (Elite de Estabilidade)**: Componente estilo Pinterest (masonry layout) que exibe operadoras que ficaram acima da média de mercado em pelo menos 2 dos 3 trimestres. Representa empresas robustas e financeiramente consistentes. O agrupamento visual por estado facilita análise regional.
5.  **Operators Table (Explorador Principal)**: Tabela completa, paginada e pesquisável contendo todas as operadoras. Implementa busca textual fuzzy estilo Google que procura simultaneamente em CNPJ e Razão Social. Serve como ponto de entrada principal para drill-down em operadoras específicas.
6.  **Operator Modal (Drill-Down Granular)**: Modal de detalhamento que abre ao clicar em qualquer operadora. Exibe dados cadastrais completos (CNPJ, Registro ANS, UF, Modalidade) e tabela de eventos contábeis com tradução automática dos códigos de conta para nomes legíveis (transformando "4.1.1.4" em "Internações - Médico-Hospitalar"), permitindo análise até o nível de lançamento individual.
7.  **AI Chat Widget (Análise Livre)**: Widget flutuante posicionado no canto inferior direito que permite fazer perguntas em linguagem natural sobre os dados. Democratiza o acesso à análise permitindo que usuários não técnicos façam consultas complexas sem conhecer SQL.

## Como executar localmente?

### Pré-requisitos

- Python 3.11.6
- PostgreSQL 16.1
- Node.js 22.12.0
- Vue.js 3.4.15
- Chart.js 4.4.0
- FastAPI 0.104.1

### Passo a passo

1. **Clone o repositório**
   ```bash
   git clone <URL_DO_REPOSITORIO>
   ```

2. **Configure o Backend (Python)**
   ```bash
   # Crie um ambiente virtual
   python -m venv .venv

   # Ative o ambiente virtual
   # Windows:
   .venv\Scripts\activate
   # Linux/Mac:
   source .venv/bin/activate

   # Instale as dependências
   pip install -r requirements.txt
   ```

3. **Configure as Variáveis de Ambiente**
   - Crie um arquivo `.env` na raiz do projeto copiando o exemplo:
   - `cp .env.example .env` (ou manualmente no Windows)
   - Edite o `.env` com suas credenciais do PostgreSQL e Groq Cloud.

4. **Prepare o Banco de Dados**
   - Certifique-se que o PostgreSQL está rodando e crie o banco:
   ```sql
   CREATE DATABASE ans_db;
   ```

5. **Execute o ETL (Carga de Dados)**
   - Este passo baixará os dados da ANS, processará e salvará no banco.
   ```bash
   python main.py
   ```

6. **Inicie a API**
   ```bash
   uvicorn api.main:app --reload
   # A API estará disponível em http://localhost:8000
   # Documentação: http://localhost:8000/docs
   ```

7. **Inicie o Frontend**
   ```bash
   cd frontend
   npm install
   npm run dev
   # O site estará disponível em http://localhost:5173
   ```

### Configuração do Ambiente de IA

Crie um arquivo `.env` na raiz do projeto (baseado no `.env.example`):



```ini

# .env

DATABASE_URL=postgresql://postgres:admin@localhost:5432/ans_db

GROQ_API_KEY=gsk_sua_chave_aqui
```


## 🤝 Contribuição

Contribuições são bem-vindas!
Faça um **Fork** do projeto e envie um **Pull Request**.   


## Autor
Rafael Henrique dos Santos Simão

## Contato
(37)99902-7695

## Email
rafaelsantossimao@outlook.com.br

## LinkedIn
https://www.linkedin.com/in/rafael-santos-simao/