"""Definições de erros e códigos canônicos para apuração do Simples Nacional.

LOFRANO TECNOLOGIA.
"""

ERR_FLOAT_PROIBIDO = "FLOAT_PROIBIDO"
ERR_BOM_PROIBIDO = "BOM_PROIBIDO"
ERR_CHAVE_DUPLICADA = "CHAVE_DUPLICADA"
ERR_PROFUNDIDADE_EXCEDIDA = "PROFUNDIDADE_EXCEDIDA"
ERR_JSON_INVALIDO = "JSON_INVALIDO"
ERR_RBT12_INVALIDO = "RBT12_INVALIDO"
ERR_RBT12_LIMITE_ULTRAPASSADO = "RBT12_LIMITE_ULTRAPASSADO"
ERR_FS12_INVALIDO = "FS12_INVALIDO"
ERR_RECEITA_INVALIDA = "RECEITA_INVALIDA"
ERR_ANEXO_INVALIDO = "ANEXO_INVALIDO"
ERR_ATIVIDADES_VAZIAS = "ATIVIDADES_VAZIAS"
ERR_ARQUIVO_EXISTENTE = "ARQUIVO_EXISTENTE"
ERR_ARQUIVO_NAO_ENCONTRADO = "ARQUIVO_NAO_ENCONTRADO"
ERR_DIVISAO_POR_ZERO = "DIVISAO_POR_ZERO"


class ErroSimplesNacional(Exception):
    """Exceção base do motor de apuração do Simples Nacional."""

    def __init__(self, mensagem: str, codigo: str) -> None:
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.codigo = codigo

    def __str__(self) -> str:
        return f"[{self.codigo}] {self.mensagem}"


class ErroCodec(ErroSimplesNacional):
    """Exceção lançada durante serialização ou desserialização JSON."""
    pass


class ErroDominio(ErroSimplesNacional):
    """Exceção lançada em caso de violação de invariantes de negócio/domínio."""
    pass


class ErroCalculo(ErroSimplesNacional):
    """Exceção lançada em caso de erro matemático no motor de cálculo."""
    pass
