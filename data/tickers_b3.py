"""
data/tickers_b3.py
Lista estática dos tickers mais negociados da B3 (ações, FIIs, ETFs, BDRs).
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


# Nome popular/comercial por ticker — usado nos paineis de mercado para
# que o usuario reconheca rapidamente a empresa (ex: PETR4 -> "Petrobras").
POPULAR_NAMES: dict = {
    # Grandes bancos
    "BBAS3": "Banco do Brasil", "BBDC3": "Bradesco", "BBDC4": "Bradesco",
    "ITUB4": "Itaú", "ITSA4": "Itaúsa", "SANB11": "Santander",
    "BPAC11": "BTG Pactual", "BBSE3": "BB Seguridade",
    # Petroleo/Energia
    "PETR3": "Petrobras", "PETR4": "Petrobras",
    "PRIO3": "PRIO", "RRRP3": "3R Petroleum", "RAIZ4": "Raízen",
    "UGPA3": "Ultrapar", "VBBR3": "Vibra", "CSAN3": "Cosan",
    # Eletricas
    "ELET3": "Eletrobras", "ELET6": "Eletrobras", "CMIG4": "Cemig",
    "CPFE3": "CPFL", "CPLE6": "Copel", "EGIE3": "Engie", "EQTL3": "Equatorial",
    "ENEV3": "Eneva", "ENGI11": "Energisa", "TAEE11": "Taesa", "TRPL4": "ISA CTEEP",
    # Mineracao/Siderurgia
    "VALE3": "Vale", "CSNA3": "CSN", "CMIN3": "CSN Mineração",
    "GGBR4": "Gerdau", "GOAU4": "Gerdau Metalúrgica",
    "USIM5": "Usiminas", "BRAP4": "Bradespar",
    # Papel/Celulose
    "SUZB3": "Suzano", "KLBN11": "Klabin", "DXCO3": "Dexco",
    # Varejo
    "LREN3": "Lojas Renner", "MGLU3": "Magalu", "AMER3": "Americanas",
    "SOMA3": "Grupo Soma", "PETZ3": "Petz", "CVCB3": "CVC",
    "ALPA4": "Alpargatas", "GRND3": "Grendene", "VULC3": "Vulcabras",
    "CASH3": "Méliuz", "LWSA3": "Locaweb",
    # Supermercados
    "PCAR3": "Pão de Açúcar", "CRFB3": "Carrefour", "ASAI3": "Assaí",
    # Alimentos/Bebidas
    "ABEV3": "Ambev", "JBSS3": "JBS", "BRFS3": "BRF",
    "BEEF3": "Minerva", "MRFG3": "Marfrig",
    "SLCE3": "SLC Agrícola", "SMTO3": "São Martinho",
    # Construcao/Shoppings
    "CYRE3": "Cyrela", "MRVE3": "MRV", "EZTC3": "EZTec", "JHSF3": "JHSF",
    "MULT3": "Multiplan", "IGTI11": "Iguatemi", "ALOS3": "Allos",
    # Industria/Logistica
    "WEGE3": "WEG", "EMBR3": "Embraer",
    "RAIL3": "Rumo", "CCRO3": "CCR", "ECOR3": "EcoRodovias",
    "AZUL4": "Azul", "GOLL4": "Gol",
    "TUPY3": "Tupy", "POSI3": "Positivo",
    # Saude
    "HAPV3": "Hapvida", "RDOR3": "Rede D'Or", "FLRY3": "Fleury",
    "RADL3": "Raia Drogasil", "QUAL3": "Qualicorp",
    "HYPE3": "Hypera", "NTCO3": "Natura",
    # Educacao
    "COGN3": "Cogna", "YDUQ3": "Yduqs",
    # Telecom
    "VIVT3": "Vivo", "TIMS3": "TIM",
    # Quimica/Outros
    "BRKM5": "Braskem", "IRBR3": "IRB Brasil Re",
    "CIEL3": "Cielo", "B3SA3": "B3",
    "TOTS3": "Totvs", "RENT3": "Localiza",
    "SBSP3": "Sabesp",
    # FIIs mais negociados
    "BCFF11": "BC Fund", "HGLG11": "CSHG Logística", "HGRE11": "CSHG Real Estate",
    "KNCR11": "Kinea Rendimentos", "KNRI11": "Kinea Renda Imobiliária",
    "MXRF11": "Maxi Renda", "XPLG11": "XP Log", "XPML11": "XP Malls",
    # ETFs
    "BOVA11": "iShares Ibovespa", "IVVB11": "iShares S&P 500",
    "SMAL11": "iShares Small Caps",
    # BDRs
    "AAPL34": "Apple", "AMZO34": "Amazon", "GOGL34": "Alphabet",
    "META34": "Meta", "MSFT34": "Microsoft", "NFLX34": "Netflix",
    "NVDC34": "Nvidia", "TSLA34": "Tesla", "DISB34": "Disney",
}


def popular_name(ticker: str) -> str:
    """Retorna nome popular/comercial do ticker, ou o proprio ticker se desconhecido."""
    return POPULAR_NAMES.get(ticker.upper().strip(), "")
