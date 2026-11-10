"""Tabelas normativas da Lei Complementar nº 123/2006 (atualizada pela LC 155/2016).

Faixas de RBT12, alíquotas nominais, parcelas a deduzir e partições de tributos para os Anexos I a V.
LOFRANO TECNOLOGIA.
"""

from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from typing import Dict, List, Tuple

# Constantes da Lei Complementar 123/2006
LIMITE_MAXIMO_RBT12_CENTAVOS: int = 480_000_000  # R$ 4.800.000,00
SUBLIMITE_ESTADUAL_CENTAVOS: int = 360_000_000   # R$ 3.600.000,00
FATOR_R_CORTE: Fraction = Fraction(28, 100)      # 28%


class AnexoSimples(str, Enum):
    """Anexos da Lei Complementar 123/2006."""
    ANEXO_I = "ANEXO_I"      # Comércio
    ANEXO_II = "ANEXO_II"    # Indústria
    ANEXO_III = "ANEXO_III"  # Serviços em geral / Serviços com Fator R >= 28%
    ANEXO_IV = "ANEXO_IV"    # Serviços específicos (CPP não inclusa no Simples)
    ANEXO_V = "ANEXO_V"      # Serviços intelectuais/tecnologia com Fator R < 28%


class Tributo(str, Enum):
    """Tributos arrecadados pelo Documento de Arrecadação do Simples Nacional (DAS)."""
    IRPJ = "IRPJ"      # Imposto sobre a Renda da Pessoa Jurídica
    CSLL = "CSLL"      # Contribuição Social sobre o Lucro Líquido
    COFINS = "COFINS"  # Contribuição para o Financiamento da Seguridade Social
    PIS = "PIS"        # Programa de Integração Social / PASEP
    CPP = "CPP"        # Contribuição Previdenciária Patronal
    IPI = "IPI"        # Imposto sobre Produtos Industrializados (Anexo II)
    ICMS = "ICMS"      # Imposto sobre Circulação de Mercadorias e Serviços
    ISS = "ISS"        # Imposto Sobre Serviços de Qualquer Natureza


@dataclass(frozen=True)
class FaixaAnexo:
    """Representação exata de uma faixa da LC 123/2006."""
    numero: int
    limite_superior_centavos: int
    aliquota_nominal: Fraction
    parcela_deduzir_centavos: int
    particao_tributos: Dict[Tributo, Fraction]


# Definição canônica das faixas para cada anexo

FAIXAS_ANEXO_I: List[FaixaAnexo] = [
    FaixaAnexo(
        numero=1,
        limite_superior_centavos=18_000_000,
        aliquota_nominal=Fraction(4, 100),
        parcela_deduzir_centavos=0,
        particao_tributos={
            Tributo.IRPJ: Fraction(550, 10000),
            Tributo.CSLL: Fraction(350, 10000),
            Tributo.COFINS: Fraction(1274, 10000),
            Tributo.PIS: Fraction(276, 10000),
            Tributo.CPP: Fraction(4150, 10000),
            Tributo.ICMS: Fraction(3400, 10000),
        },
    ),
    FaixaAnexo(
        numero=2,
        limite_superior_centavos=36_000_000,
        aliquota_nominal=Fraction(73, 1000),
        parcela_deduzir_centavos=594_000,
        particao_tributos={
            Tributo.IRPJ: Fraction(550, 10000),
            Tributo.CSLL: Fraction(350, 10000),
            Tributo.COFINS: Fraction(1274, 10000),
            Tributo.PIS: Fraction(276, 10000),
            Tributo.CPP: Fraction(4150, 10000),
            Tributo.ICMS: Fraction(3400, 10000),
        },
    ),
    FaixaAnexo(
        numero=3,
        limite_superior_centavos=72_000_000,
        aliquota_nominal=Fraction(95, 1000),
        parcela_deduzir_centavos=1_386_000,
        particao_tributos={
            Tributo.IRPJ: Fraction(550, 10000),
            Tributo.CSLL: Fraction(350, 10000),
            Tributo.COFINS: Fraction(1274, 10000),
            Tributo.PIS: Fraction(276, 10000),
            Tributo.CPP: Fraction(4200, 10000),
            Tributo.ICMS: Fraction(3350, 10000),
        },
    ),
    FaixaAnexo(
        numero=4,
        limite_superior_centavos=180_000_000,
        aliquota_nominal=Fraction(107, 1000),
        parcela_deduzir_centavos=2_250_000,
        particao_tributos={
            Tributo.IRPJ: Fraction(550, 10000),
            Tributo.CSLL: Fraction(350, 10000),
            Tributo.COFINS: Fraction(1274, 10000),
            Tributo.PIS: Fraction(276, 10000),
            Tributo.CPP: Fraction(4200, 10000),
            Tributo.ICMS: Fraction(3350, 10000),
        },
    ),
    FaixaAnexo(
        numero=5,
        limite_superior_centavos=360_000_000,
        aliquota_nominal=Fraction(143, 1000),
        parcela_deduzir_centavos=8_730_000,
        particao_tributos={
            Tributo.IRPJ: Fraction(550, 10000),
            Tributo.CSLL: Fraction(350, 10000),
            Tributo.COFINS: Fraction(1274, 10000),
            Tributo.PIS: Fraction(276, 10000),
            Tributo.CPP: Fraction(4200, 10000),
            Tributo.ICMS: Fraction(3350, 10000),
        },
    ),
    FaixaAnexo(
        numero=6,
        limite_superior_centavos=480_000_000,
        aliquota_nominal=Fraction(19, 100),
        parcela_deduzir_centavos=37_800_000,
        particao_tributos={
            Tributo.IRPJ: Fraction(1350, 10000),
            Tributo.CSLL: Fraction(1000, 10000),
            Tributo.COFINS: Fraction(2827, 10000),
            Tributo.PIS: Fraction(613, 10000),
            Tributo.CPP: Fraction(4210, 10000),
        },
    ),
]

FAIXAS_ANEXO_II: List[FaixaAnexo] = [
    FaixaAnexo(
        numero=1,
        limite_superior_centavos=18_000_000,
        aliquota_nominal=Fraction(45, 1000),
        parcela_deduzir_centavos=0,
        particao_tributos={
            Tributo.IRPJ: Fraction(550, 10000),
            Tributo.CSLL: Fraction(350, 10000),
            Tributo.COFINS: Fraction(1151, 10000),
            Tributo.PIS: Fraction(249, 10000),
            Tributo.CPP: Fraction(3750, 10000),
            Tributo.IPI: Fraction(750, 10000),
            Tributo.ICMS: Fraction(3200, 10000),
        },
    ),
    FaixaAnexo(
        numero=2,
        limite_superior_centavos=36_000_000,
        aliquota_nominal=Fraction(78, 1000),
        parcela_deduzir_centavos=594_000,
        particao_tributos={
            Tributo.IRPJ: Fraction(550, 10000),
            Tributo.CSLL: Fraction(350, 10000),
            Tributo.COFINS: Fraction(1151, 10000),
            Tributo.PIS: Fraction(249, 10000),
            Tributo.CPP: Fraction(3750, 10000),
            Tributo.IPI: Fraction(750, 10000),
            Tributo.ICMS: Fraction(3200, 10000),
        },
    ),
    FaixaAnexo(
        numero=3,
        limite_superior_centavos=72_000_000,
        aliquota_nominal=Fraction(10, 100),
        parcela_deduzir_centavos=1_386_000,
        particao_tributos={
            Tributo.IRPJ: Fraction(550, 10000),
            Tributo.CSLL: Fraction(350, 10000),
            Tributo.COFINS: Fraction(1151, 10000),
            Tributo.PIS: Fraction(249, 10000),
            Tributo.CPP: Fraction(3750, 10000),
            Tributo.IPI: Fraction(750, 10000),
            Tributo.ICMS: Fraction(3200, 10000),
        },
    ),
    FaixaAnexo(
        numero=4,
        limite_superior_centavos=180_000_000,
        aliquota_nominal=Fraction(112, 1000),
        parcela_deduzir_centavos=2_250_000,
        particao_tributos={
            Tributo.IRPJ: Fraction(550, 10000),
            Tributo.CSLL: Fraction(350, 10000),
            Tributo.COFINS: Fraction(1151, 10000),
            Tributo.PIS: Fraction(249, 10000),
            Tributo.CPP: Fraction(3750, 10000),
            Tributo.IPI: Fraction(750, 10000),
            Tributo.ICMS: Fraction(3200, 10000),
        },
    ),
    FaixaAnexo(
        numero=5,
        limite_superior_centavos=360_000_000,
        aliquota_nominal=Fraction(147, 1000),
        parcela_deduzir_centavos=8_550_000,
        particao_tributos={
            Tributo.IRPJ: Fraction(550, 10000),
            Tributo.CSLL: Fraction(350, 10000),
            Tributo.COFINS: Fraction(1151, 10000),
            Tributo.PIS: Fraction(249, 10000),
            Tributo.CPP: Fraction(3750, 10000),
            Tributo.IPI: Fraction(750, 10000),
            Tributo.ICMS: Fraction(3200, 10000),
        },
    ),
    FaixaAnexo(
        numero=6,
        limite_superior_centavos=480_000_000,
        aliquota_nominal=Fraction(30, 100),
        parcela_deduzir_centavos=72_000_000,
        particao_tributos={
            Tributo.IRPJ: Fraction(850, 10000),
            Tributo.CSLL: Fraction(750, 10000),
            Tributo.COFINS: Fraction(2096, 10000),
            Tributo.PIS: Fraction(454, 10000),
            Tributo.CPP: Fraction(2350, 10000),
            Tributo.IPI: Fraction(3500, 10000),
        },
    ),
]

FAIXAS_ANEXO_III: List[FaixaAnexo] = [
    FaixaAnexo(
        numero=1,
        limite_superior_centavos=18_000_000,
        aliquota_nominal=Fraction(6, 100),
        parcela_deduzir_centavos=0,
        particao_tributos={
            Tributo.IRPJ: Fraction(400, 10000),
            Tributo.CSLL: Fraction(350, 10000),
            Tributo.COFINS: Fraction(1282, 10000),
            Tributo.PIS: Fraction(278, 10000),
            Tributo.CPP: Fraction(4340, 10000),
            Tributo.ISS: Fraction(3350, 10000),
        },
    ),
    FaixaAnexo(
        numero=2,
        limite_superior_centavos=36_000_000,
        aliquota_nominal=Fraction(112, 1000),
        parcela_deduzir_centavos=936_000,
        particao_tributos={
            Tributo.IRPJ: Fraction(400, 10000),
            Tributo.CSLL: Fraction(350, 10000),
            Tributo.COFINS: Fraction(1405, 10000),
            Tributo.PIS: Fraction(305, 10000),
            Tributo.CPP: Fraction(4340, 10000),
            Tributo.ISS: Fraction(3200, 10000),
        },
    ),
    FaixaAnexo(
        numero=3,
        limite_superior_centavos=72_000_000,
        aliquota_nominal=Fraction(135, 1000),
        parcela_deduzir_centavos=1_764_000,
        particao_tributos={
            Tributo.IRPJ: Fraction(400, 10000),
            Tributo.CSLL: Fraction(350, 10000),
            Tributo.COFINS: Fraction(1364, 10000),
            Tributo.PIS: Fraction(296, 10000),
            Tributo.CPP: Fraction(4340, 10000),
            Tributo.ISS: Fraction(3250, 10000),
        },
    ),
    FaixaAnexo(
        numero=4,
        limite_superior_centavos=180_000_000,
        aliquota_nominal=Fraction(16, 100),
        parcela_deduzir_centavos=3_564_000,
        particao_tributos={
            Tributo.IRPJ: Fraction(400, 10000),
            Tributo.CSLL: Fraction(350, 10000),
            Tributo.COFINS: Fraction(1364, 10000),
            Tributo.PIS: Fraction(296, 10000),
            Tributo.CPP: Fraction(4340, 10000),
            Tributo.ISS: Fraction(3250, 10000),
        },
    ),
    FaixaAnexo(
        numero=5,
        limite_superior_centavos=360_000_000,
        aliquota_nominal=Fraction(21, 100),
        parcela_deduzir_centavos=12_564_000,
        particao_tributos={
            Tributo.IRPJ: Fraction(400, 10000),
            Tributo.CSLL: Fraction(350, 10000),
            Tributo.COFINS: Fraction(1282, 10000),
            Tributo.PIS: Fraction(278, 10000),
            Tributo.CPP: Fraction(4340, 10000),
            Tributo.ISS: Fraction(3350, 10000),
        },
    ),
    FaixaAnexo(
        numero=6,
        limite_superior_centavos=480_000_000,
        aliquota_nominal=Fraction(33, 100),
        parcela_deduzir_centavos=64_800_000,
        particao_tributos={
            Tributo.IRPJ: Fraction(3500, 10000),
            Tributo.CSLL: Fraction(1500, 10000),
            Tributo.COFINS: Fraction(1603, 10000),
            Tributo.PIS: Fraction(347, 10000),
            Tributo.CPP: Fraction(3050, 10000),
        },
    ),
]

FAIXAS_ANEXO_IV: List[FaixaAnexo] = [
    FaixaAnexo(
        numero=1,
        limite_superior_centavos=18_000_000,
        aliquota_nominal=Fraction(45, 1000),
        parcela_deduzir_centavos=0,
        particao_tributos={
            Tributo.IRPJ: Fraction(1880, 10000),
            Tributo.CSLL: Fraction(1520, 10000),
            Tributo.COFINS: Fraction(1767, 10000),
            Tributo.PIS: Fraction(383, 10000),
            Tributo.ISS: Fraction(4450, 10000),
        },
    ),
    FaixaAnexo(
        numero=2,
        limite_superior_centavos=36_000_000,
        aliquota_nominal=Fraction(9, 100),
        parcela_deduzir_centavos=810_000,
        particao_tributos={
            Tributo.IRPJ: Fraction(1980, 10000),
            Tributo.CSLL: Fraction(1520, 10000),
            Tributo.COFINS: Fraction(2055, 10000),
            Tributo.PIS: Fraction(445, 10000),
            Tributo.ISS: Fraction(4000, 10000),
        },
    ),
    FaixaAnexo(
        numero=3,
        limite_superior_centavos=72_000_000,
        aliquota_nominal=Fraction(102, 1000),
        parcela_deduzir_centavos=1_242_000,
        particao_tributos={
            Tributo.IRPJ: Fraction(2080, 10000),
            Tributo.CSLL: Fraction(1520, 10000),
            Tributo.COFINS: Fraction(1973, 10000),
            Tributo.PIS: Fraction(427, 10000),
            Tributo.ISS: Fraction(4000, 10000),
        },
    ),
    FaixaAnexo(
        numero=4,
        limite_superior_centavos=180_000_000,
        aliquota_nominal=Fraction(14, 100),
        parcela_deduzir_centavos=3_978_000,
        particao_tributos={
            Tributo.IRPJ: Fraction(1780, 10000),
            Tributo.CSLL: Fraction(1920, 10000),
            Tributo.COFINS: Fraction(1890, 10000),
            Tributo.PIS: Fraction(410, 10000),
            Tributo.ISS: Fraction(4000, 10000),
        },
    ),
    FaixaAnexo(
        numero=5,
        limite_superior_centavos=360_000_000,
        aliquota_nominal=Fraction(22, 100),
        parcela_deduzir_centavos=18_378_000,
        particao_tributos={
            Tributo.IRPJ: Fraction(1880, 10000),
            Tributo.CSLL: Fraction(1920, 10000),
            Tributo.COFINS: Fraction(1808, 10000),
            Tributo.PIS: Fraction(392, 10000),
            Tributo.ISS: Fraction(4000, 10000),
        },
    ),
    FaixaAnexo(
        numero=6,
        limite_superior_centavos=480_000_000,
        aliquota_nominal=Fraction(33, 100),
        parcela_deduzir_centavos=82_800_000,
        particao_tributos={
            Tributo.IRPJ: Fraction(5350, 10000),
            Tributo.CSLL: Fraction(2150, 10000),
            Tributo.COFINS: Fraction(2055, 10000),
            Tributo.PIS: Fraction(445, 10000),
        },
    ),
]

FAIXAS_ANEXO_V: List[FaixaAnexo] = [
    FaixaAnexo(
        numero=1,
        limite_superior_centavos=18_000_000,
        aliquota_nominal=Fraction(155, 1000),
        parcela_deduzir_centavos=0,
        particao_tributos={
            Tributo.IRPJ: Fraction(2500, 10000),
            Tributo.CSLL: Fraction(1500, 10000),
            Tributo.COFINS: Fraction(1410, 10000),
            Tributo.PIS: Fraction(305, 10000),
            Tributo.CPP: Fraction(2885, 10000),
            Tributo.ISS: Fraction(1400, 10000),
        },
    ),
    FaixaAnexo(
        numero=2,
        limite_superior_centavos=36_000_000,
        aliquota_nominal=Fraction(18, 100),
        parcela_deduzir_centavos=450_000,
        particao_tributos={
            Tributo.IRPJ: Fraction(2300, 10000),
            Tributo.CSLL: Fraction(1500, 10000),
            Tributo.COFINS: Fraction(1410, 10000),
            Tributo.PIS: Fraction(305, 10000),
            Tributo.CPP: Fraction(2785, 10000),
            Tributo.ISS: Fraction(1700, 10000),
        },
    ),
    FaixaAnexo(
        numero=3,
        limite_superior_centavos=72_000_000,
        aliquota_nominal=Fraction(195, 1000),
        parcela_deduzir_centavos=990_000,
        particao_tributos={
            Tributo.IRPJ: Fraction(2400, 10000),
            Tributo.CSLL: Fraction(1500, 10000),
            Tributo.COFINS: Fraction(1492, 10000),
            Tributo.PIS: Fraction(323, 10000),
            Tributo.CPP: Fraction(2385, 10000),
            Tributo.ISS: Fraction(1900, 10000),
        },
    ),
    FaixaAnexo(
        numero=4,
        limite_superior_centavos=180_000_000,
        aliquota_nominal=Fraction(205, 1000),
        parcela_deduzir_centavos=1_710_000,
        particao_tributos={
            Tributo.IRPJ: Fraction(2100, 10000),
            Tributo.CSLL: Fraction(1500, 10000),
            Tributo.COFINS: Fraction(1574, 10000),
            Tributo.PIS: Fraction(341, 10000),
            Tributo.CPP: Fraction(2385, 10000),
            Tributo.ISS: Fraction(2100, 10000),
        },
    ),
    FaixaAnexo(
        numero=5,
        limite_superior_centavos=360_000_000,
        aliquota_nominal=Fraction(23, 100),
        parcela_deduzir_centavos=6_210_000,
        particao_tributos={
            Tributo.IRPJ: Fraction(2300, 10000),
            Tributo.CSLL: Fraction(1250, 10000),
            Tributo.COFINS: Fraction(1410, 10000),
            Tributo.PIS: Fraction(305, 10000),
            Tributo.CPP: Fraction(2385, 10000),
            Tributo.ISS: Fraction(2350, 10000),
        },
    ),
    FaixaAnexo(
        numero=6,
        limite_superior_centavos=480_000_000,
        aliquota_nominal=Fraction(305, 1000),
        parcela_deduzir_centavos=54_000_000,
        particao_tributos={
            Tributo.IRPJ: Fraction(3500, 10000),
            Tributo.CSLL: Fraction(1550, 10000),
            Tributo.COFINS: Fraction(1644, 10000),
            Tributo.PIS: Fraction(356, 10000),
            Tributo.CPP: Fraction(2950, 10000),
        },
    ),
]

TABELAS_ANEXOS: Dict[AnexoSimples, List[FaixaAnexo]] = {
    AnexoSimples.ANEXO_I: FAIXAS_ANEXO_I,
    AnexoSimples.ANEXO_II: FAIXAS_ANEXO_II,
    AnexoSimples.ANEXO_III: FAIXAS_ANEXO_III,
    AnexoSimples.ANEXO_IV: FAIXAS_ANEXO_IV,
    AnexoSimples.ANEXO_V: FAIXAS_ANEXO_V,
}


def obter_faixas(anexo: AnexoSimples) -> List[FaixaAnexo]:
    """Retorna a lista de 6 faixas do anexo informado."""
    return TABELAS_ANEXOS[anexo]
