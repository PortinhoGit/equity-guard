"""
data/tickers_b3.py
Lista estática dos tickers mais negociados da B3 (ações, FIIs, ETFs, BDRs).
Atualizada em abril/2026.
"""

ACOES = [
    "ABEV3", "ALOS3", "ALPA4", "AMER3", "ASAI3", "AZUL4",
    "B3SA3", "BBAS3", "BBDC3", "BBDC4", "BBSE3", "BEEF3",
    "BPAC11", "BRAP4", "BRFS3", "BRKM5",
    "CASH3", "CCRO3", "CIEL3", "CMIG4", "CMIN3", "COGN3",
    "CPFE3", "CPLE6", "CRFB3", "CSAN3", "CSNA3", "CVCB3",
    "CYRE3",
    "DXCO3",
    "ECOR3", "EGIE3", "ELET3", "ELET6", "EMBR3", "ENEV3",
    "ENGI11", "EQTL3", "EZTC3",
    "FLRY3",
    "GGBR4", "GOAU4", "GOLL4", "GRND3",
    "HAPV3", "HYPE3",
    "IGTI11", "IRBR3", "ITSA4", "ITUB4",
    "JBSS3", "JHSF3",
    "KLBN11",
    "LREN3", "LWSA3",
    "MGLU3", "MRFG3", "MRVE3", "MULT3",
    "NTCO3",
    "PCAR3", "PETR3", "PETR4", "PETZ3", "POSI3", "PRIO3",
    "QUAL3",
    "RADL3", "RAIL3", "RAIZ4", "RDOR3", "RENT3", "RRRP3",
    "SANB11", "SBSP3", "SLCE3", "SMTO3", "SOMA3", "SUZB3",
    "TAEE11", "TIMS3", "TOTS3", "TRPL4", "TUPY3",
    "UGPA3", "USIM5",
    "VALE3", "VBBR3", "VIVT3", "VULC3",
    "WEGE3",
    "YDUQ3",
]

FIIS = [
    "BCFF11", "BRCR11", "BTLG11",
    "CPTS11",
    "HGLG11", "HSML11", "HGBS11", "HGRE11",
    "IRDM11",
    "KNCR11", "KNIP11", "KNRI11",
    "MXRF11", "MCCI11",
    "PVBI11",
    "RBRF11", "RBRR11", "RECR11", "RVBI11",
    "TGAR11", "TRXF11",
    "VISC11", "VGIR11", "VILG11", "VINO11",
    "XPML11", "XPLG11", "XPCI11",
]

ETFS = [
    "BOVA11", "BOVV11", "DIVO11", "HASH11", "IMAB11",
    "IVVB11", "MATB11", "NASD11", "SMAL11", "SPXI11",
]

BDRS = [
    "AAPL34", "AMZO34", "DISB34", "GOGL34", "META34",
    "MSFT34", "NFLX34", "NVDC34", "TSLA34",
]

ALL_TICKERS_B3 = sorted(set(ACOES + FIIS + ETFS + BDRS))
