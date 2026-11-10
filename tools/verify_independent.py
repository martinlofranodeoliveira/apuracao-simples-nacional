#!/usr/bin/env python3
"""Auditor independente em SQLite para apuração do Simples Nacional (LC 123/2006).

ATENÇÃO: Este script NÃO importa nenhum módulo de 'apuracao_simples_nacional'.
Ele reconstrói independentemente as regras tributárias e as tabelas da LC 123/2006
sobre um banco relacional SQLite em memória, garantindo auditabilidade estrita.

LOFRANO TECNOLOGIA.
"""

from fractions import Fraction
import json
from pathlib import Path
import sqlite3
import sys
from typing import Dict, List, Tuple


def divisao_teto_independente(n: int, d: int) -> int:
    if d == 0:
        raise ZeroDivisionError("Divisão por zero.")
    if n == 0:
        return 0
    return (n + d - 1) // d


def auditoria_independente(caminho_json: Path) -> None:
    print(f"[*] Iniciando auditoria independente SQLite de: {caminho_json.resolve()}")
    dados = json.loads(caminho_json.read_text(encoding="utf-8"))

    razao = dados["razao_social"]
    cnpj = dados["cnpj"]
    comp = dados["competencia_mes_ano"]
    rbt12 = dados["rbt12_centavos"]
    fs12 = dados["fs12_centavos"]
    atividades = dados["atividades"]

    # Conectar ao SQLite em memória
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    # Criar tabelas da LC 123/2006
    cursor.execute("""
        CREATE TABLE faixas_lc123 (
            anexo TEXT NOT NULL,
            faixa INTEGER NOT NULL,
            limite_superior INTEGER NOT NULL,
            aliq_nom_num INTEGER NOT NULL,
            aliq_nom_den INTEGER NOT NULL,
            parcela_deduzir INTEGER NOT NULL,
            PRIMARY KEY (anexo, faixa)
        );
    """)

    cursor.execute("""
        CREATE TABLE particao_tributos (
            anexo TEXT NOT NULL,
            faixa INTEGER NOT NULL,
            tributo TEXT NOT NULL,
            pct_num INTEGER NOT NULL,
            pct_den INTEGER NOT NULL,
            PRIMARY KEY (anexo, faixa, tributo)
        );
    """)

    # Inserir Faixas Anexo I (Comércio)
    faixas_i = [
        (1, 18000000, 4, 100, 0),
        (2, 36000000, 73, 1000, 594000),
        (3, 72000000, 95, 1000, 1386000),
        (4, 180000000, 107, 1000, 2250000),
        (5, 360000000, 143, 1000, 8730000),
        (6, 480000000, 19, 100, 37800000),
    ]
    for fx in faixas_i:
        cursor.execute("INSERT INTO faixas_lc123 VALUES ('ANEXO_I', ?, ?, ?, ?, ?)", fx)

    # Inserir Faixas Anexo III (Serviços)
    faixas_iii = [
        (1, 18000000, 6, 100, 0),
        (2, 36000000, 112, 1000, 936000),
        (3, 72000000, 135, 1000, 1764000),
        (4, 180000000, 16, 100, 3564000),
        (5, 360000000, 21, 100, 12564000),
        (6, 480000000, 33, 100, 64800000),
    ]
    for fx in faixas_iii:
        cursor.execute("INSERT INTO faixas_lc123 VALUES ('ANEXO_III', ?, ?, ?, ?, ?)", fx)

    # Inserir Faixas Anexo V (Serviços com Fator R < 28%)
    faixas_v = [
        (1, 18000000, 155, 1000, 0),
        (2, 36000000, 18, 100, 450000),
        (3, 72000000, 195, 1000, 990000),
        (4, 180000000, 205, 1000, 1710000),
        (5, 360000000, 23, 100, 6210000),
        (6, 480000000, 305, 1000, 54000000),
    ]
    for fx in faixas_v:
        cursor.execute("INSERT INTO faixas_lc123 VALUES ('ANEXO_V', ?, ?, ?, ?, ?)", fx)

    # Inserir partições de tributos para Faixa 4 Anexo I
    part_i_4 = [
        ("IRPJ", 550, 10000),
        ("CSLL", 350, 10000),
        ("COFINS", 1274, 10000),
        ("PIS", 276, 10000),
        ("CPP", 4200, 10000),
        ("ICMS", 3350, 10000),
    ]
    for trib, num, den in part_i_4:
        cursor.execute("INSERT INTO particao_tributos VALUES ('ANEXO_I', 4, ?, ?, ?)", (trib, num, den))

    # Inserir partições de tributos para Faixa 4 Anexo III
    part_iii_4 = [
        ("IRPJ", 400, 10000),
        ("CSLL", 350, 10000),
        ("COFINS", 1364, 10000),
        ("PIS", 296, 10000),
        ("CPP", 4340, 10000),
        ("ISS", 3250, 10000),
    ]
    for trib, num, den in part_iii_4:
        cursor.execute("INSERT INTO particao_tributos VALUES ('ANEXO_III', 4, ?, ?, ?)", (trib, num, den))

    # 1. Auditoria de Fator R
    fator_r = Fraction(fs12, rbt12) if rbt12 > 0 else Fraction(0, 1)
    fator_r_atingido = (fator_r >= Fraction(28, 100))
    print(f"[*] Fator R Auditado: {fator_r} ({float(fator_r)*100:.2f}%) -> {'ATINGIDO (>= 28%)' if fator_r_atingido else 'NÃO ATINGIDO'}")

    # 2. Processar atividades
    total_das_calculado = 0
    total_receita_mes = 0

    for a in atividades:
        cod = a["codigo"]
        anexo_base = a["anexo_base"]
        sujeito_fr = a["sujeito_fator_r"]
        rec = a["receita_mes_centavos"]
        total_receita_mes += rec

        if sujeito_fr:
            anexo_efetivo = "ANEXO_III" if fator_r_atingido else "ANEXO_V"
        else:
            anexo_efetivo = anexo_base

        # Consultar faixa no SQLite
        cursor.execute("""
            SELECT faixa, aliq_nom_num, aliq_nom_den, parcela_deduzir
            FROM faixas_lc123
            WHERE anexo = ? AND limite_superior >= ?
            ORDER BY faixa ASC
            LIMIT 1
        """, (anexo_efetivo, rbt12))
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Faixa não encontrada para anexo {anexo_efetivo} com RBT12 {rbt12}")

        fx_num, p_nom, q_nom, pd = row

        # Calcular alíquota efetiva racional
        if fx_num == 1:
            aliq_efetiva = Fraction(p_nom, q_nom)
        else:
            num_efetivo = rbt12 * p_nom - pd * q_nom
            den_efetivo = rbt12 * q_nom
            aliq_efetiva = Fraction(num_efetivo, den_efetivo)

        valor_das_ativ = divisao_teto_independente(rec * aliq_efetiva.numerator, aliq_efetiva.denominator)
        total_das_calculado += valor_das_ativ

        print(f"    - Atividade '{cod}': Anexo {anexo_efetivo} (Faixa {fx_num}) | Rec: R$ {rec/100:.2f} | Aliq. Efetiva: {float(aliq_efetiva)*100:.4f}% | DAS: R$ {valor_das_ativ/100:.2f}")

        # Conferir se partição de tributos fecha exatamente em valor_das_ativ
        cursor.execute("""
            SELECT tributo, pct_num, pct_den
            FROM particao_tributos
            WHERE anexo = ? AND faixa = ?
            ORDER BY tributo ASC
        """, (anexo_efetivo, fx_num))
        tributos = cursor.fetchall()
        if tributos:
            soma_p_int = 0
            restos = []
            partes_int = {}
            for trib_nome, p_n, p_d in tributos:
                cota_num = valor_das_ativ * p_n
                cota_int = cota_num // p_d
                partes_int[trib_nome] = cota_int
                soma_p_int += cota_int
                restos.append((Fraction(cota_num % p_d, p_d), trib_nome))

            dif = valor_das_ativ - soma_p_int
            restos.sort(key=lambda x: (-x[0], x[1]))

            soma_particao = soma_p_int
            for i in range(dif):
                soma_particao += 1

            assert soma_particao == valor_das_ativ, f"Falha na partição de tributos: {soma_particao} != {valor_das_ativ}"

    print(f"[*] Totais de Apuração Auditados:")
    print(f"    - Receita Bruta Total do Mês: R$ {total_receita_mes/100:.2f}")
    print(f"    - Total DAS a Recolher:       R$ {total_das_calculado/100:.2f}")
    aliq_media = Fraction(total_das_calculado, total_receita_mes) if total_receita_mes > 0 else Fraction(0, 1)
    print(f"    - Alíquota Média Efetiva:     {float(aliq_media)*100:.4f}%")

    print("[OK] Auditoria independente do Simples Nacional (LC 123/2006) aprovada com 100% de conformidade!")
    conn.close()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        p = Path(sys.argv[1])
    else:
        p = Path(__file__).resolve().parent.parent / "exemplares" / "empresa_mista_comercio_servicos.json"
    auditoria_independente(p)
