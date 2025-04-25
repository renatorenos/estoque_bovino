import csv
from dataclasses import dataclass
from typing import Dict, List
from datetime import datetime


@dataclass
class Movimentacao:
    data: datetime
    tipo: str  # 'E' para entrada, 'S' para saída
    quantidade: float
    saldo_apos: float = 0.0


@dataclass
class Produto:
    codigo: int
    descricao: str
    percentual: float = 0.0
    saldo_atual: float = 0.0
    movimentacoes: List[Movimentacao] = None
    tentativa_venda_negativa: bool = False
    total_falta_estoque: float = 0.0
    vendas_negativas_por_dia: Dict[datetime, int] = None
    dia_mais_vendas_negativas: datetime = None
    qtd_vendas_negativas_no_dia: int = 0
    falta_no_dia_mais_vendas_negativas: float = 0.0

    def __post_init__(self):
        self.movimentacoes = []
        self.vendas_negativas_por_dia = {}

    def registrar_entrada(self, data: datetime, quantidade: float):
        self.saldo_atual += quantidade
        self.movimentacoes.append(
            Movimentacao(data, 'E', quantidade, self.saldo_atual)
        )

    def registrar_saida(self, data: datetime, quantidade: float) -> bool:
        if self.saldo_atual >= quantidade:
            self.saldo_atual -= quantidade
            self.movimentacoes.append(
                Movimentacao(data, 'S', quantidade, self.saldo_atual)
            )
            return True
        else:
            self.tentativa_venda_negativa = True
            falta = quantidade - self.saldo_atual
            self.total_falta_estoque += falta
            
            # Registra a tentativa de venda negativa do dia
            data_sem_hora = datetime(data.year, data.month, data.day)
            self.vendas_negativas_por_dia[data_sem_hora] = self.vendas_negativas_por_dia.get(data_sem_hora, 0) + 1
            
            # Atualiza o dia com mais vendas negativas e a falta total nesse dia
            qtd_atual = self.vendas_negativas_por_dia[data_sem_hora]
            if self.dia_mais_vendas_negativas is None or qtd_atual > self.qtd_vendas_negativas_no_dia:
                self.dia_mais_vendas_negativas = data_sem_hora
                self.qtd_vendas_negativas_no_dia = qtd_atual
                self.falta_no_dia_mais_vendas_negativas = falta
            elif self.dia_mais_vendas_negativas == data_sem_hora:
                self.falta_no_dia_mais_vendas_negativas += falta
            
            return False

    @property
    def total_entradas(self) -> float:
        return sum(m.quantidade for m in self.movimentacoes if m.tipo == 'E')

    @property
    def total_saidas(self) -> float:
        return sum(m.quantidade for m in self.movimentacoes if m.tipo == 'S')


class ControladorEstoque:
    def __init__(self):
        self.produtos: Dict[int, Produto] = {}
        self.produto_base_codigo = 25274
        self.produto_base_descricao = "CARNE BOV RSF KG"
        self.entrada_total = 0.0
        self.entradas_por_data: Dict[datetime, float] = {}
        self.movimentacoes_ordenadas = []
        self.tem_alertas_estoque = False
        
        # Carrega os dados
        self.carregar_produtos_e_percentuais()
        self.carregar_movimentacoes()
        self.processar_movimentacoes()
    
    def carregar_produtos_e_percentuais(self):
        """Carrega os produtos e seus percentuais de rendimento"""
        with open('percentuais_v2.csv', 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file, delimiter=';')
            for row in reader:
                codigo = int(row['SEQPRODUTO'])
                descricao = row['DESCCOMPLETA']
                percentual = float(row['PERCENTUAL'].replace(',', '.'))
                self.produtos[codigo] = Produto(codigo, descricao, percentual)

    def carregar_movimentacoes(self):
        """Carrega todas as movimentações (entradas e saídas) e ordena por data"""
        # Carrega entradas
        entradas = []
        with open('entradas_v2.csv', 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file, delimiter=';')
            for row in reader:
                data = datetime.strptime(row['DATA'], '%d/%m/%y')
                quantidade = float(row['QUANTIDADE'].replace(',', '.'))
                # Remove a hora da data para comparação
                data_sem_hora = datetime(data.year, data.month, data.day)
                entradas.append(('E', data, quantidade, None))
                self.entrada_total += quantidade
                self.entradas_por_data[data_sem_hora] = quantidade

        # Carrega vendas
        vendas = []
        with open('vendas_v2.csv', 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file, delimiter=';')
            for row in reader:
                data = datetime.strptime(row['DATA'], '%d/%m/%y')
                codigo = int(row['SEQPRODUTO'])
                quantidade = float(row['QUANTIDADE'].replace(',', '.'))
                if codigo in self.produtos:
                    vendas.append(('S', data, quantidade, codigo))

        # Combina e ordena todas as movimentações por data
        self.movimentacoes_ordenadas = sorted(entradas + vendas, key=lambda x: x[1])

    def encontrar_entrada_do_dia(self, data: datetime) -> float:
        """Encontra a entrada do dia especificado ou do dia mais próximo anterior"""
        data_sem_hora = datetime(data.year, data.month, data.day)
        
        # Primeiro tenta encontrar entrada no mesmo dia
        if data_sem_hora in self.entradas_por_data:
            return self.entradas_por_data[data_sem_hora]
        
        # Se não encontrar, procura a entrada mais próxima anterior
        datas_anteriores = [d for d in self.entradas_por_data.keys() if d < data_sem_hora]
        if datas_anteriores:
            data_mais_proxima = max(datas_anteriores)
            return self.entradas_por_data[data_mais_proxima]
        
        return 0.0  # Retorna 0 se não encontrar nenhuma entrada anterior

    def processar_movimentacoes(self):
        """Processa todas as movimentações em ordem cronológica"""
        for tipo, data, quantidade, codigo in self.movimentacoes_ordenadas:
            if tipo == 'E':
                # Entrada do boi casado - distribui para os produtos
                for produto in self.produtos.values():
                    quantidade_derivada = (quantidade * produto.percentual) / 100
                    produto.registrar_entrada(data, quantidade_derivada)
            else:
                # Venda de produto específico
                produto = self.produtos[codigo]
                if not produto.registrar_saida(data, quantidade):
                    falta = quantidade - produto.saldo_atual
                    print(f"ALERTA: Tentativa de venda sem estoque suficiente em {data.strftime('%d/%m/%y')}")
                    print(f"Produto: {produto.codigo} - {produto.descricao}")
                    print(f"Quantidade solicitada: {quantidade:.3f}")
                    print(f"Saldo disponível: {produto.saldo_atual:.3f}")
                    print(f"Quantidade faltante: {falta:.3f}")
                    print()                    
                    self.tem_alertas_estoque = True
                    
                    # Armazenar a quantidade faltante no produto
                    if not hasattr(produto, 'total_falta_estoque'):
                        produto.total_falta_estoque = 0
                    produto.total_falta_estoque += falta
                    
    def gerar_relatorio(self):
        """Gera um relatório completo do estoque"""
        print("\nRELATÓRIO DE ESTOQUE - CARNES BOVINAS")
        print("=" * 100)
        
        # Informações do produto base
        print("\nPRODUTO BASE:")
        print(f"Código: {self.produto_base_codigo}")
        print(f"Descrição: {self.produto_base_descricao}")
        print(f"Quantidade Total Entrada: {self.entrada_total:.3f} kg")
        
        # Informações dos produtos derivados
        print("\nPRODUTOS DERIVADOS:")
        print("-" * 100)
        print(f"{'Código':<10} {'Descrição':<40} {'Percentual':<10} {'Entradas':<12} {'Saídas':<12} {'Saldo':<12}")
        print("-" * 100)
        
        total_percentual = 0
        total_entradas = 0
        total_saidas = 0
        total_saldo = 0
        
        for produto in sorted(self.produtos.values(), key=lambda x: x.codigo):
            print(f"{produto.codigo:<10} "
                  f"{produto.descricao[:40]:<40} "
                  f"{produto.percentual:>9.2f}% "
                  f"{produto.total_entradas:>11.2f} "
                  f"{produto.total_saidas:>11.2f} "
                  f"{produto.saldo_atual:>11.2f}")
            
            total_percentual += produto.percentual
            total_entradas += produto.total_entradas
            total_saidas += produto.total_saidas
            total_saldo += produto.saldo_atual
        
        print("-" * 100)
        print(f"{'TOTAL':<51} "
              f"{total_percentual:>9.2f}% "
              f"{total_entradas:>11.2f} "
              f"{total_saidas:>11.2f} "
              f"{total_saldo:>11.2f}")
        
        # Encontra o produto com maior saldo
        produto_maior_saldo = max(self.produtos.values(), key=lambda p: p.saldo_atual)
        print("\nPRODUTO COM MAIOR SALDO:")
        print(f"Código: {produto_maior_saldo.codigo}")
        print(f"Descrição: {produto_maior_saldo.descricao}")
        print(f"Saldo atual: {produto_maior_saldo.saldo_atual:.3f} kg")

        # Validações e alertas
        print("\nVALIDAÇÕES E ALERTAS:")
        if abs(total_percentual - 100) > 0.01:
            print(f"ALERTA: Soma dos percentuais ({total_percentual:.3f}%) não totaliza 100%")
        
        produtos_negativos = [p for p in self.produtos.values() if p.saldo_atual < 0]
        if produtos_negativos:
            print("\nALERTA: Produtos com saldo negativo:")
            for produto in produtos_negativos:
                print(f"- {produto.codigo} {produto.descricao}: {produto.saldo_atual:.3f} kg")
        
        produtos_tentativa_negativa = [p for p in self.produtos.values() if p.tentativa_venda_negativa]
        if produtos_tentativa_negativa:
            print("\nALERTA: Produtos com tentativas de venda com estoque insuficiente:")
            for produto in produtos_tentativa_negativa:
                total_falta = getattr(produto, 'total_falta_estoque', 0)
                print(f"- {produto.codigo} {produto.descricao}")
                print(f"  Total de quantidade faltante: {total_falta:.3f} kg")
                if produto.dia_mais_vendas_negativas:
                    print(f"  Dia com mais tentativas de vendas negativas: {produto.dia_mais_vendas_negativas.strftime('%d/%m/%y')}")
                    print(f"  Quantidade de tentativas neste dia: {produto.qtd_vendas_negativas_no_dia}")
                    print(f"  Total faltante neste dia: {produto.falta_no_dia_mais_vendas_negativas:.3f} kg")
                    # Encontra a entrada correspondente ao dia com mais vendas negativas
                    entrada_do_dia = self.encontrar_entrada_do_dia(produto.dia_mais_vendas_negativas)
                    print(entrada_do_dia)
                    if entrada_do_dia > 0:
                        # porcentagem = (produto.falta_no_dia_mais_vendas_negativas / entrada_do_dia) * 100
                        porcentagem = (total_falta / entrada_do_dia) * 100
                        print(f"  Porcentagem em relação à entrada do dia: {porcentagem:.2f}%")

    def gerar_relatorio_movimentacoes(self, codigo_produto: int = None):
        """Gera um relatório detalhado das movimentações de um produto específico"""
        if codigo_produto is not None and codigo_produto not in self.produtos:
            print(f"Produto {codigo_produto} não encontrado!")
            return

        produtos = [self.produtos[codigo_produto]] if codigo_produto else self.produtos.values()
        
        for produto in produtos:
            print(f"\nMovimentações do produto {produto.codigo} - {produto.descricao}")
            print("-" * 80)
            print(f"{'Data':<12} {'Tipo':<8} {'Quantidade':>12} {'Saldo':>12}")
            print("-" * 80)
            
            for mov in produto.movimentacoes:
                print(f"{mov.data.strftime('%d/%m/%y'):<12} "
                      f"{mov.tipo:<8} "
                      f"{mov.quantidade:>12.3f} "
                      f"{mov.saldo_apos:>12.3f}")
            print("-" * 80)


if __name__ == "__main__":
    controlador = ControladorEstoque()
    controlador.gerar_relatorio()