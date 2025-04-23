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

    def __post_init__(self):
        self.movimentacoes = []

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
        self.movimentacoes_ordenadas = []
        self.tem_alertas_estoque = False
        
        # Carrega os dados
        self.carregar_produtos_e_percentuais()
        self.carregar_movimentacoes()
        self.processar_movimentacoes()
    
    def carregar_produtos_e_percentuais(self):
        """Carrega os produtos e seus percentuais de rendimento"""
        with open('percentuais.csv', 'r', encoding='utf-8') as file:
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
        with open('entradas.csv', 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file, delimiter=';')
            for row in reader:
                data = datetime.strptime(row['DATA'], '%d/%m/%y')
                quantidade = float(row['QUANTIDADE'].replace(',', '.'))
                entradas.append(('E', data, quantidade, None))
                self.entrada_total += quantidade

        # Carrega vendas
        vendas = []
        with open('vendas.csv', 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file, delimiter=';')
            for row in reader:
                data = datetime.strptime(row['DATA'], '%d/%m/%y')
                codigo = int(row['SEQPRODUTO'])
                quantidade = float(row['QUANTIDADE'].replace(',', '.'))
                if codigo in self.produtos:
                    vendas.append(('S', data, quantidade, codigo))

        # Combina e ordena todas as movimentações por data
        self.movimentacoes_ordenadas = sorted(entradas + vendas, key=lambda x: x[1])

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
                    print(f"ALERTA: Tentativa de venda sem estoque suficiente em {data.strftime('%d/%m/%y')}")
                    print(f"Produto: {produto.codigo} - {produto.descricao}")
                    print(f"Quantidade solicitada: {quantidade:.3f}")
                    print(f"Saldo disponível: {produto.saldo_atual:.3f}")
                    print()                    
                    self.tem_alertas_estoque = True
                    
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
        
        # Validações e alertas
        print("\nVALIDAÇÕES E ALERTAS:")
        if abs(total_percentual - 100) > 0.01:
            print(f"ALERTA: Soma dos percentuais ({total_percentual:.3f}%) não totaliza 100%")
        
        produtos_negativos = [p for p in self.produtos.values() if p.saldo_atual < 0]
        if produtos_negativos:
            print("\nALERTA: Produtos com saldo negativo:")
            for produto in produtos_negativos:
                print(f"- {produto.codigo} {produto.descricao}: {produto.saldo_atual:.3f} kg")

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
                      f"{mov.saldo_apos:>12.2f}")

    def calcular_percentuais_ideais(self):
        """
        Calcula os percentuais ideais para cada produto baseado nas movimentações reais,
        considerando a frequência dos problemas de estoque e o padrão de consumo.
        
        Returns:
            Dict[int, float]: Dicionário com código do produto e percentual ideal
        """
        percentuais_ideais = {}
        ajustes_necessarios = {}
        
        # Primeira passagem: analisa os problemas de cada produto
        for codigo, produto in self.produtos.items():
            # Analisa o padrão real de movimentações
            total_dias = len(produto.movimentacoes)
            if total_dias == 0:
                ajustes_necessarios[codigo] = 0
                continue
            
            # Conta dias com problemas e calcula gravidade
            dias_com_problema = 0
            soma_problemas = 0
            
            for mov in produto.movimentacoes:
                if mov.tipo == 'S':
                    if mov.saldo_apos < 0:
                        dias_com_problema += 1
                        soma_problemas += abs(mov.saldo_apos)
            
            # Se não tem problemas, não precisa de ajuste
            if dias_com_problema == 0:
                ajustes_necessarios[codigo] = 0
                continue
            
            # Calcula o fator de ajuste baseado na frequência e gravidade dos problemas
            frequencia = dias_com_problema / total_dias
            gravidade = soma_problemas / (produto.total_saidas if produto.total_saidas > 0 else 1)
            
            # O ajuste será proporcional aos problemas
            ajuste = min(frequencia + gravidade, 0.5)  # limita o ajuste a 50%
            ajustes_necessarios[codigo] = ajuste
            
            # Debug para análise detalhada
            if codigo == 145889:
                print(f"\nAnálise detalhada para {codigo} - {produto.descricao}:")
                print(f"Percentual atual: {produto.percentual:.2f}%")
                print(f"Dias com problema: {dias_com_problema}")
                print(f"Total dias: {total_dias}")
                print(f"Frequência de problemas: {frequencia:.2f}")
                print(f"Gravidade dos problemas: {gravidade:.2f}")
                print(f"Ajuste calculado: {ajuste:.2f}")
        
        # Segunda passagem: aplica os ajustes mantendo a soma em 100%
        total_atual = sum(p.percentual for p in self.produtos.values())
        
        # Calcula os novos percentuais
        for codigo, produto in self.produtos.items():
            ajuste = ajustes_necessarios[codigo]
            if ajuste > 0:
                # Aumenta o percentual para produtos com problemas
                percentual_ideal = produto.percentual * (1 + ajuste)
            else:
                # Mantém o mesmo percentual para produtos sem problemas
                percentual_ideal = produto.percentual
            percentuais_ideais[codigo] = percentual_ideal
        
        # Normaliza para manter a soma em 100%
        total_novo = sum(percentuais_ideais.values())
        fator_normalizacao = total_atual / total_novo
        
        # Aplica a normalização e arredonda
        for codigo in percentuais_ideais:
            percentuais_ideais[codigo] = round(percentuais_ideais[codigo] * fator_normalizacao, 2)
            
            # Debug para produto específico
            if codigo == 145889:
                print(f"\nAnálise detalhada para {codigo}:")
                print(f"Percentual atual: {self.produtos[codigo].percentual:.2f}%")
                print(f"Ajuste calculado: {ajustes_necessarios[codigo]:.2f}")
                print(f"Percentual após ajuste: {percentuais_ideais[codigo]:.2f}%")
        
        # Gera relatório comparativo
        print("\nPERCENTUAIS IDEAIS VS ATUAIS:")
        print("=" * 100)
        print(f"{'Código':<10} {'Descrição':<40} {'% Atual':<10} {'% Ideal':<10} {'Diferença':<10}")
        print("-" * 100)
        
        for codigo, percentual_ideal in sorted(percentuais_ideais.items()):
            produto = self.produtos[codigo]
            diferenca = round(percentual_ideal, 2) - round(produto.percentual, 2)
            diferenca_formatada = f"+{diferenca:.2f}%" if round(diferenca, 2) >= 0.01 else f"{diferenca:.2f}%"
            print(f"{codigo:<10} "
                  f"{produto.descricao[:40]:<40} "
                  f"{produto.percentual:>9.2f}% "
                  f"{percentual_ideal:>9.2f}% "
                  f"{diferenca_formatada:>10}")
        
        print("-" * 100)
        print(f"{'TOTAL':<51} {total_atual:>9.2f}% {sum(percentuais_ideais.values()):>9.2f}%")
        
        return percentuais_ideais
            percentuais_ideais[ultimo_codigo] = round(diferenca, 2)
            percentuais_ideais[codigo] = percentual_ideal
            
        # Gera relatório comparativo
        print("\nPERCENTUAIS IDEAIS VS ATUAIS:")
        print("=" * 100)
        print(f"{'Código':<10} {'Descrição':<40} {'% Atual':<10} {'% Ideal':<10} {'Diferença':<10}")
        print("-" * 100)
        
        for codigo, percentual_ideal in sorted(percentuais_ideais.items()):
            produto = self.produtos[codigo]
            diferenca = round(percentual_ideal, 2) - round(produto.percentual, 2)
            diferenca_formatada = f"+{diferenca:.2f}%" if round(diferenca, 2) >= 0.01 else f"{diferenca:.2f}%"
            print(f"{codigo:<10} "
                  f"{produto.descricao[:40]:<40} "
                  f"{produto.percentual:>9.2f}% "
                  f"{percentual_ideal:>9.2f}% "
                  f"{diferenca_formatada:>10}")
        
        total_atual = sum(p.percentual for p in self.produtos.values())
        total_ideal = sum(percentuais_ideais.values())
        print("-" * 100)
        print(f"{'TOTAL':<51} {total_atual:>9.2f}% {total_ideal:>9.2f}%")
        
        # Gerar arquivo CSV com os percentuais ideais
        with open('percentuais_ideais.csv', 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file, delimiter=";")
            writer.writerow(['SEQPRODUTO', 'DESCCOMPLETA', 'PERCENTUAL'])
            for codigo, percentual_ideal in sorted(percentuais_ideais.items()):
                produto = self.produtos[codigo]
                writer.writerow([codigo, produto.descricao, f"{percentual_ideal:.2f}".replace('.', ',')])

        return percentuais_ideais

def main():
    controlador = ControladorEstoque()
    controlador.gerar_relatorio()
    
    # Exemplo de relatório detalhado para um produto específico
    # print("\nRelatório detalhado de movimentações:")
    # controlador.gerar_relatorio_movimentacoes(145924)  # Exemplo com um código específico
    # Calcula os percentuais ideais apenas se houver alertas de estoque insuficiente
    if controlador.tem_alertas_estoque:
        print("\nForam detectadas tentativas de venda sem estoque suficiente.")
        print("Calculando percentuais ideais para evitar este problema...")
        controlador.calcular_percentuais_ideais()
    else:
        print("\nNão foram detectados problemas de estoque insuficiente.")
        print("Não é necessário recalcular os percentuais.")
if __name__ == "__main__":
    main()
    