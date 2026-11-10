"""Interface de linha de comando (CLI) para apuração do Simples Nacional.

LOFRANO TECNOLOGIA.
"""

import argparse
from pathlib import Path
import sys
from typing import List, Optional

from .calculator import calcular_apuracao_mensal
from .codecs import (
    apuracao_para_dict,
    carregar_apuracao,
    serializar_json_canonico,
)
from .domain import formatar_centavos_br, formatar_fracao_pct
from .errors import ErroSimplesNacional
from .exports import (
    criar_pacote_zip_deterministico,
    gerar_atividades_csv_str,
    gerar_relatorio_markdown,
    gerar_tributos_csv_str,
)
from .svg_report import gerar_painel_svg

VERSAO = "1.0.0"

EXEMPLO_CANONICO = {
    "razao_social": "Tech & Varejo Soluções Integradas Ltda ME",
    "cnpj": "12.345.678/0001-90",
    "competencia_mes_ano": "11/2026",
    "rbt12_centavos": 85_000_000,
    "fs12_centavos": 25_500_000,
    "atividades": [
        {
            "codigo": "COM-01",
            "descricao": "Comércio Varejista de Equipamentos e Periféricos",
            "anexo_base": "ANEXO_I",
            "sujeito_fator_r": False,
            "receita_mes_centavos": 4_200_000
        },
        {
            "codigo": "DEV-02",
            "descricao": "Desenvolvimento e Manutenção de Softwares Customizados",
            "anexo_base": "ANEXO_V",
            "sujeito_fator_r": True,
            "receita_mes_centavos": 6_800_000
        },
        {
            "codigo": "SUP-03",
            "descricao": "Suporte Técnico e Treinamento Presencial de TI",
            "anexo_base": "ANEXO_III",
            "sujeito_fator_r": False,
            "receita_mes_centavos": 1_500_000
        }
    ]
}


def criar_parser() -> argparse.ArgumentParser:
    """Cria o analisador de argumentos de linha de comando."""
    parser = argparse.ArgumentParser(
        prog="simples-nacional",
        description="Apuração determinística do Simples Nacional (LC 123/2006) — LOFRANO TECNOLOGIA",
    )
    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version=f"apuracao-simples-nacional {VERSAO}",
    )

    subparsers = parser.add_subparsers(dest="subcomando", help="Subcomandos disponíveis")

    # Subcomando 'apurar'
    p_apurar = subparsers.add_parser("apurar", help="Executa a apuração mensal a partir de arquivo JSON")
    p_apurar.add_argument("arquivo", help="Caminho do arquivo JSON de entrada")
    p_apurar.add_argument("--saida", "-s", help="Diretório para salvar relatórios (CSV, JSON, MD, SVG)")
    p_apurar.add_argument("--zip", "-z", help="Caminho para gerar pacote ZIP determinístico consolidado")

    # Subcomando 'exemplo'
    p_exemplo = subparsers.add_parser("exemplo", help="Emite modelo JSON canônico para preenchimento")
    p_exemplo.add_argument("--saida", "-o", help="Caminho do arquivo de saída (padrão: stdout)")

    # Subcomando 'versao'
    subparsers.add_parser("versao", help="Exibe a versão do sistema")

    return parser


def comando_apurar(args: argparse.Namespace) -> int:
    """Executa o comando de apuração fiscal."""
    caminho = Path(args.arquivo)
    if not caminho.exists():
        print(f"Erro: Arquivo não encontrado: '{caminho}'", file=sys.stderr)
        return 1

    try:
        entrada = carregar_apuracao(caminho)
        resultado = calcular_apuracao_mensal(entrada)
    except ErroSimplesNacional as e:
        print(f"Erro de apuração: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Erro inesperado: {e}", file=sys.stderr)
        return 1

    # Exibição resumida no terminal
    fator_badge = "ATINGIDO (>= 28% -> Anexo III)" if resultado.fator_r_atingido else "NÃO ATINGIDO (< 28% -> Anexo V)"

    print(f"Contribuinte: '{resultado.razao_social}' (CNPJ: {resultado.cnpj})")
    print(f"Competência: {resultado.competencia_mes_ano} · Total de atividades econômicas: {len(resultado.atividades)}")
    print()
    print("--- RESULTADO DE APURAÇÃO DO SIMPLES NACIONAL (LC 123/2006) ---")
    print(f"Receita Bruta 12 Meses (RBT12): {formatar_centavos_br(resultado.rbt12_centavos)}")
    print(f"Folha Salarial 12 Meses (FS12):  {formatar_centavos_br(resultado.fs12_centavos)}")
    print(f"Fator R Calculado:              {formatar_fracao_pct(resultado.fator_r)} [{fator_badge}]")
    print(f"Receita Bruta Total do Mês:     {formatar_centavos_br(resultado.receita_total_mes_centavos)}")
    print(f"TOTAL DO DAS A RECOLHER:        {formatar_centavos_br(resultado.total_das_centavos)}")
    print(f"Alíquota Média Efetiva Global:  {formatar_fracao_pct(resultado.aliquota_media_efetiva)}")
    print()
    print("Detalhamento por Atividade:")
    for a in resultado.atividades:
        fator_str = " (Fator R)" if a.sujeito_fator_r else ""
        print(
            f"  - [{a.codigo}] {a.descricao[:36]:<36} | {a.anexo_aplicado.value}{fator_str} Faixa {a.faixa} "
            f"| Rec: {formatar_centavos_br(a.receita_mes_centavos):>14} | Efetiva: {formatar_fracao_pct(a.aliquota_efetiva):>8} "
            f"| DAS: {formatar_centavos_br(a.valor_das_centavos):>14}"
        )
    print()
    print("Partição de Tributos no DAS (Hare-Niemeyer):")
    total_das = resultado.total_das_centavos
    for trib in sorted(resultado.total_por_tributo.keys(), key=lambda t: t.value):
        centavos = resultado.total_por_tributo[trib]
        prop_str = f"{(centavos * 100 / total_das):.2f}%" if total_das > 0 else "0,00%"
        print(f"  - {trib.value:<6}: {formatar_centavos_br(centavos):>14} ({prop_str:>6})")

    # Exportações se solicitadas
    if args.saida:
        dir_saida = Path(args.saida)
        dir_saida.mkdir(parents=True, exist_ok=True)

        dict_apuracao = apuracao_para_dict(resultado)
        json_str = serializar_json_canonico(dict_apuracao)
        (dir_saida / "apuracao_consolidada.json").write_text(json_str, encoding="utf-8")

        csv_ativs = gerar_atividades_csv_str(resultado)
        (dir_saida / "atividades.csv").write_text(csv_ativs, encoding="utf-8")

        csv_tribs = gerar_tributos_csv_str(resultado)
        (dir_saida / "tributos_das.csv").write_text(csv_tribs, encoding="utf-8")

        md_rel = gerar_relatorio_markdown(resultado)
        (dir_saida / "relatorio_fiscal.md").write_text(md_rel, encoding="utf-8")

        svg_painel = gerar_painel_svg(resultado)
        (dir_saida / "painel_executivo.svg").write_text(svg_painel, encoding="utf-8")

        print(f"\nArtefatos fiscais gerados na pasta: {dir_saida.resolve()}")

    if args.zip:
        zip_caminho = Path(args.zip)
        dict_apuracao = apuracao_para_dict(resultado)
        json_bytes = serializar_json_canonico(dict_apuracao).encode("utf-8")
        csv_ativs_bytes = gerar_atividades_csv_str(resultado).encode("utf-8")
        csv_tribs_bytes = gerar_tributos_csv_str(resultado).encode("utf-8")
        md_rel_bytes = gerar_relatorio_markdown(resultado).encode("utf-8")
        svg_painel_bytes = gerar_painel_svg(resultado).encode("utf-8")

        arquivos_zip = [
            ("entrada.json", caminho.read_bytes()),
            ("apuracao_consolidada.json", json_bytes),
            ("atividades.csv", csv_ativs_bytes),
            ("tributos_das.csv", csv_tribs_bytes),
            ("relatorio_fiscal.md", md_rel_bytes),
            ("painel_executivo.svg", svg_painel_bytes),
        ]
        try:
            criar_pacote_zip_deterministico(zip_caminho, arquivos_zip)
            print(f"Pacote ZIP determinístico gerado: {zip_caminho.resolve()}")
        except ErroSimplesNacional as e:
            print(f"Erro ao gerar ZIP: {e}", file=sys.stderr)
            return 1

    return 0


def comando_exemplo(args: argparse.Namespace) -> int:
    """Emite modelo JSON canônico."""
    json_str = serializar_json_canonico(EXEMPLO_CANONICO)
    if args.saida:
        p = Path(args.saida)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json_str, encoding="utf-8")
        print(f"Exemplo canônico gravado em: {p.resolve()}")
    else:
        sys.stdout.write(json_str)
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    """Ponto de entrada da CLI."""
    parser = criar_parser()
    args = parser.parse_args(argv)

    if args.subcomando == "apurar":
        return comando_apurar(args)
    elif args.subcomando == "exemplo":
        return comando_exemplo(args)
    elif args.subcomando == "versao":
        print(f"apuracao-simples-nacional {VERSAO}")
        return 0
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
