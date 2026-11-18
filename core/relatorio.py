"""Tabelas finais e exportação (HTML para imprimir em PDF e planilha XLSX)."""
from __future__ import annotations

import html
import io
from datetime import date

import pandas as pd

from .formatar import br
from .nutricao import Animal, Exigencias, avaliar, checklist, composicao, tabela_ingredientes

CASAS = {
    "kg MN/vaca/dia": 3, "kg MS/vaca/dia": 3, "% da MS": 2, "kg MN lote/dia": 1, "Custo R$/vaca/dia": 2,
    "Exigido (kg)": 3, "Fornecido (kg)": 3, "Diferença (kg)": 3, "Exigido (% MS)": 2,
    "Fornecido (% MS)": 2, "% atendido": 1, "Limite (kg)": 3, "Obtido (kg)": 3, "Limite (% MS)": 2,
    "Obtido (% MS)": 2, "Valor marginal (R$/kg)": 2,
}

STATUS_TXT = {"ok": "Atende", "excesso": "Atende (excesso)", "perto": "Quase", "fora": "Não atende"}


def df_ingredientes(racao, alimentos, n_vacas) -> pd.DataFrame:
    df = pd.DataFrame(tabela_ingredientes(racao, alimentos, n_vacas))
    if df.empty:
        return df
    total = {"Ingrediente": "TOTAL", "Categoria": ""}
    for c in ["kg MN/vaca/dia", "kg MS/vaca/dia", "% da MS", "kg MN lote/dia", "Custo R$/vaca/dia"]:
        total[c] = df[c].sum()
    return pd.concat([df, pd.DataFrame([total])], ignore_index=True)


def df_nutrientes(racao, alimentos, animal, exig, incluir_amido) -> pd.DataFrame:
    df = pd.DataFrame(avaliar(racao, alimentos, animal, exig, incluir_amido))
    if not df.empty:
        df["Status"] = df["Status"].map(STATUS_TXT)
    return df


def df_checklist(racao, alimentos, animal, exig, aditivos, incluir_amido) -> pd.DataFrame:
    df = pd.DataFrame(checklist(racao, alimentos, animal, exig, aditivos, incluir_amido))
    if not df.empty:
        df["OK"] = df["OK"].map({True: "✔", False: "✘"})
    return df


def df_animal(animal: Animal, exig: Exigencias) -> pd.DataFrame:
    ims = animal.ims_kg
    linhas = [
        ("Número de vacas", animal.n_vacas, ""), ("Dias em lactação", animal.dias_lactacao, "dias"),
        ("Peso corporal médio", animal.peso, "kg"), ("IMS", animal.ims_pct_pc, "% PC"),
        ("IMS", round(ims, 3), "kg MS/vaca/dia"), ("Produção de leite", animal.leite, "kg/dia"),
        ("Gordura no leite", animal.gordura, "%"), ("Proteína no leite", animal.proteina, "%"),
        ("PB exigida", exig.pb_kg, f"kg/dia ({br(100 * exig.pb_kg / ims)}% MS)"),
        ("NDT exigido", exig.ndt_kg, f"kg/dia ({br(100 * exig.ndt_kg / ims)}% MS)"),
        ("Cálcio", exig.ca_pct, f"% MS ({br(exig.ca_pct / 100 * ims, 3)} kg)"),
        ("Fósforo", exig.p_pct, f"% MS ({br(exig.p_pct / 100 * ims, 3)} kg)"),
        ("FDN mínimo", exig.fdn_min_pct, "% MS"), ("EE máximo", exig.ee_max_pct, "% MS"),
        ("Amido máximo (ração 3)", exig.amido_max_pct, "% MS"),
    ]
    linhas = [(i, str(v) if isinstance(v, int) else br(v, 3 if abs(v) < 1 else 2), u) for i, v, u in linhas]
    return pd.DataFrame(linhas, columns=["Item", "Valor", "Unidade"])


def montar_relatorio(projeto_racoes: dict, alimentos: dict, animal: Animal, exig: Exigencias,
                     aditivos: dict) -> dict:
    """projeto_racoes = {título: (racao_com_aditivos, incluir_amido)} → tabelas por ração."""
    saida = {}
    for titulo, (racao, amido) in projeto_racoes.items():
        if not racao:
            continue
        saida[titulo] = {
            "ingredientes": df_ingredientes(racao, alimentos, animal.n_vacas),
            "nutrientes": df_nutrientes(racao, alimentos, animal, exig, amido),
            "checklist": df_checklist(racao, alimentos, animal, exig, aditivos, amido),
            "custo": composicao(racao, alimentos)["custo"],
        }
    return saida


# ---------------------------------------------------------------- exportação

def _fmt_df(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for c in out.columns:
        if pd.api.types.is_float_dtype(out[c]):
            casas = CASAS.get(c, 2)
            out[c] = out[c].map(lambda v, k=casas: "" if pd.isna(v) else br(v, k))
    return out


def tabela_html(df: pd.DataFrame) -> str:
    if df is None or df.empty:
        return "<p><em>Sem dados.</em></p>"
    return _fmt_df(df).to_html(index=False, escape=True, border=0, classes="t")


CSS = """
body{font-family:Segoe UI,Arial,sans-serif;color:#1d2a22;margin:24px;font-size:12px}
h1{font-size:20px;margin:0 0 4px} h2{font-size:16px;margin:24px 0 6px;border-bottom:2px solid #2e7d4f;padding-bottom:3px}
h3{font-size:13px;margin:14px 0 4px} .sub{color:#5a6b60;margin-bottom:12px}
table.t{border-collapse:collapse;width:100%;margin:4px 0 10px}
table.t th{background:#e8f2ec;text-align:left;padding:4px 6px;border:1px solid #c9dccf}
table.t td{padding:3px 6px;border:1px solid #dde7e0} table.t tr:last-child td{font-weight:600}
.just{margin:4px 0 10px;padding:6px 8px;background:#f6f8f6;border-left:3px solid #2e7d4f}
.alerta{color:#8a5a00} @media print{body{margin:10mm} h2{page-break-after:avoid} table{page-break-inside:avoid}}
"""


def gerar_html(titulo: str, animal: Animal, exig: Exigencias, racoes: dict, aditivos: dict,
               silo: dict | None, pl: dict | None, historico: pd.DataFrame | None = None) -> str:
    e = html.escape
    partes = [f"<!doctype html><html lang='pt-BR'><head><meta charset='utf-8'><title>{e(titulo)}</title>"
              f"<style>{CSS}</style></head><body>",
              f"<h1>{e(titulo)}</h1><div class='sub'>Gerado em {date.today():%d/%m/%Y}</div>",
              "<h2>Dados dos animais e exigências</h2>", tabela_html(df_animal(animal, exig))]
    for nome, tabs in racoes.items():
        partes.append(f"<h2>{e(nome)}</h2>")
        partes.append("<h3>Fórmula (por vaca/dia e para o lote)</h3>" + tabela_html(tabs["ingredientes"]))
        partes.append("<h3>Nutrientes: exigido × fornecido</h3>" + tabela_html(tabs["nutrientes"]))
        partes.append("<h3>Checklist do trabalho</h3>" + tabela_html(tabs["checklist"]))
        if nome.startswith("Ração 1") and historico is not None and not historico.empty:
            partes.append("<h3>Histórico de tentativas</h3>" + tabela_html(historico))
        if nome.startswith("Ração 3") and pl:
            partes.append(f"<h3>Relatório da otimização</h3><p>{e(pl.get('mensagem', ''))} "
                          f"Custo: R$ {br(pl.get('custo_vaca', 0))}/vaca/dia · "
                          f"R$ {br(pl.get('custo_lote', 0))}/dia para o lote.</p>")
            partes.append(tabela_html(pd.DataFrame(pl.get("restricoes", []))))
            partes.append(tabela_html(pd.DataFrame(pl.get("alimentos", []))))
    partes.append("<h2>Aditivos e justificativas</h2>")
    for nome, info in aditivos.items():
        partes.append(f"<h3>{e(nome)} — {br(info.get('dose_kg', 0) * 1000, 1)} g/vaca/dia</h3>"
                      f"<div class='just'>{e(info.get('justificativa', ''))}</div>")
    if silo:
        partes.append("<h2>Silagem de milho: silo, fatia diária e área</h2>")
        partes.append(tabela_html(pd.DataFrame(silo["passos"], columns=["Etapa", "Cálculo", "Resultado"])))
        for a in silo.get("alertas", []):
            partes.append(f"<p class='alerta'>⚠ {e(a)}</p>")
    partes.append("</body></html>")
    return "\n".join(partes)


def gerar_xlsx(planilhas: dict[str, pd.DataFrame]) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        usados = set()
        for nome, df in planilhas.items():
            if df is None or df.empty:
                continue
            aba = "".join(ch for ch in nome if ch not in "[]:*?/\\")[:31]
            base, i = aba, 2
            while aba in usados:
                aba = f"{base[:28]}_{i}"
                i += 1
            usados.add(aba)
            df.to_excel(w, sheet_name=aba, index=False)
            ws = w.sheets[aba]
            for col in ws.columns:
                largura = max(len(str(c.value or "")) for c in col)
                ws.column_dimensions[col[0].column_letter].width = min(60, max(10, largura + 2))
    return buf.getvalue()
