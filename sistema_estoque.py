import csv
from dataclasses import dataclass
from typing import Dict, List
from datetime import datetime
import math


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
    maior_falta_estoque: float = 0.0
    data_maior_falta_estoque: datetime = None
    
    def __post_init__(self):
        self.movimentacoes = []

    def registrar_entrada(self, data: datetime, quantidade: float):
        self.saldo_atual += quantidade
        self.movimentacoes.append(
            Movimentacao(data, 'E', quantidade, self.saldo_atual)
        )
    
    def registrar_saida(self, data: datetime, quantidade: float) -> bool:
        flag = True
        if quantidade > self.saldo_atual:
            flag = False
        self.saldo_atual -= quantidade
        self.movimentacoes.append(
            Movimentacao(data, 'S', quantidade, self.saldo_atual)
        )
        return flag
    
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
        with open('data/percentuais_v2.csv', 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file, delimiter=';')
            for row in reader:
                codigo = int(row['SEQPRODUTO'])
                descricao = row['DESCCOMPLETA']
                percentual = float(row['PERCENTUAL'].replace(',', '.'))
                self.produtos[codigo] = Produto(codigo, descricao, percentual)
            print("Percentuais carregados com sucesso.")

    def carregar_movimentacoes(self):
        """Carrega todas as movimentações (entradas e saídas) e ordena por data"""
        # Carrega entradas
        entradas = []
        with open('data/entradas_v2.csv', 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file, delimiter=';')
            for row in reader:
                data = datetime.strptime(row['DATA'], '%d/%m/%y')
                quantidade = float(row['QUANTIDADE'].replace(',', '.'))
                # Remove a hora da data para comparação
                data_sem_hora = datetime(data.year, data.month, data.day)
                entradas.append(('E', data, quantidade, None))
                self.entrada_total += quantidade
                self.entradas_por_data[data_sem_hora] = self.entradas_por_data.get(data_sem_hora, 0) + quantidade
            print("Entradas carregadas com sucesso.")

        # Carrega vendas
        vendas = []
        with open('data/vendas_v2.csv', 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file, delimiter=';')
            for row in reader:
                data = datetime.strptime(row['DATA'], '%d/%m/%y')
                codigo = int(row['SEQPRODUTO'])
                quantidade = float(row['QUANTIDADE'].replace(',', '.'))
                if codigo in self.produtos:
                    vendas.append(('S', data, quantidade, codigo))
            print("Vendas carregadas com sucesso.\n\n")

        # Combina e ordena todas as movimentações por data
        self.movimentacoes_ordenadas = sorted(entradas + vendas, key=lambda x: x[1])

    def processar_movimentacoes(self):
        """Processa todas as movimentações em ordem cronológica"""
        for tipo, data, quantidade, codigo in self.movimentacoes_ordenadas:
            if tipo == 'E':
                # Entrada do boi casado - distribui para os produtos
                for produto in self.produtos.values():
                    quantidade_derivada = (quantidade * produto.percentual) / 100
                    # if produto.codigo == 145924:
                    #     print(f"$$$$$$$$$$  Quantidade {quantidade} | Perc {produto.percentual} | Quantidade derivada {quantidade_derivada:.3f}")
                    produto.registrar_entrada(data, quantidade_derivada)
            else:
                # Venda de produto específico
                produto = self.produtos[codigo]
                if not produto.registrar_saida(data, quantidade):
                    print(f"ALERTA: Tentativa de venda sem estoque suficiente em {data.strftime('%d/%m/%y')}")
                    print(f"Produto: {produto.codigo} - {produto.descricao}")
                    print(f"Quantidade solicitada: {quantidade:.3f}")
                    print(f"Saldo disponível: {produto.saldo_atual:.3f}")                   
                    self.tem_alertas_estoque = True

                    if produto.maior_falta_estoque > produto.saldo_atual:
                        produto.maior_falta_estoque = produto.saldo_atual
                        produto.data_maior_falta_estoque = data
                        print(f"Quantidade ajustada para o produto: {produto.maior_falta_estoque:.3f} kg")
                    print() 
    
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
        
        produtos_tentativa_negativa = [p for p in self.produtos.values() if p.maior_falta_estoque < 0]

        if produtos_tentativa_negativa:
            print("\nALERTA: Produtos com tentativas de venda com estoque insuficiente:")
            for produto in produtos_tentativa_negativa:
                print(f"- {produto.codigo} {produto.descricao}")
                print(f"  Total de quantidade faltante: {produto.maior_falta_estoque:.3f} kg")
                print(f"  Data da maior falta de estoque: {produto.data_maior_falta_estoque.strftime('%d/%m/%y')}")
                print(f"  Percentual de falta: {self.calcula_percentual_falta(produto, produto.data_maior_falta_estoque)}%\n")

    def calcula_percentual_falta(self, produto, data_limite: datetime) -> float:
        """
        Calcula o percentual de falta de estoque de um produto em relação às entradas até uma data limite.

        Args:
            produto: O produto para o qual o percentual de falta será calculado.
            data_limite: Data limite para considerar as entradas (exclusive).

        Returns:
            float: Percentual de falta arredondado para duas casas decimais
        """

        # percentual_falta = round((produto.maior_falta_estoque * -100) / self.calcular_entradas_ate_data(data_limite), 2)
        # percentual_falta = 0.01 if percentual_falta < 0.01 else math.ceil(percentual_falta * 100) / 100
        # return percentual_falta

        percentual_falta = (produto.maior_falta_estoque * -100) / self.calcular_entradas_ate_data(data_limite)
        return math.ceil(percentual_falta * 100) / 100

    def calcular_entradas_ate_data(self, data_limite: datetime) -> float:
        """
        Calcula a soma de todas as entradas anteriores à data especificada.
        
        Args:
            data_limite: Data limite para considerar as entradas (exclusive)
            
        Returns:
            float: Soma total das entradas anteriores à data especificada
        """
        # Normaliza a data removendo a hora para comparação consistente
        if isinstance(data_limite, datetime):
            data_limite_sem_hora = datetime(data_limite.year, data_limite.month, data_limite.day)
        else:
            # Se a data for fornecida em outro formato, tenta convertê-la
            data_limite_sem_hora = data_limite
        
        # Soma todas as entradas anteriores à data limite
        total_entradas = 0.0
        for data, quantidade in self.entradas_por_data.items():
            if data <= data_limite_sem_hora:
                total_entradas += quantidade
                
        return total_entradas

    def gerar_relatorio_movimentacoes(self, codigo_produto: int = None):
        """Gera um relatório detalhado das movimentações de um produto específico"""
        if codigo_produto is not None and codigo_produto not in self.produtos:
            print(f"Produto {codigo_produto} não encontrado!")
            return
 
        produtos = [self.produtos[codigo_produto]] if codigo_produto else self.produtos.values()
         
        for produto in produtos:
            print(f"\nMOVIMENTAÇÕES - {produto.codigo} {produto.descricao}")
            print("=" * 80)
            print(f"{'Data':<12} {'Tipo':<8} {'Quantidade':>12} {'Saldo':>12}")
            print("-" * 80)
             
            for mov in produto.movimentacoes:
                tipo = "Entrada" if mov.tipo == 'E' else "Saída"
                print(f"{mov.data.strftime('%Y-%m-%d'):<12} "
                      f"{tipo:<8} "
                      f"{mov.quantidade:>12.2f} "
                      f"{mov.saldo_apos:>12.3f}")

if __name__ == "__main__":
    controlador = ControladorEstoque()
    controlador.gerar_relatorio_movimentacoes(145895)
    controlador.gerar_relatorio()
    