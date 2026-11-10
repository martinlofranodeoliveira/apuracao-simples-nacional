"""Pacote de Apuração Determinística do Simples Nacional (LC 123/2006).

LOFRANO TECNOLOGIA.
"""

from .calculator import (
    calcular_aliquota_efetiva,
    calcular_apuracao_mensal,
    calcular_fator_r,
    determinar_anexo_aplicado,
    divisao_teto,
    encontrar_faixa,
    particionar_tributos_hare_niemeyer,
)
from .domain import (
    ApuracaoAtividadeResultado,
    ApuracaoGeralResultado,
    ApuracaoMensalEntrada,
    ReceitaAtividadeEntrada,
    TributoParticionado,
    formatar_centavos_br,
    formatar_fracao_pct,
)
from .errors import (
    ErroCalculo,
    ErroCodec,
    ErroDominio,
    ErroSimplesNacional,
)
from .tabelas_lc123 import (
    AnexoSimples,
    FATOR_R_CORTE,
    LIMITE_MAXIMO_RBT12_CENTAVOS,
    SUBLIMITE_ESTADUAL_CENTAVOS,
    Tributo,
)

__version__ = "1.0.0"

__all__ = [
    "__version__",
    "calcular_aliquota_efetiva",
    "calcular_apuracao_mensal",
    "calcular_fator_r",
    "determinar_anexo_aplicado",
    "divisao_teto",
    "encontrar_faixa",
    "particionar_tributos_hare_niemeyer",
    "ApuracaoAtividadeResultado",
    "ApuracaoGeralResultado",
    "ApuracaoMensalEntrada",
    "ReceitaAtividadeEntrada",
    "TributoParticionado",
    "formatar_centavos_br",
    "formatar_fracao_pct",
    "ErroCalculo",
    "ErroCodec",
    "ErroDominio",
    "ErroSimplesNacional",
    "AnexoSimples",
    "FATOR_R_CORTE",
    "LIMITE_MAXIMO_RBT12_CENTAVOS",
    "SUBLIMITE_ESTADUAL_CENTAVOS",
    "Tributo",
]
