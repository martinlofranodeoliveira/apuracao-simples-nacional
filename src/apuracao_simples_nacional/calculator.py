"""Motor de cálculo determinístico e exato da apuração do Simples Nacional (LC 123/2006).

Aritmética estritamente racional e inteira, sem uso de ponto flutuante (zero float).
Rateio de tributos pelo método dos maiores restos (Hare-Niemeyer / Hamilton).
LOFRANO TECNOLOGIA.
"""

from fractions import Fraction
from typing import Dict, List, Tuple

from .domain import (
    ApuracaoAtividadeResultado,
    ApuracaoGeralResultado,
    ApuracaoMensalEntrada,
    ReceitaAtividadeEntrada,
    TributoParticionado,
)
from .errors import ERR_DIVISAO_POR_ZERO, ErroCalculo
from .tabelas_lc123 import (
    AnexoSimples,
    FATOR_R_CORTE,
    FaixaAnexo,
    Tributo,
    obter_faixas,
)


def divisao_teto(numerador: int, denominador: int) -> int:
    """Divisão inteira com arredondamento para cima (teto): ceil(n / d)."""
    if denominador == 0:
        raise ErroCalculo("Divisão por zero no cálculo de teto.", ERR_DIVISAO_POR_ZERO)
    if numerador == 0:
        return 0
    return (numerador + denominador - 1) // denominador


def calcular_fator_r(fs12_centavos: int, rbt12_centavos: int) -> Fraction:
    """Calcula a razão racional do Fator R: FS12 / RBT12."""
    if rbt12_centavos == 0:
        if fs12_centavos == 0:
            return Fraction(0, 1)
        # Se folha > 0 e receita 12 = 0, considera proporção máxima
        return Fraction(1, 1)
    return Fraction(fs12_centavos, rbt12_centavos)


def determinar_anexo_aplicado(
    anexo_base: AnexoSimples,
    sujeito_fator_r: bool,
    fator_r: Fraction,
) -> AnexoSimples:
    """Determina o anexo final de tributação considerando o Fator R (art. 18, §§ 5º-J e 5º-M)."""
    if not sujeito_fator_r:
        return anexo_base
    if fator_r >= FATOR_R_CORTE:
        return AnexoSimples.ANEXO_III
    return AnexoSimples.ANEXO_V


def encontrar_faixa(anexo: AnexoSimples, rbt12_centavos: int) -> FaixaAnexo:
    """Identifica a faixa aplicável da LC 123/2006 com base na RBT12."""
    faixas = obter_faixas(anexo)
    if rbt12_centavos == 0:
        return faixas[0]
    for f in faixas:
        if rbt12_centavos <= f.limite_superior_centavos:
            return f
    # Ultrapassou a 6ª faixa (já validado no domínio, mas garantido aqui)
    return faixas[-1]


def calcular_aliquota_efetiva(rbt12_centavos: int, faixa: FaixaAnexo) -> Fraction:
    """Calcula a alíquota efetiva exata segundo a fórmula da LC 123/2006:

    Alíquota Efetiva = ((RBT12 * Alíquota Nominal) - Parcela a Deduzir) / RBT12
    """
    if rbt12_centavos == 0 or faixa.numero == 1:
        return faixa.aliquota_nominal

    p_nom = faixa.aliquota_nominal.numerator
    q_nom = faixa.aliquota_nominal.denominator
    pd = faixa.parcela_deduzir_centavos

    numerador_racional = rbt12_centavos * p_nom - pd * q_nom
    denominador_racional = rbt12_centavos * q_nom

    return Fraction(numerador_racional, denominador_racional)


def particionar_tributos_hare_niemeyer(
    valor_das_centavos: int,
    aliquota_efetiva_anexo: Fraction,
    particao_tributos: Dict[Tributo, Fraction],
) -> List[TributoParticionado]:
    """Particiona o valor do DAS entre os tributos usando o algoritmo dos maiores restos.

    Garante conservação exata de centavos: sum(valor_centavos_i) == valor_das_centavos.
    """
    if valor_das_centavos == 0:
        return [
            TributoParticionado(
                tributo=t,
                percentual_faixa=p,
                aliquota_efetiva_tributo=aliquota_efetiva_anexo * p,
                valor_centavos=0,
            )
            for t, p in particao_tributos.items()
        ]

    # Ordenação canônica estável dos tributos
    tributos_ordenados = list(particao_tributos.items())

    partes_inteiras: Dict[Tributo, int] = {}
    restos_fracionarios: List[Tuple[Fraction, str, Tributo, Fraction]] = []
    soma_partes_inteiras = 0

    for trib, pct in tributos_ordenados:
        num = valor_das_centavos * pct.numerator
        den = pct.denominator
        p_int = num // den
        partes_inteiras[trib] = p_int
        soma_partes_inteiras += p_int
        resto = Fraction(num % den, den)
        # Para ordenação: resto descendente, desempate por nome do tributo
        restos_fracionarios.append((resto, trib.value, trib, pct))

    diferenca_centavos = valor_das_centavos - soma_partes_inteiras

    # Ordenar por resto decrescente; em empate, ordem alfabética do enum
    restos_fracionarios.sort(key=lambda item: (-item[0], item[1]))

    # Distribuir os centavos restantes
    centavos_adicionais: Dict[Tributo, int] = {trib: 0 for trib, _ in tributos_ordenados}
    for i in range(diferenca_centavos):
        trib_ganhador = restos_fracionarios[i][2]
        centavos_adicionais[trib_ganhador] += 1

    resultado: List[TributoParticionado] = []
    for trib, pct in tributos_ordenados:
        val_final = partes_inteiras[trib] + centavos_adicionais[trib]
        aliq_tributo = aliquota_efetiva_anexo * pct
        resultado.append(
            TributoParticionado(
                tributo=trib,
                percentual_faixa=pct,
                aliquota_efetiva_tributo=aliq_tributo,
                valor_centavos=val_final,
            )
        )

    return resultado


def calcular_apuracao_mensal(entrada: ApuracaoMensalEntrada) -> ApuracaoGeralResultado:
    """Executa a apuração mensal completa do Simples Nacional para todas as atividades."""
    fator_r = calcular_fator_r(entrada.fs12_centavos, entrada.rbt12_centavos)
    fator_r_atingido = (fator_r >= FATOR_R_CORTE)

    atividades_resultado: List[ApuracaoAtividadeResultado] = []
    total_das_centavos = 0
    receita_total_mes_centavos = 0
    total_por_tributo: Dict[Tributo, int] = {}

    for ativ in entrada.atividades:
        receita_total_mes_centavos += ativ.receita_mes_centavos

        anexo_aplicado = determinar_anexo_aplicado(
            ativ.anexo_base,
            ativ.sujeito_fator_r,
            fator_r,
        )

        faixa = encontrar_faixa(anexo_aplicado, entrada.rbt12_centavos)
        aliq_efetiva = calcular_aliquota_efetiva(entrada.rbt12_centavos, faixa)

        # Cálculo do valor do DAS para a atividade
        valor_das_ativ = divisao_teto(
            ativ.receita_mes_centavos * aliq_efetiva.numerator,
            aliq_efetiva.denominator,
        )
        total_das_centavos += valor_das_ativ

        # Partição dos tributos
        particao = particionar_tributos_hare_niemeyer(
            valor_das_ativ,
            aliq_efetiva,
            faixa.particao_tributos,
        )

        for item_t in particao:
            total_por_tributo[item_t.tributo] = (
                total_por_tributo.get(item_t.tributo, 0) + item_t.valor_centavos
            )

        atividades_resultado.append(
            ApuracaoAtividadeResultado(
                codigo=ativ.codigo,
                descricao=ativ.descricao,
                anexo_base=ativ.anexo_base,
                anexo_aplicado=anexo_aplicado,
                sujeito_fator_r=ativ.sujeito_fator_r,
                faixa=faixa.numero,
                aliquota_nominal=faixa.aliquota_nominal,
                parcela_deduzir_centavos=faixa.parcela_deduzir_centavos,
                aliquota_efetiva=aliq_efetiva,
                receita_mes_centavos=ativ.receita_mes_centavos,
                valor_das_centavos=valor_das_ativ,
                particao_tributos=particao,
            )
        )

    # Alíquota média efetiva ponderada
    if receita_total_mes_centavos > 0:
        aliq_media_efetiva = Fraction(total_das_centavos, receita_total_mes_centavos)
    else:
        aliq_media_efetiva = Fraction(0, 1)

    return ApuracaoGeralResultado(
        razao_social=entrada.razao_social,
        cnpj=entrada.cnpj,
        competencia_mes_ano=entrada.competencia_mes_ano,
        rbt12_centavos=entrada.rbt12_centavos,
        fs12_centavos=entrada.fs12_centavos,
        fator_r=fator_r,
        fator_r_atingido=fator_r_atingido,
        receita_total_mes_centavos=receita_total_mes_centavos,
        total_das_centavos=total_das_centavos,
        aliquota_media_efetiva=aliq_media_efetiva,
        total_por_tributo=total_por_tributo,
        atividades=atividades_resultado,
    )
