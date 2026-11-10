"""Exportação de relatórios (CSV, Markdown, ZIP determinístico) para apuração do Simples Nacional.

LOFRANO TECNOLOGIA.
"""

import io
import os
from pathlib import Path
from typing import Any, List, Tuple
import zipfile

from .domain import ApuracaoGeralResultado, formatar_centavos_br, formatar_fracao_pct
from .errors import ERR_ARQUIVO_EXISTENTE, ErroCalculo
from .tabelas_lc123 import Tributo

CARACTERES_PERIGOSOS_CSV = ("=", "+", "-", "@", "\t", "\r")


def sanitizar_campo_csv(valor: Any) -> str:
    """Neutraliza injeção de fórmulas em células CSV adicionando apóstrofo prefixal."""
    texto = str(valor)
    if texto.startswith(CARACTERES_PERIGOSOS_CSV):
        return "'" + texto
    return texto


def gerar_atividades_csv_str(resultado: ApuracaoGeralResultado) -> str:
    """Gera planilha CSV com o detalhamento por atividade econômica e anexo."""
    buf = io.StringIO()
    colunas = [
        "codigo",
        "descricao",
        "anexo_base",
        "anexo_aplicado",
        "sujeito_fator_r",
        "faixa_lc123",
        "aliquota_nominal",
        "parcela_deduzir_reais",
        "aliquota_efetiva",
        "receita_mes_reais",
        "valor_das_reais",
    ]
    buf.write(";".join(colunas) + "\n")

    for ativ in resultado.atividades:
        p_deduzir_reais = f"{ativ.parcela_deduzir_centavos / 100:.2f}".replace(".", ",")
        receita_reais = f"{ativ.receita_mes_centavos / 100:.2f}".replace(".", ",")
        das_reais = f"{ativ.valor_das_centavos / 100:.2f}".replace(".", ",")

        linha = [
            sanitizar_campo_csv(ativ.codigo),
            sanitizar_campo_csv(ativ.descricao),
            sanitizar_campo_csv(ativ.anexo_base.value),
            sanitizar_campo_csv(ativ.anexo_aplicado.value),
            sanitizar_campo_csv("SIM" if ativ.sujeito_fator_r else "NAO"),
            str(ativ.faixa),
            formatar_fracao_pct(ativ.aliquota_nominal),
            p_deduzir_reais,
            formatar_fracao_pct(ativ.aliquota_efetiva),
            receita_reais,
            das_reais,
        ]
        buf.write(";".join(linha) + "\n")

    return buf.getvalue()


def gerar_tributos_csv_str(resultado: ApuracaoGeralResultado) -> str:
    """Gera planilha CSV com a partição consolidada por tributo no DAS."""
    buf = io.StringIO()
    colunas = [
        "tributo",
        "sigla",
        "valor_centavos",
        "valor_reais",
        "proporcao_do_das",
    ]
    buf.write(";".join(colunas) + "\n")

    total_das = resultado.total_das_centavos
    for trib in sorted(resultado.total_por_tributo.keys(), key=lambda t: t.value):
        centavos = resultado.total_por_tributo[trib]
        reais = f"{centavos / 100:.2f}".replace(".", ",")
        prop_str = f"{(centavos * 100 / total_das):.2f}%".replace(".", ",") if total_das > 0 else "0,00%"

        linha = [
            sanitizar_campo_csv(trib.name),
            sanitizar_campo_csv(trib.value),
            str(centavos),
            reais,
            prop_str,
        ]
        buf.write(";".join(linha) + "\n")

    return buf.getvalue()


def gerar_relatorio_markdown(resultado: ApuracaoGeralResultado) -> str:
    """Gera memorial descritivo em Markdown da apuração mensal do Simples Nacional."""
    linhas = [
        f"# Memória de Apuração Fiscal do Simples Nacional — Competência {resultado.competencia_mes_ano}",
        "",
        f"**Contribuinte:** {resultado.razao_social}  ",
        f"**CNPJ:** {resultado.cnpj}  ",
        f"**Regime Tributário:** Simples Nacional (Lei Complementar nº 123/2006)  ",
        f"**Padrão de Apuração:** LOFRANO TECNOLOGIA  ",
        "",
        "---",
        "",
        "## 1. Indicadores Acumulados (Últimos 12 Meses)",
        "",
        f"- **Receita Bruta Total Acumulada (RBT12):** {formatar_centavos_br(resultado.rbt12_centavos)}",
        f"- **Folha Salarial Acumulada (FS12):** {formatar_centavos_br(resultado.fs12_centavos)}",
        f"- **Fator R (FS12 / RBT12):** {formatar_fracao_pct(resultado.fator_r)} (Corte legal: 28,00%)",
        f"- **Enquadramento pelo Fator R:** {'Atingido (Anexo III - Favorável)' if resultado.fator_r_atingido else 'Não Atingido (Anexo V - Alíquota Padrão)'}",
        "",
        "---",
        "",
        "## 2. Resumo da Guia Única (DAS) do Mês",
        "",
        f"- **Receita Bruta Total do Mês:** {formatar_centavos_br(resultado.receita_total_mes_centavos)}",
        f"- **Valor Total do DAS a Recolher:** {formatar_centavos_br(resultado.total_das_centavos)}",
        f"- **Alíquota Média Efetiva:** {formatar_fracao_pct(resultado.aliquota_media_efetiva)}",
        "",
        "### Partição dos Tributos no DAS",
        "",
        "| Tributo | Descrição Legal | Valor Apurado | Proporção no DAS |",
        "|---|---|:---:|:---:|",
    ]

    descricoes_tributos = {
        Tributo.IRPJ: "Imposto sobre a Renda da Pessoa Jurídica",
        Tributo.CSLL: "Contribuição Social sobre o Lucro Líquido",
        Tributo.COFINS: "Contribuição para o Financiamento da Seguridade Social",
        Tributo.PIS: "Programa de Integração Social / PASEP",
        Tributo.CPP: "Contribuição Previdenciária Patronal",
        Tributo.IPI: "Imposto sobre Produtos Industrializados",
        Tributo.ICMS: "Imposto sobre Circulação de Mercadorias e Serviços",
        Tributo.ISS: "Imposto Sobre Serviços de Qualquer Natureza",
    }

    total_das = resultado.total_das_centavos
    for trib in sorted(resultado.total_por_tributo.keys(), key=lambda t: t.value):
        centavos = resultado.total_por_tributo[trib]
        prop_str = f"{(centavos * 100 / total_das):.2f}%".replace(".", ",") if total_das > 0 else "0,00%"
        desc = descricoes_tributos.get(trib, trib.value)
        linhas.append(f"| **{trib.value}** | {desc} | {formatar_centavos_br(centavos)} | {prop_str} |")

    linhas.extend([
        "",
        "---",
        "",
        "## 3. Detalhamento por Atividade Econômica",
        "",
        "| Código | Descrição | Anexo Aplicado | Faixa | Alíquota Nominal | Parcela a Deduzir | Alíquota Efetiva | Receita no Mês | Valor DAS |",
        "|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
    ])

    for a in resultado.atividades:
        fator_info = " (Fator R)" if a.sujeito_fator_r else ""
        linhas.append(
            f"| `{a.codigo}` | {a.descricao} | {a.anexo_aplicado.value}{fator_info} | Faixa {a.faixa} | "
            f"{formatar_fracao_pct(a.aliquota_nominal)} | {formatar_centavos_br(a.parcela_deduzir_centavos)} | "
            f"{formatar_fracao_pct(a.aliquota_efetiva)} | {formatar_centavos_br(a.receita_mes_centavos)} | "
            f"{formatar_centavos_br(a.valor_das_centavos)} |"
        )

    linhas.extend([
        "",
        "---",
        "",
        "> [!NOTE]",
        "> Cálculo executado em conformidade estrita com a Lei Complementar nº 123/2006 e resoluções CGSN.",
        "> Aritmética 100% inteira e racional exata (zero float), com fechamento de centavos via Hare-Niemeyer.",
    ])

    return "\n".join(linhas) + "\n"


def criar_pacote_zip_deterministico(
    caminho_zip: Path,
    arquivos: List[Tuple[str, bytes]],
) -> None:
    """Cria um pacote ZIP determinístico com proteção contra sobreescrita (os.O_EXCL)."""
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY

    try:
        fd = os.open(str(caminho_zip), flags)
    except FileExistsError:
        raise ErroCalculo(f"O arquivo de destino '{caminho_zip}' já existe.", ERR_ARQUIVO_EXISTENTE)

    tempo_fixo = (2026, 11, 10, 0, 0, 0)

    with os.fdopen(fd, "wb") as f_out:
        with zipfile.ZipFile(f_out, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for nome_relativo, dados in sorted(arquivos, key=lambda x: x[0]):
                zinfo = zipfile.ZipInfo(filename=nome_relativo, date_time=tempo_fixo)
                zinfo.external_attr = 0o644 << 16
                zinfo.compress_type = zipfile.ZIP_DEFLATED
                zf.writestr(zinfo, dados)
