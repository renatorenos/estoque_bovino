# Sistema de Controle de Estoque de Carnes Bovinas

Este sistema implementa um controle de estoque especializado para carnes bovinas, onde um produto base (boi casado) é dividido em diversos cortes (produtos derivados), cada um com seu percentual de rendimento específico. O sistema mantém o controle de entradas, saídas e saldos, gerando alertas quando necessário e fornecendo relatórios detalhados da situação do estoque.

## Estruturas de Dados

### Classe Movimentacao
- **data**: data/hora da movimentação
- **tipo**: texto ('E' para entrada, 'S' para saída)
- **quantidade**: número decimal
- **saldo_após**: número decimal

### Classe Produto
- **código**: inteiro
- **descrição**: texto
- **percentual**: número decimal
- **saldo_atual**: número decimal
- **movimentações**: lista de Movimentacao
- **maior_falta_estoque**: número decimal
- **data_maior_falta_estoque**: data/hora
- **percentual_ideal**: número decimal

### Classe ControladorEstoque
- **produtos**: dicionário de Produto
- **produto_base_código**: inteiro
- **produto_base_descrição**: texto
- **entrada_total**: número decimal
- **entradas_por_data**: dicionário de data -> quantidade
- **movimentações_ordenadas**: lista de movimentações
- **tem_alertas_estoque**: booleano

## Fluxo do Sistema

### 1. Inicialização do Sistema
1. Criar novo ControladorEstoque
2. Carregar produtos e percentuais do arquivo CSV
3. Carregar movimentações
4. Processar movimentações

### 2. Carregamento de Produtos e Percentuais
1. Abrir arquivo CSV de percentuais
2. Para cada linha do arquivo:
   - Extrair código, descrição e percentual
   - Criar novo Produto
   - Adicionar ao dicionário de produtos

### 3. Carregamento de Movimentações
1. **Carregar Entradas:**
   - Ler arquivo de entradas
   - Para cada entrada:
     * Converter data e quantidade
     * Adicionar à lista de movimentações
     * Atualizar entrada_total
     * Atualizar entradas_por_data

2. **Carregar Vendas:**
   - Ler arquivo de vendas
   - Para cada venda:
     * Converter data, código e quantidade
     * Se produto existe, adicionar à lista de movimentações

3. Ordenar todas as movimentações por data

### 4. Processamento de Movimentações
Para cada movimentação ordenada:
- **Se tipo é 'E' (Entrada):**
  * Para cada produto:
    - Calcular quantidade derivada (quantidade * percentual / 100)
    - Registrar entrada no produto
- **Se tipo é 'S' (Saída):**
  * Localizar produto específico
  * Tentar registrar saída
  * Se saldo insuficiente:
    - Gerar alerta
    - Atualizar maior falta de estoque se necessário

### 5. Geração de Relatório
1. Exibir informações do produto base
2. Exibir lista de produtos derivados com:
   - Código
   - Descrição
   - Percentual
   - Total de entradas
   - Total de saídas
   - Saldo atual
3. Calcular e exibir totais
4. Identificar e exibir produto com maior saldo
5. Exibir validações e alertas:
   - Verificar se percentuais somam 100%
   - Listar produtos com saldo negativo
   - Listar produtos com tentativas de saldo negativo

## Fluxo de Dados

### Entrada de Dados
- Arquivo de percentuais (CSV)
- Arquivo de entradas (CSV)
- Arquivo de vendas (CSV)

### Processamento
1. Carregamento de produtos e percentuais
2. Carregamento de movimentações
3. Ordenação cronológica
4. Processamento de entradas (distribuição proporcional)
5. Processamento de saídas (verificação de saldo)
6. Cálculo de totais e estatísticas

### Saída de Dados
- Relatório de estoque
- Alertas de estoque insuficiente
- Estatísticas de movimentação
- Validações de percentuais e saldos

## Regras de Negócio

1. Cada produto tem um percentual de rendimento em relação ao produto base
2. Entradas são distribuídas proporcionalmente conforme percentual de cada produto
3. Saídas são registradas individualmente por produto
4. Sistema monitora e alerta sobre tentativas de saída com saldo insuficiente
5. Mantém registro histórico de todas as movimentações
6. Valida se a soma dos percentuais totaliza 100%
7. Controla saldos negativos e maiores faltas de estoque