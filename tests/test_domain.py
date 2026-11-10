"""Testes de invariantes e validação de domínio para apuração do Simples Nacional.

LOFRANO TECNOLOGIA.
"""

from fractions import Fraction
import unittest

from apuracao_simples_nacional.domain import (
    ApuracaoMensalEntrada,
    ReceitaAtividadeEntrada,
    formatar_centavos_br,
    formatar_fracao_pct,
)
from apuracao_simples_nacional.errors import (
    ERR_ANEXO_INVALIDO,
    ERR_ATIVIDADES_VAZIAS,
    ERR_FS12_INVALIDO,
    ERR_RBT12_INVALIDO,
    ERR_RBT12_LIMITE_ULTRAPASSADO,
    ERR_RECEITA_INVALIDA,
    ErroDominio,
)
from apuracao_simples_nacional.tabelas_lc123 import AnexoSimples


class TestDominio(unittest.TestCase):

    def test_formatar_centavos_br(self) -> None:
        self.assertEqual(formatar_centavos_br(0), "R$ 0,00")
        self.assertEqual(formatar_centavos_br(99), "R$ 0,99")
        self.assertEqual(formatar_centavos_br(100), "R$ 1,00")
        self.assertEqual(formatar_centavos_br(123456), "R$ 1.234,56")
        self.assertEqual(formatar_centavos_br(480000000), "R$ 4.800.000,00")
        self.assertEqual(formatar_centavos_br(-500), "-R$ 5,00")

    def test_formatar_fracao_pct(self) -> None:
        self.assertEqual(formatar_fracao_pct(Fraction(0, 1)), "0,0000%")
        self.assertEqual(formatar_fracao_pct(Fraction(4, 100)), "4,0000%")
        self.assertEqual(formatar_fracao_pct(Fraction(28, 100)), "28,0000%")
        self.assertEqual(formatar_fracao_pct(Fraction(1, 3)), "33,3333%")
        self.assertEqual(formatar_fracao_pct(Fraction(1, 8)), "12,5000%")

    def test_atividade_valida(self) -> None:
        a = ReceitaAtividadeEntrada("COM-01", "Comércio", AnexoSimples.ANEXO_I, 100000)
        self.assertEqual(a.codigo, "COM-01")
        self.assertEqual(a.descricao, "Comércio")
        self.assertEqual(a.anexo_base, AnexoSimples.ANEXO_I)
        self.assertEqual(a.receita_mes_centavos, 100000)
        self.assertFalse(a.sujeito_fator_r)

    def test_atividade_codigo_vazio(self) -> None:
        with self.assertRaises(ErroDominio):
            ReceitaAtividadeEntrada("", "Comércio", AnexoSimples.ANEXO_I, 100000)

    def test_atividade_descricao_vazia(self) -> None:
        with self.assertRaises(ErroDominio):
            ReceitaAtividadeEntrada("COM-01", "", AnexoSimples.ANEXO_I, 100000)

    def test_atividade_receita_negativa(self) -> None:
        with self.assertRaises(ErroDominio) as ctx:
            ReceitaAtividadeEntrada("COM-01", "Comércio", AnexoSimples.ANEXO_I, -100)
        self.assertEqual(ctx.exception.codigo, ERR_RECEITA_INVALIDA)

    def test_atividade_fator_r_em_anexo_incompativel(self) -> None:
        # Fator R só se aplica aos Anexos III e V
        with self.assertRaises(ErroDominio) as ctx:
            ReceitaAtividadeEntrada("IND-01", "Indústria", AnexoSimples.ANEXO_II, 100000, sujeito_fator_r=True)
        self.assertEqual(ctx.exception.codigo, ERR_ANEXO_INVALIDO)

    def test_apuracao_entrada_valida(self) -> None:
        a = ReceitaAtividadeEntrada("A1", "Serviço", AnexoSimples.ANEXO_III, 500000)
        e = ApuracaoMensalEntrada("Empresa Exemplo", "11.222.333/0001-44", "11/2026", 12000000, 3600000, [a])
        self.assertEqual(e.razao_social, "Empresa Exemplo")
        self.assertEqual(e.rbt12_centavos, 12000000)
        self.assertEqual(e.fs12_centavos, 3600000)

    def test_apuracao_razao_social_vazia(self) -> None:
        a = ReceitaAtividadeEntrada("A1", "Serviço", AnexoSimples.ANEXO_III, 500000)
        with self.assertRaises(ErroDominio):
            ApuracaoMensalEntrada("", "11.222.333/0001-44", "11/2026", 12000000, 3600000, [a])

    def test_apuracao_cnpj_vazio(self) -> None:
        a = ReceitaAtividadeEntrada("A1", "Serviço", AnexoSimples.ANEXO_III, 500000)
        with self.assertRaises(ErroDominio):
            ApuracaoMensalEntrada("Empresa Exemplo", "", "11/2026", 12000000, 3600000, [a])

    def test_apuracao_competencia_vazia(self) -> None:
        a = ReceitaAtividadeEntrada("A1", "Serviço", AnexoSimples.ANEXO_III, 500000)
        with self.assertRaises(ErroDominio):
            ApuracaoMensalEntrada("Empresa Exemplo", "11.222.333/0001-44", "", 12000000, 3600000, [a])

    def test_apuracao_rbt12_negativo(self) -> None:
        a = ReceitaAtividadeEntrada("A1", "Serviço", AnexoSimples.ANEXO_III, 500000)
        with self.assertRaises(ErroDominio) as ctx:
            ApuracaoMensalEntrada("Empresa Exemplo", "11.222.333/0001-44", "11/2026", -1, 3600000, [a])
        self.assertEqual(ctx.exception.codigo, ERR_RBT12_INVALIDO)

    def test_apuracao_rbt12_acima_do_limite_legal(self) -> None:
        a = ReceitaAtividadeEntrada("A1", "Serviço", AnexoSimples.ANEXO_III, 500000)
        # R$ 4.800.000,01 -> 480.000.001 centavos
        with self.assertRaises(ErroDominio) as ctx:
            ApuracaoMensalEntrada("Empresa Exemplo", "11.222.333/0001-44", "11/2026", 480000001, 3600000, [a])
        self.assertEqual(ctx.exception.codigo, ERR_RBT12_LIMITE_ULTRAPASSADO)

    def test_apuracao_fs12_negativo(self) -> None:
        a = ReceitaAtividadeEntrada("A1", "Serviço", AnexoSimples.ANEXO_III, 500000)
        with self.assertRaises(ErroDominio) as ctx:
            ApuracaoMensalEntrada("Empresa Exemplo", "11.222.333/0001-44", "11/2026", 12000000, -500, [a])
        self.assertEqual(ctx.exception.codigo, ERR_FS12_INVALIDO)

    def test_apuracao_sem_atividades(self) -> None:
        with self.assertRaises(ErroDominio) as ctx:
            ApuracaoMensalEntrada("Empresa Exemplo", "11.222.333/0001-44", "11/2026", 12000000, 3600000, [])
        self.assertEqual(ctx.exception.codigo, ERR_ATIVIDADES_VAZIAS)

    def test_apuracao_atividades_duplicadas(self) -> None:
        a1 = ReceitaAtividadeEntrada("A1", "Serviço 1", AnexoSimples.ANEXO_III, 500000)
        a2 = ReceitaAtividadeEntrada("A1", "Serviço 2", AnexoSimples.ANEXO_III, 300000)
        with self.assertRaises(ErroDominio):
            ApuracaoMensalEntrada("Empresa Exemplo", "11.222.333/0001-44", "11/2026", 12000000, 3600000, [a1, a2])
