"""Testes da interface de linha de comando (CLI) do Simples Nacional.

LOFRANO TECNOLOGIA.
"""

import io
from pathlib import Path
import sys
import tempfile
import unittest

from apuracao_simples_nacional.cli import VERSAO, main


class TestCLI(unittest.TestCase):

    def setUp(self) -> None:
        self.exemplar = (
            Path(__file__).resolve().parent.parent
            / "exemplares"
            / "empresa_mista_comercio_servicos.json"
        )

    def test_cli_ajuda(self) -> None:
        stdout_buf = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = stdout_buf
        try:
            with self.assertRaises(SystemExit) as ctx:
                main(["--help"])
            self.assertEqual(ctx.exception.code, 0)
        finally:
            sys.stdout = old_stdout
        self.assertIn("simples-nacional", stdout_buf.getvalue())

    def test_cli_versao_subcomando(self) -> None:
        stdout_buf = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = stdout_buf
        try:
            cod = main(["versao"])
            self.assertEqual(cod, 0)
        finally:
            sys.stdout = old_stdout
        self.assertIn(VERSAO, stdout_buf.getvalue())

    def test_cli_versao_flag(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            main(["--version"])
        self.assertEqual(ctx.exception.code, 0)

    def test_cli_exemplo_stdout(self) -> None:
        stdout_buf = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = stdout_buf
        try:
            cod = main(["exemplo"])
            self.assertEqual(cod, 0)
        finally:
            sys.stdout = old_stdout
        saida = stdout_buf.getvalue()
        self.assertIn("razao_social", saida)
        self.assertIn("rbt12_centavos", saida)

    def test_cli_exemplo_arquivo(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            alvo = Path(tmpdir) / "modelo.json"
            cod = main(["exemplo", "--saida", str(alvo)])
            self.assertEqual(cod, 0)
            self.assertTrue(alvo.exists())
            conteudo = alvo.read_text(encoding="utf-8")
            self.assertIn("razao_social", conteudo)

    def test_cli_apurar_stdout(self) -> None:
        stdout_buf = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = stdout_buf
        try:
            cod = main(["apurar", str(self.exemplar)])
            self.assertEqual(cod, 0)
        finally:
            sys.stdout = old_stdout
        saida = stdout_buf.getvalue()
        self.assertIn("TOTAL DO DAS A RECOLHER", saida)
        self.assertIn("R$ 13.182,10", saida)
        self.assertIn("Fator R", saida)

    def test_cli_apurar_arquivo_inexistente(self) -> None:
        stderr_buf = io.StringIO()
        old_stderr = sys.stderr
        sys.stderr = stderr_buf
        try:
            cod = main(["apurar", "/tmp/inexistente_9999.json"])
            self.assertEqual(cod, 1)
        finally:
            sys.stderr = old_stderr
        self.assertIn("não encontrado", stderr_buf.getvalue())

    def test_cli_apurar_com_saida_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            pasta_saida = Path(tmpdir) / "relatorios_fiscais"
            cod = main(["apurar", str(self.exemplar), "--saida", str(pasta_saida)])
            self.assertEqual(cod, 0)
            self.assertTrue((pasta_saida / "apuracao_consolidada.json").exists())
            self.assertTrue((pasta_saida / "atividades.csv").exists())
            self.assertTrue((pasta_saida / "tributos_das.csv").exists())
            self.assertTrue((pasta_saida / "relatorio_fiscal.md").exists())
            self.assertTrue((pasta_saida / "painel_executivo.svg").exists())

    def test_cli_apurar_com_zip(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_alvo = Path(tmpdir) / "pacote.zip"
            cod = main(["apurar", str(self.exemplar), "--zip", str(zip_alvo)])
            self.assertEqual(cod, 0)
            self.assertTrue(zip_alvo.exists())
