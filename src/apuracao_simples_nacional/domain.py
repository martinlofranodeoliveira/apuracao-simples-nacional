"""Modelos de domínio e invariantes de negócio para apuração do Simples Nacional.

LOFRANO TECNOLOGIA.
"""

from dataclasses import dataclass, field
from fractions import Fraction
import re
from typing import Dict, List

from .errors import (
    ERR_ANEXO_INVALIDO,
    ERR_ATIVIDADES_VAZIAS,
    ERR_FS12_INVALIDO,
    ERR_RBT12_INVALIDO,
    ERR_RBT12_LIMITE_ULTRAPASSADO,
    ERR_RECEITA_INVALIDA,
    ErroDominio,
)
from .tabelas_lc123 import (
    AnexoSimples,
    LIMITE_MAXIMO_RBT12_CENTAVOS,
    Tributo,
)


def formatar_centavos_br(centavos: int) -> str:
    """Formata valor inteiro em centavos para moeda brasileira: R$ 1.234,56."""
    sinal = "-" if centavos < 0 else ""
    abs_centavos = abs(centavos)
    reais = abs_centavos // 100
    resto = abs_centavos % 100
    reais_formatados = f"{reais:,}".replace(",", ".")
    return f"{sinal}R$ {reais_formatados},{resto:02d}"


def formatar_fracao_pct(frac: Fraction, casas: int = 4) -> str:
    """Formata fração racional como porcentagem com casas decimais: 4,0000%."""
    # Ex: Fraction(4, 100) -> 4,0000%
    fator = 10 ** casas
    # Multiplica por 100 para percentual, e por fator para casas decimais
    num = frac.numerator * 100 * fator
    den = frac.denominator
    # Divisão inteira arredondada para o mais próximo
    val_inteiro = (num + den // 2) // den
    inteiro_pct = val_inteiro // fator
    resto = val_inteiro % fator
    return f"{inteiro_pct},{resto:0{casas}d}%"


@dataclass(frozen=True)
class ReceitaAtividadeEntrada:
    """Entrada de receita bruta no mês por atividade econômica."""
    codigo: str
    descricao: str
    anexo_base: AnexoSimples
    receita_mes_centavos: int
    sujeito_fator_r: bool = False

    def __post_init__(self) -> None:
        if not self.codigo or not self.codigo.strip():
            raise ErroDominio("O código da atividade não pode ser vazio.", "CODIGO_VAZIO")
        if not self.descricao or not self.descricao.strip():
            raise ErroDominio(f"A descrição da atividade '{self.codigo}' não pode ser vazia.", "DESCRICAO_VAZIA")
        if not isinstance(self.anexo_base, AnexoSimples):
            raise ErroDominio(f"Anexo base inválido na atividade '{self.codigo}'.", ERR_ANEXO_INVALIDO)
        if not isinstance(self.receita_mes_centavos, int) or self.receita_mes_centavos < 0:
            raise ErroDominio(
                f"A receita do mês da atividade '{self.codigo}' deve ser um inteiro não-negativo em centavos.",
                ERR_RECEITA_INVALIDA,
            )
        if self.sujeito_fator_r and self.anexo_base not in (AnexoSimples.ANEXO_III, AnexoSimples.ANEXO_V):
            raise ErroDominio(
                f"Atividade '{self.codigo}' sujeita ao Fator R deve ter anexo base III ou V.",
                ERR_ANEXO_INVALIDO,
            )


@dataclass(frozen=True)
class ApuracaoMensalEntrada:
    """Dados cadastrais e financeiros para apuração mensal do Simples Nacional."""
    razao_social: str
    cnpj: str
    competencia_mes_ano: str
    rbt12_centavos: int
    fs12_centavos: int
    atividades: List[ReceitaAtividadeEntrada]

    def __post_init__(self) -> None:
        if not self.razao_social or not self.razao_social.strip():
            raise ErroDominio("A razão social é obrigatória.", "RAZAO_SOCIAL_VAZIA")
        if not self.cnpj or not self.cnpj.strip():
            raise ErroDominio("O CNPJ é obrigatório.", "CNPJ_VAZIO")
        if not self.competencia_mes_ano or not self.competencia_mes_ano.strip():
            raise ErroDominio("A competência (mês/ano) é obrigatória.", "COMPETENCIA_VAZIA")
        if not isinstance(self.rbt12_centavos, int) or self.rbt12_centavos < 0:
            raise ErroDominio(
                "A Receita Bruta Acumulada (RBT12) deve ser um inteiro não-negativo em centavos.",
                ERR_RBT12_INVALIDO,
            )
        if self.rbt12_centavos > LIMITE_MAXIMO_RBT12_CENTAVOS:
            raise ErroDominio(
                f"RBT12 ({formatar_centavos_br(self.rbt12_centavos)}) excede o limite máximo legal do Simples Nacional "
                f"de {formatar_centavos_br(LIMITE_MAXIMO_RBT12_CENTAVOS)} (art. 3º, II da LC 123/2006). "
                "Empresa sujeita a desenquadramento compulsório.",
                ERR_RBT12_LIMITE_ULTRAPASSADO,
            )
        if not isinstance(self.fs12_centavos, int) or self.fs12_centavos < 0:
            raise ErroDominio(
                "A Folha Salarial Acumulada (FS12) deve ser um inteiro não-negativo em centavos.",
                ERR_FS12_INVALIDO,
            )
        if not self.atividades:
            raise ErroDominio("A lista de atividades econômicas não pode ser vazia.", ERR_ATIVIDADES_VAZIAS)

        # Validar unicidade dos códigos
        codigos = [a.codigo for a in self.atividades]
        if len(codigos) != len(set(codigos)):
            raise ErroDominio("Foram detectadas atividades com códigos duplicados.", "CODIGOS_DUPLICADOS")


@dataclass(frozen=True)
class TributoParticionado:
    """Valor e alíquota efetiva apurada para um tributo específico."""
    tributo: Tributo
    percentual_faixa: Fraction
    aliquota_efetiva_tributo: Fraction
    valor_centavos: int


@dataclass(frozen=True)
class ApuracaoAtividadeResultado:
    """Resultado da apuração fiscal para uma atividade específica."""
    codigo: str
    descricao: str
    anexo_base: AnexoSimples
    anexo_aplicado: AnexoSimples
    sujeito_fator_r: bool
    faixa: int
    aliquota_nominal: Fraction
    parcela_deduzir_centavos: int
    aliquota_efetiva: Fraction
    receita_mes_centavos: int
    valor_das_centavos: int
    particao_tributos: List[TributoParticionado]


@dataclass(frozen=True)
class ApuracaoGeralResultado:
    """Resultado consolidado da apuração mensal do Simples Nacional."""
    razao_social: str
    cnpj: str
    competencia_mes_ano: str
    rbt12_centavos: int
    fs12_centavos: int
    fator_r: Fraction
    fator_r_atingido: bool
    receita_total_mes_centavos: int
    total_das_centavos: int
    aliquota_media_efetiva: Fraction
    total_por_tributo: Dict[Tributo, int]
    atividades: List[ApuracaoAtividadeResultado]
