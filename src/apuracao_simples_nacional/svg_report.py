"""Geração de painel executivo e analítico em SVG (1440x900) para apuração do Simples Nacional.

LOFRANO TECNOLOGIA.
"""

from typing import Dict
from .domain import ApuracaoGeralResultado, formatar_centavos_br, formatar_fracao_pct
from .tabelas_lc123 import Tributo


def gerar_painel_svg(res: ApuracaoGeralResultado) -> str:
    """Gera o código XML/SVG do painel executivo em 1440x900."""
    total_das = res.total_das_centavos
    rbt12_fmt = formatar_centavos_br(res.rbt12_centavos)
    fs12_fmt = formatar_centavos_br(res.fs12_centavos)
    fator_r_fmt = formatar_fracao_pct(res.fator_r)
    rec_mes_fmt = formatar_centavos_br(res.receita_total_mes_centavos)
    total_das_fmt = formatar_centavos_br(total_das)
    aliq_media_fmt = formatar_fracao_pct(res.aliquota_media_efetiva)

    fator_r_badge = "ATINGIDO (>= 28%)" if res.fator_r_atingido else "NÃO ATINGIDO (< 28%)"
    fator_r_cor = "#10b981" if res.fator_r_atingido else "#f59e0b"

    # Cores dos tributos
    cores_tributos = {
        Tributo.IRPJ: "#3b82f6",
        Tributo.CSLL: "#6366f1",
        Tributo.COFINS: "#8b5cf6",
        Tributo.PIS: "#ec4899",
        Tributo.CPP: "#f59e0b",
        Tributo.IPI: "#ef4444",
        Tributo.ICMS: "#10b981",
        Tributo.ISS: "#06b6d4",
    }

    # Renderizar barras de tributos
    barras_tributos_svg = []
    y_trib = 360
    tributos_ordenados = sorted(res.total_por_tributo.keys(), key=lambda t: -res.total_por_tributo[t])
    for trib in tributos_ordenados:
        val = res.total_por_tributo[trib]
        pct = (val * 100 // total_das) if total_das > 0 else 0
        prop_str = f"{(val * 100 / total_das):.2f}%".replace(".", ",") if total_das > 0 else "0,00%"
        largura_max = 500
        largura_barra = max(6, int((val * largura_max) / total_das)) if total_das > 0 else 0
        cor = cores_tributos.get(trib, "#94a3b8")

        barras_tributos_svg.append(f"""
        <g transform="translate(60, {y_trib})">
            <text x="0" y="16" fill="#f8fafc" font-size="14" font-weight="600" font-family="system-ui, -apple-system, sans-serif">{trib.value}</text>
            <rect x="70" y="2" width="{largura_barra}" height="18" rx="4" fill="{cor}" />
            <text x="{70 + largura_barra + 12}" y="16" fill="#cbd5e1" font-size="13" font-family="system-ui, -apple-system, sans-serif">{formatar_centavos_br(val)} ({prop_str})</text>
        </g>
        """)
        y_trib += 38

    # Renderizar tabela de atividades
    linhas_tabela_svg = []
    y_tab = 360
    for ativ in res.atividades[:6]:
        linhas_tabela_svg.append(f"""
        <g transform="translate(720, {y_tab})">
            <rect x="0" y="0" width="660" height="48" rx="6" fill="#1e293b" stroke="#334155" stroke-width="1" />
            <text x="16" y="20" fill="#38bdf8" font-size="13" font-weight="700" font-family="system-ui, -apple-system, sans-serif">[{ativ.codigo}] {ativ.descricao[:32]}</text>
            <text x="16" y="38" fill="#94a3b8" font-size="12" font-family="system-ui, -apple-system, sans-serif">{ativ.anexo_aplicado.value} · Faixa {ativ.faixa} (Aliq. Nominal: {formatar_fracao_pct(ativ.aliquota_nominal)})</text>
            
            <text x="440" y="20" fill="#cbd5e1" font-size="12" text-anchor="end" font-family="system-ui, -apple-system, sans-serif">Receita: {formatar_centavos_br(ativ.receita_mes_centavos)}</text>
            <text x="440" y="38" fill="#10b981" font-size="12" font-weight="600" text-anchor="end" font-family="system-ui, -apple-system, sans-serif">Efetiva: {formatar_fracao_pct(ativ.aliquota_efetiva)}</text>
            
            <rect x="460" y="10" width="184" height="28" rx="4" fill="#0f172a" />
            <text x="552" y="29" fill="#f8fafc" font-size="13" font-weight="700" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif">DAS: {formatar_centavos_br(ativ.valor_das_centavos)}</text>
        </g>
        """)
        y_tab += 56

    bloco_barras = "\n".join(barras_tributos_svg)
    bloco_tabela = "\n".join(linhas_tabela_svg)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 900" width="1440" height="900">
    <defs>
        <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#0b0f19" />
            <stop offset="100%" stop-color="#111827" />
        </linearGradient>
        <linearGradient id="cardGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#1e293b" />
            <stop offset="100%" stop-color="#0f172a" />
        </linearGradient>
        <linearGradient id="destaqueGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#059669" />
            <stop offset="100%" stop-color="#047857" />
        </linearGradient>
    </defs>

    <!-- Fundo Principal -->
    <rect width="1440" height="900" fill="url(#bg)" />

    <!-- Cabeçalho -->
    <g transform="translate(60, 50)">
        <rect x="0" y="0" width="1320" height="90" rx="12" fill="#1e293b" stroke="#334155" stroke-width="1" />
        <circle cx="45" cy="45" r="24" fill="#3b82f6" opacity="0.2" />
        <text x="45" y="52" fill="#60a5fa" font-size="22" font-weight="900" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif">SN</text>
        
        <text x="85" y="38" fill="#f8fafc" font-size="22" font-weight="800" font-family="system-ui, -apple-system, sans-serif">Apuração Fiscal do Simples Nacional (LC 123/2006)</text>
        <text x="85" y="65" fill="#94a3b8" font-size="14" font-family="system-ui, -apple-system, sans-serif">Contribuinte: <tspan fill="#f1f5f9" font-weight="600">{res.razao_social}</tspan> · CNPJ: <tspan fill="#f1f5f9">{res.cnpj}</tspan> · Competência: <tspan fill="#38bdf8" font-weight="700">{res.competencia_mes_ano}</tspan></text>
        
        <rect x="1100" y="25" width="190" height="40" rx="8" fill="#0f172a" stroke="#475569" stroke-width="1" />
        <text x="1195" y="50" fill="#38bdf8" font-size="13" font-weight="700" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif">LOFRANO TECNOLOGIA</text>
    </g>

    <!-- Cards Executivos de Resumo -->
    <g transform="translate(60, 165)">
        <!-- Card 1: RBT12 -->
        <rect x="0" y="0" width="310" height="120" rx="10" fill="url(#cardGrad)" stroke="#334155" stroke-width="1" />
        <text x="24" y="34" fill="#94a3b8" font-size="13" font-weight="600" font-family="system-ui, -apple-system, sans-serif">RECEITA BRUTA 12 MESES (RBT12)</text>
        <text x="24" y="74" fill="#f8fafc" font-size="24" font-weight="800" font-family="system-ui, -apple-system, sans-serif">{rbt12_fmt}</text>
        <text x="24" y="100" fill="#64748b" font-size="12" font-family="system-ui, -apple-system, sans-serif">Limite Anual: R$ 4.800.000,00</text>

        <!-- Card 2: FS12 & Fator R -->
        <rect x="335" y="0" width="310" height="120" rx="10" fill="url(#cardGrad)" stroke="#334155" stroke-width="1" />
        <text x="359" y="34" fill="#94a3b8" font-size="13" font-weight="600" font-family="system-ui, -apple-system, sans-serif">FOLHA 12M / FATOR R</text>
        <text x="359" y="74" fill="#f8fafc" font-size="24" font-weight="800" font-family="system-ui, -apple-system, sans-serif">{fator_r_fmt}</text>
        <text x="359" y="100" fill="{fator_r_cor}" font-size="12" font-weight="700" font-family="system-ui, -apple-system, sans-serif">{fator_r_badge} · FS12: {fs12_fmt}</text>

        <!-- Card 3: Receita no Mês -->
        <rect x="670" y="0" width="310" height="120" rx="10" fill="url(#cardGrad)" stroke="#334155" stroke-width="1" />
        <text x="694" y="34" fill="#94a3b8" font-size="13" font-weight="600" font-family="system-ui, -apple-system, sans-serif">RECEITA BRUTA DO MÊS</text>
        <text x="694" y="74" fill="#38bdf8" font-size="24" font-weight="800" font-family="system-ui, -apple-system, sans-serif">{rec_mes_fmt}</text>
        <text x="694" y="100" fill="#64748b" font-size="12" font-family="system-ui, -apple-system, sans-serif">Base de incidência do Simples</text>

        <!-- Card 4: Total do DAS -->
        <rect x="1005" y="0" width="315" height="120" rx="10" fill="url(#destaqueGrad)" stroke="#10b981" stroke-width="1" />
        <text x="1029" y="34" fill="#a7f3d0" font-size="13" font-weight="700" font-family="system-ui, -apple-system, sans-serif">TOTAL DAS A RECOLHER</text>
        <text x="1029" y="74" fill="#ffffff" font-size="26" font-weight="900" font-family="system-ui, -apple-system, sans-serif">{total_das_fmt}</text>
        <text x="1029" y="100" fill="#d1fae5" font-size="13" font-weight="700" font-family="system-ui, -apple-system, sans-serif">Alíquota Média Efetiva: {aliq_media_fmt}</text>
    </g>

    <!-- Títulos das Seções Centrais -->
    <text x="60" y="330" fill="#f8fafc" font-size="18" font-weight="700" font-family="system-ui, -apple-system, sans-serif">Partição de Tributos no DAS (Hare-Niemeyer)</text>
    <text x="720" y="330" fill="#f8fafc" font-size="18" font-weight="700" font-family="system-ui, -apple-system, sans-serif">Detalhamento por Atividade e Enquadramento</text>

    <!-- Seção Esquerda: Barras de Tributos -->
    <rect x="60" y="345" width="630" height="465" rx="10" fill="#131d2e" stroke="#1e293b" stroke-width="1" />
    {bloco_barras}

    <!-- Seção Direita: Tabela de Atividades -->
    <rect x="710" y="345" width="670" height="465" rx="10" fill="#131d2e" stroke="#1e293b" stroke-width="1" />
    {bloco_tabela}

    <!-- Rodapé com Garantias de Engenharia -->
    <g transform="translate(60, 835)">
        <rect x="0" y="0" width="1320" height="45" rx="8" fill="#0f172a" stroke="#1e293b" stroke-width="1" />
        <text x="24" y="28" fill="#64748b" font-size="13" font-family="system-ui, -apple-system, sans-serif">Padrão de Engenharia LOFRANO TECNOLOGIA</text>
        <text x="420" y="28" fill="#10b981" font-size="13" font-weight="600" font-family="system-ui, -apple-system, sans-serif">✓ Zero Float (Inteiros e Frações Racionais)</text>
        <text x="780" y="28" fill="#38bdf8" font-size="13" font-weight="600" font-family="system-ui, -apple-system, sans-serif">✓ Fechamento Exato de Centavos (Hare-Niemeyer)</text>
        <text x="1170" y="28" fill="#a855f7" font-size="13" font-weight="600" font-family="system-ui, -apple-system, sans-serif">✓ Auditável via SQLite</text>
    </g>
</svg>
"""
