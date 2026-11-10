"""Testes das tabelas da Lei Complementar nº 123/2006.

LOFRANO TECNOLOGIA.
"""

from fractions import Fraction
import unittest

from apuracao_simples_nacional.tabelas_lc123 import (
    AnexoSimples,
    LIMITE_MAXIMO_RBT12_CENTAVOS,
    SUBLIMITE_ESTADUAL_CENTAVOS,
    Tributo,
    obter_faixas,
)


class TestTabelasLC123(unittest.TestCase):

    def test_todos_anexos_possuem_seis_faixas(self) -> None:
        for anexo in AnexoSimples:
            faixas = obter_faixas(anexo)
            self.assertEqual(len(faixas), 6, f"{anexo} não possui 6 faixas")

    def test_faixas_crescentes_e_limite_maximo(self) -> None:
        limites_esperados = [
            18_000_000,
            36_000_000,
            72_000_000,
            180_000_000,
            360_000_000,
            480_000_000,
        ]
        for anexo in AnexoSimples:
            faixas = obter_faixas(anexo)
            limites = [f.limite_superior_centavos for f in faixas]
            self.assertEqual(limites, limites_esperados, f"Limites de faixas incorretos para {anexo}")
            self.assertEqual(faixas[-1].limite_superior_centavos, LIMITE_MAXIMO_RBT12_CENTAVOS)

    def test_faixa_um_sempre_tem_deducao_zero(self) -> None:
        for anexo in AnexoSimples:
            faixas = obter_faixas(anexo)
            self.assertEqual(faixas[0].parcela_deduzir_centavos, 0)

    def test_todas_particoes_somam_cem_porcento(self) -> None:
        for anexo in AnexoSimples:
            faixas = obter_faixas(anexo)
            for f in faixas:
                soma = sum(f.particao_tributos.values(), Fraction(0, 1))
                self.assertEqual(
                    soma,
                    Fraction(1, 1),
                    f"Partição de tributos do {anexo} faixa {f.numero} não fecha em 100%: soma={soma}",
                )

    def test_anexo_iv_nao_possui_cpp_no_simples(self) -> None:
        # Pela LC 123/2006, empresas do Anexo IV recolhem CPP à parte na GPS / DCTFWeb
        faixas_iv = obter_faixas(AnexoSimples.ANEXO_IV)
        for f in faixas_iv:
            self.assertNotIn(Tributo.CPP, f.particao_tributos)

    def test_anexo_i_e_ii_possuem_icms_nas_primeiras_faixas(self) -> None:
        for anexo in (AnexoSimples.ANEXO_I, AnexoSimples.ANEXO_II):
            faixas = obter_faixas(anexo)
            for f in faixas[:5]:
                self.assertIn(Tributo.ICMS, f.particao_tributos)
            # Na faixa 6 (acima de 3.6M), ICMS é recolhido no sublimite
            self.assertNotIn(Tributo.ICMS, faixas[5].particao_tributos)

    def test_anexo_iii_iv_v_possuem_iss_nas_primeiras_faixas(self) -> None:
        for anexo in (AnexoSimples.ANEXO_III, AnexoSimples.ANEXO_IV, AnexoSimples.ANEXO_V):
            faixas = obter_faixas(anexo)
            for f in faixas[:5]:
                self.assertIn(Tributo.ISS, f.particao_tributos)
            # Na faixa 6, ISS é recolhido no sublimite
            self.assertNotIn(Tributo.ISS, faixas[5].particao_tributos)

    def test_aliquotas_nominais_iniciais(self) -> None:
        # Anexo I: 4%
        self.assertEqual(obter_faixas(AnexoSimples.ANEXO_I)[0].aliquota_nominal, Fraction(4, 100))
        # Anexo II: 4,5%
        self.assertEqual(obter_faixas(AnexoSimples.ANEXO_II)[0].aliquota_nominal, Fraction(45, 1000))
        # Anexo III: 6%
        self.assertEqual(obter_faixas(AnexoSimples.ANEXO_III)[0].aliquota_nominal, Fraction(6, 100))
        # Anexo IV: 4,5%
        self.assertEqual(obter_faixas(AnexoSimples.ANEXO_IV)[0].aliquota_nominal, Fraction(45, 1000))
        # Anexo V: 15,5%
        self.assertEqual(obter_faixas(AnexoSimples.ANEXO_V)[0].aliquota_nominal, Fraction(155, 1000))
