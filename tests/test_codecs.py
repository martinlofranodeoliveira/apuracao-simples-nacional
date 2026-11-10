"""Testes do codec JSON canônico para apuração do Simples Nacional.

LOFRANO TECNOLOGIA.
"""

from pathlib import Path
import tempfile
import unittest

from apuracao_simples_nacional.calculator import calcular_apuracao_mensal
from apuracao_simples_nacional.codecs import (
    apuracao_para_dict,
    carregar_apuracao,
    decodificar_json_canonico,
    serializar_json_canonico,
)
from apuracao_simples_nacional.domain import (
    ApuracaoMensalEntrada,
    ReceitaAtividadeEntrada,
)
from apuracao_simples_nacional.errors import (
    ERR_ANEXO_INVALIDO,
    ERR_BOM_PROIBIDO,
    ERR_CHAVE_DUPLICADA,
    ERR_FLOAT_PROIBIDO,
    ERR_JSON_INVALIDO,
    ERR_PROFUNDIDADE_EXCEDIDA,
    ErroCodec,
)
from apuracao_simples_nacional.tabelas_lc123 import AnexoSimples


class TestCodecs(unittest.TestCase):

    def test_rejeitar_bom_bytes(self) -> None:
        com_bom = b"\xef\xbb\xbf{\"chave\": 1}"
        with self.assertRaises(ErroCodec) as ctx:
            decodificar_json_canonico(com_bom)
        self.assertEqual(ctx.exception.codigo, ERR_BOM_PROIBIDO)

    def test_rejeitar_bom_str(self) -> None:
        com_bom = "\ufeff{\"chave\": 1}"
        with self.assertRaises(ErroCodec) as ctx:
            decodificar_json_canonico(com_bom)
        self.assertEqual(ctx.exception.codigo, ERR_BOM_PROIBIDO)

    def test_rejeitar_float_na_leitura(self) -> None:
        json_float = '{"valor": 12.34}'
        with self.assertRaises(ErroCodec) as ctx:
            decodificar_json_canonico(json_float)
        self.assertEqual(ctx.exception.codigo, ERR_FLOAT_PROIBIDO)

    def test_rejeitar_chave_duplicada(self) -> None:
        json_dup = '{"a": 1, "a": 2}'
        with self.assertRaises(ErroCodec) as ctx:
            decodificar_json_canonico(json_dup)
        self.assertEqual(ctx.exception.codigo, ERR_CHAVE_DUPLICADA)

    def test_rejeitar_profundidade_excessiva(self) -> None:
        obj: dict = {}
        curr = obj
        for _ in range(35):
            curr["filho"] = {}
            curr = curr["filho"]
        json_str = serializar_json_canonico(obj)
        with self.assertRaises(ErroCodec) as ctx:
            decodificar_json_canonico(json_str)
        self.assertEqual(ctx.exception.codigo, ERR_PROFUNDIDADE_EXCEDIDA)

    def test_rejeitar_float_na_serializacao(self) -> None:
        with self.assertRaises(ErroCodec) as ctx:
            serializar_json_canonico({"taxa": 3.14})
        self.assertEqual(ctx.exception.codigo, ERR_FLOAT_PROIBIDO)

    def test_serializacao_deterministica(self) -> None:
        d1 = {"b": 2, "a": 1}
        d2 = {"a": 1, "b": 2}
        s1 = serializar_json_canonico(d1)
        s2 = serializar_json_canonico(d2)
        self.assertEqual(s1, s2)
        self.assertTrue(s1.endswith("\n"))

    def test_carregar_apuracao_valida(self) -> None:
        caminho_exemplar = (
            Path(__file__).resolve().parent.parent
            / "exemplares"
            / "empresa_mista_comercio_servicos.json"
        )
        entrada = carregar_apuracao(caminho_exemplar)
        self.assertEqual(entrada.razao_social, "Tech & Varejo Soluções Integradas Ltda ME")
        self.assertEqual(len(entrada.atividades), 3)

    def test_carregar_apuracao_arquivo_inexistente(self) -> None:
        with self.assertRaises(FileNotFoundError):
            carregar_apuracao("/tmp/inexistente_123456.json")

    def test_carregar_apuracao_campos_obrigatorios_ausentes(self) -> None:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            f.write('{"cnpj": "123"}')
            temp_path = f.name
        try:
            with self.assertRaises(ErroCodec) as ctx:
                carregar_apuracao(temp_path)
            self.assertEqual(ctx.exception.codigo, ERR_JSON_INVALIDO)
        finally:
            Path(temp_path).unlink()

    def test_carregar_apuracao_anexo_invalido(self) -> None:
        json_invalido = """{
            "razao_social": "X",
            "cnpj": "123",
            "competencia_mes_ano": "11/2026",
            "rbt12_centavos": 1000,
            "fs12_centavos": 100,
            "atividades": [
                {
                    "codigo": "A1",
                    "descricao": "Desc",
                    "anexo_base": "ANEXO_INEXISTENTE",
                    "sujeito_fator_r": false,
                    "receita_mes_centavos": 500
                }
            ]
        }"""
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            f.write(json_invalido)
            temp_path = f.name
        try:
            with self.assertRaises(ErroCodec) as ctx:
                carregar_apuracao(temp_path)
            self.assertEqual(ctx.exception.codigo, ERR_ANEXO_INVALIDO)
        finally:
            Path(temp_path).unlink()

    def test_apuracao_para_dict_completo(self) -> None:
        a = ReceitaAtividadeEntrada("C1", "Comércio", AnexoSimples.ANEXO_I, 100000)
        e = ApuracaoMensalEntrada("Empresa", "11.222.333/0001-44", "11/2026", 1000000, 300000, [a])
        res = calcular_apuracao_mensal(e)
        d = apuracao_para_dict(res)

        self.assertIn("identificacao", d)
        self.assertIn("indicadores_12_meses", d)
        self.assertIn("consolidado_apuracao", d)
        self.assertIn("atividades", d)
        self.assertEqual(d["identificacao"]["razao_social"], "Empresa")
