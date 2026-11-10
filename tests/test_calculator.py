"""Testes do motor de cálculo da apuração do Simples Nacional.

LOFRANO TECNOLOGIA.
"""

from fractions import Fraction
import unittest

from apuracao_simples_nacional.calculator import (
    calcular_aliquota_efetiva,
    calcular_apuracao_mensal,
    calcular_fator_r,
    determinar_anexo_aplicado,
    divisao_teto,
    encontrar_faixa,
    particionar_tributos_hare_niemeyer,
)
from apuracao_simples_nacional.domain import (
    ApuracaoMensalEntrada,
    ReceitaAtividadeEntrada,
)
from apuracao_simples_nacional.errors import ERR_DIVISAO_POR_ZERO, ErroCalculo
from apuracao_simples_nacional.tabelas_lc123 import (
    AnexoSimples,
    FATOR_R_CORTE,
    Tributo,
    obter_faixas,
)


class TestCalculator(unittest.TestCase):

    def test_divisao_teto(self) -> None:
        self.assertEqual(divisao_teto(100, 10), 10)
        self.assertEqual(divisao_teto(101, 10), 11)
        self.assertEqual(divisao_teto(0, 5), 0)
        self.assertEqual(divisao_teto(1, 5), 1)

    def test_divisao_teto_por_zero(self) -> None:
        with self.assertRaises(ErroCalculo) as ctx:
            divisao_teto(100, 0)
        self.assertEqual(ctx.exception.codigo, ERR_DIVISAO_POR_ZERO)

    def test_calcular_fator_r_zerados(self) -> None:
        self.assertEqual(calcular_fator_r(0, 0), Fraction(0, 1))
        self.assertEqual(calcular_fator_r(100000, 0), Fraction(1, 1))

    def test_calcular_fator_r_proporcoes(self) -> None:
        # Folha R$ 28.000 / Receita R$ 100.000 -> exatamente 28%
        self.assertEqual(calcular_fator_r(2800000, 10000000), Fraction(28, 100))
        # Folha R$ 25.500 / Receita R$ 85.000 -> 30%
        self.assertEqual(calcular_fator_r(2550000, 8500000), Fraction(3, 10))
        # Folha R$ 10.000 / Receita R$ 100.000 -> 10%
        self.assertEqual(calcular_fator_r(1000000, 10000000), Fraction(1, 10))

    def test_determinar_anexo_aplicado(self) -> None:
        # Atividade sem Fator R: mantém Anexo I
        self.assertEqual(
            determinar_anexo_aplicado(AnexoSimples.ANEXO_I, False, Fraction(1, 10)),
            AnexoSimples.ANEXO_I,
        )
        # Atividade sujeita ao Fator R com Fator R >= 28%: enquadra no Anexo III
        self.assertEqual(
            determinar_anexo_aplicado(AnexoSimples.ANEXO_V, True, Fraction(28, 100)),
            AnexoSimples.ANEXO_III,
        )
        self.assertEqual(
            determinar_anexo_aplicado(AnexoSimples.ANEXO_V, True, Fraction(30, 100)),
            AnexoSimples.ANEXO_III,
        )
        # Atividade sujeita ao Fator R com Fator R < 28%: cai no Anexo V
        self.assertEqual(
            determinar_anexo_aplicado(AnexoSimples.ANEXO_V, True, Fraction(2799, 10000)),
            AnexoSimples.ANEXO_V,
        )
        self.assertEqual(
            determinar_anexo_aplicado(AnexoSimples.ANEXO_III, True, Fraction(15, 100)),
            AnexoSimples.ANEXO_V,
        )

    def test_encontrar_faixa(self) -> None:
        # RBT12 = 0 -> Faixa 1
        self.assertEqual(encontrar_faixa(AnexoSimples.ANEXO_I, 0).numero, 1)
        # RBT12 = R$ 180.000,00 -> Faixa 1
        self.assertEqual(encontrar_faixa(AnexoSimples.ANEXO_I, 18000000).numero, 1)
        # RBT12 = R$ 180.000,01 -> Faixa 2
        self.assertEqual(encontrar_faixa(AnexoSimples.ANEXO_I, 18000001).numero, 2)
        # RBT12 = R$ 360.000,00 -> Faixa 2
        self.assertEqual(encontrar_faixa(AnexoSimples.ANEXO_I, 36000000).numero, 2)
        # RBT12 = R$ 360.000,01 -> Faixa 3
        self.assertEqual(encontrar_faixa(AnexoSimples.ANEXO_I, 36000001).numero, 3)
        # RBT12 = R$ 720.000,01 -> Faixa 4
        self.assertEqual(encontrar_faixa(AnexoSimples.ANEXO_I, 72000001).numero, 4)
        # RBT12 = R$ 1.800.000,01 -> Faixa 5
        self.assertEqual(encontrar_faixa(AnexoSimples.ANEXO_I, 180000001).numero, 5)
        # RBT12 = R$ 3.600.000,01 -> Faixa 6
        self.assertEqual(encontrar_faixa(AnexoSimples.ANEXO_I, 360000001).numero, 6)

    def test_calcular_aliquota_efetiva_faixa_um(self) -> None:
        faixa_1 = obter_faixas(AnexoSimples.ANEXO_I)[0]
        # Na faixa 1, alíquota efetiva é igual à nominal (4%)
        self.assertEqual(calcular_aliquota_efetiva(10000000, faixa_1), Fraction(4, 100))
        self.assertEqual(calcular_aliquota_efetiva(0, faixa_1), Fraction(4, 100))

    def test_calcular_aliquota_efetiva_faixas_superiores(self) -> None:
        # Anexo I, Faixa 2: nominal 7,3%, dedução R$ 5.940,00 (594.000 centavos)
        # RBT12 = R$ 200.000,00 (20.000.000 centavos)
        # Alíquota efetiva = ((200.000 * 0,073) - 5.940) / 200.000 = (14.600 - 5.940) / 200.000 = 8.660 / 200.000 = 4,33%
        faixa_2 = obter_faixas(AnexoSimples.ANEXO_I)[1]
        aliq = calcular_aliquota_efetiva(20000000, faixa_2)
        self.assertEqual(aliq, Fraction(866, 20000))
        self.assertEqual(aliq, Fraction(433, 10000))  # 4,33%

    def test_particionar_tributos_conservacao_centavos(self) -> None:
        faixa_1 = obter_faixas(AnexoSimples.ANEXO_I)[0]
        # DAS de R$ 100,01 (10.001 centavos)
        particao = particionar_tributos_hare_niemeyer(10001, faixa_1.aliquota_nominal, faixa_1.particao_tributos)
        soma_centavos = sum(p.valor_centavos for p in particao)
        self.assertEqual(soma_centavos, 10001)

    def test_particionar_tributos_das_zero(self) -> None:
        faixa_1 = obter_faixas(AnexoSimples.ANEXO_I)[0]
        particao = particionar_tributos_hare_niemeyer(0, faixa_1.aliquota_nominal, faixa_1.particao_tributos)
        for p in particao:
            self.assertEqual(p.valor_centavos, 0)

    def test_apuracao_completa_cenario_real(self) -> None:
        # Cenário canônico: RBT12 R$ 850.000, FS12 R$ 255.000 (Fator R = 30%)
        # COM-01 (Anexo I, Faixa 4): Rec R$ 42.000
        # DEV-02 (Anexo V -> Anexo III Faixa 4 via Fator R): Rec R$ 68.000
        # SUP-03 (Anexo III, Faixa 4): Rec R$ 15.000
        a1 = ReceitaAtividadeEntrada("COM-01", "Comércio", AnexoSimples.ANEXO_I, 4200000, False)
        a2 = ReceitaAtividadeEntrada("DEV-02", "Desenvolvimento", AnexoSimples.ANEXO_V, 6800000, True)
        a3 = ReceitaAtividadeEntrada("SUP-03", "Suporte", AnexoSimples.ANEXO_III, 1500000, False)

        entrada = ApuracaoMensalEntrada("Empresa Teste", "11.222.333/0001-44", "11/2026", 85000000, 25500000, [a1, a2, a3])
        res = calcular_apuracao_mensal(entrada)

        self.assertEqual(res.fator_r, Fraction(3, 10))
        self.assertTrue(res.fator_r_atingido)
        self.assertEqual(res.receita_total_mes_centavos, 12500000)

        # Verificar anexo aplicado em DEV-02
        self.assertEqual(res.atividades[1].anexo_aplicado, AnexoSimples.ANEXO_III)

        # Total do DAS auditado: R$ 13.182,10 (1.318.210 centavos)
        self.assertEqual(res.total_das_centavos, 1318210)

        # Fechamento exato da soma por tributo
        soma_tribs = sum(res.total_por_tributo.values())
        self.assertEqual(soma_tribs, res.total_das_centavos)

    def test_apuracao_com_fator_r_nao_atingido(self) -> None:
        # Folha R$ 10.000 / RBT12 R$ 100.000 -> 10% (< 28%)
        # Atividade Anexo V permanece no Anexo V
        a1 = ReceitaAtividadeEntrada("DEV-01", "Dev TI", AnexoSimples.ANEXO_V, 1000000, True)
        entrada = ApuracaoMensalEntrada("Tech", "12.345.678/0001-90", "11/2026", 10000000, 1000000, [a1])
        res = calcular_apuracao_mensal(entrada)

        self.assertFalse(res.fator_r_atingido)
        self.assertEqual(res.atividades[0].anexo_aplicado, AnexoSimples.ANEXO_V)
        # Anexo V Faixa 1: alíquota 15,5% -> DAS R$ 1.550,00 (155.000 centavos)
        self.assertEqual(res.total_das_centavos, 155000)
