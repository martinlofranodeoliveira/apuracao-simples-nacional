"""Codec JSON canônico e determinístico para apuração do Simples Nacional.

LOFRANO TECNOLOGIA.
"""

from fractions import Fraction
import json
from pathlib import Path
from typing import Any, Dict, List, Union

from .domain import (
    ApuracaoGeralResultado,
    ApuracaoMensalEntrada,
    ReceitaAtividadeEntrada,
    formatar_centavos_br,
    formatar_fracao_pct,
)
from .errors import (
    ERR_ANEXO_INVALIDO,
    ERR_BOM_PROIBIDO,
    ERR_CHAVE_DUPLICADA,
    ERR_FLOAT_PROIBIDO,
    ERR_JSON_INVALIDO,
    ERR_PROFUNDIDADE_EXCEDIDA,
    ErroCodec,
)
from .tabelas_lc123 import AnexoSimples, Tributo

LIMITE_PROFUNDIDADE_MAXIMA = 32


def _verificar_profundidade(obj: Any, nivel: int = 0) -> None:
    if nivel > LIMITE_PROFUNDIDADE_MAXIMA:
        raise ErroCodec(
            f"Profundidade de aninhamento excedeu o limite máximo de {LIMITE_PROFUNDIDADE_MAXIMA}.",
            ERR_PROFUNDIDADE_EXCEDIDA,
        )
    if isinstance(obj, dict):
        for v in obj.values():
            _verificar_profundidade(v, nivel + 1)
    elif isinstance(obj, list):
        for item in obj:
            _verificar_profundidade(item, nivel + 1)


def _verificar_sem_float(obj: Any) -> None:
    if isinstance(obj, float):
        raise ErroCodec("Números em ponto flutuante (float) são terminantemente proibidos.", ERR_FLOAT_PROIBIDO)
    if isinstance(obj, dict):
        for k, v in obj.items():
            _verificar_sem_float(k)
            _verificar_sem_float(v)
    elif isinstance(obj, list):
        for item in obj:
            _verificar_sem_float(item)


def decodificar_json_canonico(conteudo: Union[str, bytes]) -> Any:
    """Decodifica JSON rejeitando BOM, floats, chaves duplicadas e profundidade excessiva."""
    if isinstance(conteudo, bytes):
        if conteudo.startswith(b"\xef\xbb\xbf"):
            raise ErroCodec("Byte Order Mark (BOM) UTF-8 é proibido.", ERR_BOM_PROIBIDO)
        texto = conteudo.decode("utf-8")
    else:
        if conteudo.startswith("\ufeff"):
            raise ErroCodec("Byte Order Mark (BOM) UTF-8 é proibido.", ERR_BOM_PROIBIDO)
        texto = conteudo

    def _rejeitar_float(val: str) -> None:
        raise ErroCodec(f"Valor numérico em ponto flutuante '{val}' é proibido.", ERR_FLOAT_PROIBIDO)

    def _pares_sem_duplicadas(pares: List[tuple]) -> Dict[str, Any]:
        d: Dict[str, Any] = {}
        for k, v in pares:
            if k in d:
                raise ErroCodec(f"Chave duplicada detectada no JSON: '{k}'.", ERR_CHAVE_DUPLICADA)
            d[k] = v
        return d

    try:
        dados = json.loads(
            texto,
            parse_float=_rejeitar_float,
            object_pairs_hook=_pares_sem_duplicadas,
        )
    except json.JSONDecodeError as e:
        raise ErroCodec(f"JSON malformado ou inválido: {e}", ERR_JSON_INVALIDO)

    _verificar_profundidade(dados)
    return dados


def serializar_json_canonico(obj: Any) -> str:
    """Serializa estruturas para JSON canônico determinístico com indentação 2."""
    _verificar_sem_float(obj)

    def _converter(o: Any) -> Any:
        if isinstance(o, Fraction):
            return {"num": o.numerator, "den": o.denominator}
        if isinstance(o, (AnexoSimples, Tributo)):
            return o.value
        if isinstance(o, float):
            raise ErroCodec("Tentativa de serializar float detectada.", ERR_FLOAT_PROIBIDO)
        raise TypeError(f"Objeto do tipo {type(o)} não é serializável.")

    return json.dumps(
        obj,
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
        default=_converter,
    ) + "\n"


def carregar_apuracao(caminho: Union[str, Path]) -> ApuracaoMensalEntrada:
    """Carrega e valida os dados de entrada de apuração a partir de arquivo JSON."""
    caminho_p = Path(caminho)
    if not caminho_p.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    dados = decodificar_json_canonico(caminho_p.read_bytes())
    if not isinstance(dados, dict):
        raise ErroCodec("O nó raiz deve ser um objeto JSON.", ERR_JSON_INVALIDO)

    razao = dados.get("razao_social")
    cnpj = dados.get("cnpj")
    comp = dados.get("competencia_mes_ano")
    rbt12 = dados.get("rbt12_centavos")
    fs12 = dados.get("fs12_centavos")
    ativs_raw = dados.get("atividades")

    if not isinstance(razao, str) or not razao.strip():
        raise ErroCodec("Campo 'razao_social' é obrigatório.", ERR_JSON_INVALIDO)
    if not isinstance(cnpj, str) or not cnpj.strip():
        raise ErroCodec("Campo 'cnpj' é obrigatório.", ERR_JSON_INVALIDO)
    if not isinstance(comp, str) or not comp.strip():
        raise ErroCodec("Campo 'competencia_mes_ano' é obrigatório.", ERR_JSON_INVALIDO)
    if not isinstance(rbt12, int):
        raise ErroCodec("Campo 'rbt12_centavos' deve ser um inteiro em centavos.", ERR_JSON_INVALIDO)
    if not isinstance(fs12, int):
        raise ErroCodec("Campo 'fs12_centavos' deve ser um inteiro em centavos.", ERR_JSON_INVALIDO)
    if not isinstance(ativs_raw, list):
        raise ErroCodec("Campo 'atividades' deve ser uma lista.", ERR_JSON_INVALIDO)

    atividades_lista: List[ReceitaAtividadeEntrada] = []
    for idx, item in enumerate(ativs_raw):
        if not isinstance(item, dict):
            raise ErroCodec(f"Atividade no índice {idx} deve ser um objeto JSON.", ERR_JSON_INVALIDO)

        cod = item.get("codigo")
        desc = item.get("descricao")
        anexo_str = item.get("anexo_base")
        receita = item.get("receita_mes_centavos")
        fator_r_flag = item.get("sujeito_fator_r", False)

        if not isinstance(cod, str) or not cod.strip():
            raise ErroCodec(f"Atividade no índice {idx} possui 'codigo' inválido.", ERR_JSON_INVALIDO)
        if not isinstance(desc, str) or not desc.strip():
            raise ErroCodec(f"Atividade '{cod}' possui 'descricao' inválida.", ERR_JSON_INVALIDO)
        if not isinstance(receita, int):
            raise ErroCodec(f"Atividade '{cod}' possui 'receita_mes_centavos' inválido.", ERR_JSON_INVALIDO)
        if not isinstance(fator_r_flag, bool):
            raise ErroCodec(f"Atividade '{cod}' possui 'sujeito_fator_r' inválido.", ERR_JSON_INVALIDO)

        try:
            anexo_base = AnexoSimples(anexo_str)
        except ValueError:
            raise ErroCodec(f"Anexo Simples inválido na atividade '{cod}': '{anexo_str}'.", ERR_ANEXO_INVALIDO)

        atividades_lista.append(
            ReceitaAtividadeEntrada(
                codigo=cod,
                descricao=desc,
                anexo_base=anexo_base,
                receita_mes_centavos=receita,
                sujeito_fator_r=fator_r_flag,
            )
        )

    return ApuracaoMensalEntrada(
        razao_social=razao,
        cnpj=cnpj,
        competencia_mes_ano=comp,
        rbt12_centavos=rbt12,
        fs12_centavos=fs12,
        atividades=atividades_lista,
    )


def apuracao_para_dict(resultado: ApuracaoGeralResultado) -> Dict[str, Any]:
    """Converte o resultado consolidado da apuração em dicionário canônico determinístico."""
    atividades_json = []
    for ativ in resultado.atividades:
        particao_json = []
        for p in ativ.particao_tributos:
            particao_json.append({
                "tributo": p.tributo.value,
                "percentual_faixa": {
                    "num": p.percentual_faixa.numerator,
                    "den": p.percentual_faixa.denominator,
                    "formatado": formatar_fracao_pct(p.percentual_faixa),
                },
                "aliquota_efetiva_tributo": {
                    "num": p.aliquota_efetiva_tributo.numerator,
                    "den": p.aliquota_efetiva_tributo.denominator,
                    "formatado": formatar_fracao_pct(p.aliquota_efetiva_tributo),
                },
                "valor_centavos": p.valor_centavos,
                "valor_formatado": formatar_centavos_br(p.valor_centavos),
            })

        atividades_json.append({
            "codigo": ativ.codigo,
            "descricao": ativ.descricao,
            "anexo_base": ativ.anexo_base.value,
            "anexo_aplicado": ativ.anexo_aplicado.value,
            "sujeito_fator_r": ativ.sujeito_fator_r,
            "faixa": ativ.faixa,
            "aliquota_nominal": {
                "num": ativ.aliquota_nominal.numerator,
                "den": ativ.aliquota_nominal.denominator,
                "formatado": formatar_fracao_pct(ativ.aliquota_nominal),
            },
            "parcela_deduzir_centavos": ativ.parcela_deduzir_centavos,
            "parcela_deduzir_formatado": formatar_centavos_br(ativ.parcela_deduzir_centavos),
            "aliquota_efetiva": {
                "num": ativ.aliquota_efetiva.numerator,
                "den": ativ.aliquota_efetiva.denominator,
                "formatado": formatar_fracao_pct(ativ.aliquota_efetiva),
            },
            "receita_mes_centavos": ativ.receita_mes_centavos,
            "receita_mes_formatado": formatar_centavos_br(ativ.receita_mes_centavos),
            "valor_das_centavos": ativ.valor_das_centavos,
            "valor_das_formatado": formatar_centavos_br(ativ.valor_das_centavos),
            "particao_tributos": particao_json,
        })

    totais_tributos_json = {}
    for trib in sorted(resultado.total_por_tributo.keys(), key=lambda t: t.value):
        centavos = resultado.total_por_tributo[trib]
        totais_tributos_json[trib.value] = {
            "centavos": centavos,
            "formatado": formatar_centavos_br(centavos),
        }

    return {
        "identificacao": {
            "razao_social": resultado.razao_social,
            "cnpj": resultado.cnpj,
            "competencia_mes_ano": resultado.competencia_mes_ano,
        },
        "indicadores_12_meses": {
            "rbt12_centavos": resultado.rbt12_centavos,
            "rbt12_formatado": formatar_centavos_br(resultado.rbt12_centavos),
            "fs12_centavos": resultado.fs12_centavos,
            "fs12_formatado": formatar_centavos_br(resultado.fs12_centavos),
            "fator_r": {
                "num": resultado.fator_r.numerator,
                "den": resultado.fator_r.denominator,
                "formatado": formatar_fracao_pct(resultado.fator_r),
            },
            "fator_r_atingido": resultado.fator_r_atingido,
        },
        "consolidado_apuracao": {
            "receita_total_mes_centavos": resultado.receita_total_mes_centavos,
            "receita_total_mes_formatado": formatar_centavos_br(resultado.receita_total_mes_centavos),
            "total_das_centavos": resultado.total_das_centavos,
            "total_das_formatado": formatar_centavos_br(resultado.total_das_centavos),
            "aliquota_media_efetiva": {
                "num": resultado.aliquota_media_efetiva.numerator,
                "den": resultado.aliquota_media_efetiva.denominator,
                "formatado": formatar_fracao_pct(resultado.aliquota_media_efetiva),
            },
            "total_por_tributo": totais_tributos_json,
        },
        "atividades": atividades_json,
    }
