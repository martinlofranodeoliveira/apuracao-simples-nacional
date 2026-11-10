"""Testes de exportações (CSV, Markdown, SVG e ZIP) para o Simples Nacional.

LOFRANO TECNOLOGIA.
"""

from pathlib import Path
import tempfile
import unittest
import zipfile

from apuracao_simples_nacional.calculator import calcular_apuracao_mensal
from apuracao_simples_nacional.domain import (
    ApuracaoMensalEntrada,
    ReceitaAtividadeEntrada,
)
from apuracao_simples_nacional.errors import ERR_ARQUIVO_EXISTENTE, ErroCalculo
from apuracao_simples_nacional.exports import (
    criar_pacote_zip_deterministico,
    gerar_atividades_csv_str,
    gerar_relatorio_markdown,
    gerar_tributos_csv_str,
    sanitizar_campo_csv,
)
from apuracao_simples_nacional.svg_report import gerar_painel_svg
from apuracao_simples_nacional.tabelas_lc123 import AnexoSimples


class TestExports(unittest.TestCase):

    def setUp(self) -> None:
        a1 = ReceitaAtividadeEntrada("C1", "Venda de Mercadorias", AnexoSimples.ANEXO_I, 2000000)
        a2 = ReceitaAtividadeEntrada("S1", "Serviços TI", AnexoSimples.ANEXO_V, 3000000, sujeito_fator_r=True)
        self.entrada = ApuracaoMensalEntrada("Empresa Alfa", "12.345.678/0001-90", "11/2026", 50000000, 15000000, [a1, a2])
        self.resultado = calcular_apuracao_mensal(self.entrada)

    def test_sanitizar_csv_formula_injection(self) -> None:
        self.assertEqual(sanitizar_campo_csv("=1+1"), "'=1+1")
        self.assertEqual(sanitizar_campo_csv("+123"), "'+123")
        self.assertEqual(sanitizar_campo_csv("-456"), "'-456")
        self.assertEqual(sanitizar_campo_csv("@cmd"), "'@cmd")
        self.assertEqual(sanitizar_campo_csv("\ttab"), "'\ttab")
        self.assertEqual(sanitizar_campo_csv("\rret"), "'\rret")
        self.assertEqual(sanitizar_campo_csv("Texto Seguro"), "Texto Seguro")

    def test_gerar_atividades_csv_str(self) -> None:
        csv_str = gerar_atividades_csv_str(self.resultado)
        linhas = [l for l in csv_str.split("\n") if l.strip()]
        self.assertGreaterEqual(len(linhas), 3)  # cabeçalho + 2 atividades
        cabecalho = linhas[0].split(";")
        self.assertIn("codigo", cabecalho)
        self.assertIn("aliquota_efetiva", cabecalho)
        self.assertIn("valor_das_reais", cabecalho)

    def test_gerar_tributos_csv_str(self) -> None:
        csv_str = gerar_tributos_csv_str(self.resultado)
        linhas = [l for l in csv_str.split("\n") if l.strip()]
        self.assertGreaterEqual(len(linhas), 5)  # cabeçalho + tributos
        cabecalho = linhas[0].split(";")
        self.assertIn("tributo", cabecalho)
        self.assertIn("valor_centavos", cabecalho)

    def test_gerar_relatorio_markdown(self) -> None:
        md_str = gerar_relatorio_markdown(self.resultado)
        self.assertIn("Empresa Alfa", md_str)
        self.assertIn("12.345.678/0001-90", md_str)
        self.assertIn("Fator R", md_str)
        self.assertIn("Partição dos Tributos no DAS", md_str)

    def test_gerar_painel_svg(self) -> None:
        svg_str = gerar_painel_svg(self.resultado)
        self.assertTrue(svg_str.strip().startswith("<svg"))
        self.assertTrue(svg_str.strip().endswith("</svg>"))
        self.assertIn("viewBox=\"0 0 1440 900\"", svg_str)
        self.assertIn("Empresa Alfa", svg_str)

    def test_criar_pacote_zip_deterministico(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_p = Path(tmpdir) / "teste.zip"
            arquivos = [
                ("dados.txt", b"conteudo de teste"),
                ("pasta/doc.md", b"# Markdown"),
            ]
            criar_pacote_zip_deterministico(zip_p, arquivos)
            self.assertTrue(zip_p.exists())

            # Conferir conteúdo do zip
            with zipfile.ZipFile(zip_p, "r") as zf:
                nomes = zf.namelist()
                self.assertIn("dados.txt", nomes)
                self.assertIn("pasta/doc.md", nomes)
                self.assertEqual(zf.read("dados.txt"), b"conteudo de teste")

    def test_criar_pacote_zip_nao_sobrescreve(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_p = Path(tmpdir) / "teste.zip"
            zip_p.write_bytes(b"existente")
            with self.assertRaises(ErroCalculo) as ctx:
                criar_pacote_zip_deterministico(zip_p, [("a.txt", b"1")])
            self.assertEqual(ctx.exception.codigo, ERR_ARQUIVO_EXISTENTE)
