import re
from typing import Optional

import requests
from bs4 import BeautifulSoup

from schemas.esempio import EsempioRead
from schemas.parola import ParolaRead
from schemas.punto import PuntoRead
from schemas.significato import SignificatoRead

DOT_TOKEN = "§DOT§"

CATEGORIA_REGEX = re.compile(
    r"(v\.\s*tr\.\s*e\s*intr\."
    r"|v\.\s*intr\.\s*e\s*tr\."
    r"|v\.\s*tr\."
    r"|v\.\s*intr\."
    r"|v\.\s*rifl\."
    r"|v\."
    r"|s\.\s*m\.\s*e\s*f\."
    r"|s\.\s*f\.\s*e\s*m\."
    r"|s\.\s*m\."
    r"|s\.\s*f\."
    r"|agg\."
    r"|avv\."
    r"|prep\."
    r"|cong\."
    r"|pron\.)",
    re.IGNORECASE
)

ABBREVIAZIONI = [
    "m.", "s.", "f.", "n.", "pl.", "sing.",
    "fig.", "ecc.", "sim.", "cfr.", "v.", "ant.",
    "lett.", "letter.", "abbrev.", "lat.", "fam.",
    "prov.", "locuz.", "avv.", "sign.", "partic.",
    "com.", "spec.", "mod.", "estens.", "anticam.",
    "propriam.", "traduz.", "giur.", "sec.", "dim.",
    "accr.", "spreg.", "pegg.", "dial."
]


# =========================================================
# Utility testo
# =========================================================

def normalizza_spazi(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip(" \n\t; ")


def proteggi_punti_speciali(testo: str) -> str:
    # abbreviazioni note
    for abbr in sorted(ABBREVIAZIONI, key=len, reverse=True):
        pattern = re.escape(abbr)
        repl = abbr.replace(".", DOT_TOKEN)
        testo = re.sub(pattern, repl, testo, flags=re.IGNORECASE)

    # iniziali tipo:
    # T. Tasso
    # L. B. Alberti
    # S. M.
    testo = re.sub(r"\b([A-ZÀ-Ú])\.", rf"\1{DOT_TOKEN}", testo)

    return testo


def ripristina_punti(testo: str) -> str:
    return testo.replace(DOT_TOKEN, ".")


def merge_frammenti(parti: list[str]) -> list[str]:
    risultato = []

    for p in parti:
        p = p.strip()
        if not p:
            continue

        if risultato and (
            p.startswith("(") or
            re.fullmatch(r"[A-Z]\.?", p) or
            re.fullmatch(r"(?:[A-Z]\.?\s*){1,5}", p)
        ):
            risultato[-1] += " " + p
        else:
            risultato.append(p)

    return risultato


# =========================================================
# Split significati / esempi
# =========================================================

def split_significati(testo: str) -> list[str]:
    """
    Divide il testo in macro-significati.
    Heuristica:
    - split dopo un punto
    - solo se dopo c'è una maiuscola
    - non se il punto fa parte di abbreviazioni / iniziali
    """
    testo = normalizza_spazi(testo)
    if not testo:
        return []

    testo = proteggi_punti_speciali(testo)

    parti = re.split(
        r'(?<=\.)\s+(?=(?:[«“"\'‘’])?[A-ZÀ-Ú])',
        testo
    )

    parti = [ripristina_punti(p).strip() for p in parti if p.strip()]
    parti = merge_frammenti(parti)

    return parti


def split_esempi(testo: str) -> list[str]:
    """
    Divide la parte dopo i due punti nei vari esempi.
    Heuristica:
    - split sui ';'
    """
    testo = normalizza_spazi(testo)
    if not testo:
        return []

    parti = [normalizza_spazi(p).strip(" ;") for p in testo.split(";")]
    return [p for p in parti if p]


def costruisci_significati(testo: str) -> list[dict]:
    """
    Trasforma un testo in:
    [
      {"indice": 1, "testo": "...", "esempi": [...]},
      ...
    ]

    Regola:
    - prima del primo ":" => testo del significato
    - dopo ":" => esempi separati da ";"
    """
    chunks = split_significati(testo)
    risultati = []

    for i, chunk in enumerate(chunks, start=1):
        chunk = normalizza_spazi(chunk)
        if not chunk:
            continue

        if ":" in chunk:
            definizione, resto = chunk.split(":", 1)
            definizione = normalizza_spazi(definizione).strip(" .;:")
            esempi = split_esempi(resto)
        else:
            definizione = chunk.strip(" .;:")
            esempi = []

        risultati.append({
            "indice": i,
            "testo": definizione,
            "esempi": esempi
        })

    return risultati


# =========================================================
# Parsing struttura blocchi
# =========================================================

def separa_testata_e_corpo(blocchi: list[dict]) -> list[dict]:
    """
    Se il primo blocco introduttivo contiene:
        testata – corpo
    allora:
    - il primo blocco resta la testata
    - il corpo diventa un nuovo punto sintetico
    """
    if not blocchi:
        return blocchi

    primo = blocchi[0]

    if primo["numero"] is not None:
        return blocchi

    testo = normalizza_spazi(primo["testo"])

    parti = re.split(r"\s+[–-]\s+", testo, maxsplit=1)
    if len(parti) != 2:
        return blocchi

    testata, corpo = parti
    testata = normalizza_spazi(testata)
    corpo = normalizza_spazi(corpo)

    primo["testo"] = testata

    if not corpo:
        return blocchi

    max_num = max((b["numero"] for b in blocchi if b["numero"] is not None), default=0)

    nuovo_blocco = {
        "numero": max_num + 1 if max_num > 0 else 1,
        "lettera": None,
        "testo": corpo,
        "significati": []
    }

    return [primo, nuovo_blocco] + blocchi[1:]


def espandi_blocchi_diamante(blocchi: list[dict]) -> list[dict]:
    """
    Ogni '◆ ...' viene trasformato in un nuovo punto sintetico.
    """
    nuovi_blocchi = []
    max_num = max((b["numero"] for b in blocchi if b["numero"] is not None), default=0)

    for blocco in blocchi:
        testo = normalizza_spazi(blocco["testo"])

        if "◆" not in testo:
            nuovi_blocchi.append(blocco)
            continue

        parti = [normalizza_spazi(p) for p in re.split(r"\s*◆\s*", testo) if normalizza_spazi(p)]

        if not parti:
            nuovi_blocchi.append(blocco)
            continue

        nuovi_blocchi.append({
            **blocco,
            "testo": parti[0],
            "significati": []
        })

        for extra in parti[1:]:
            max_num += 1
            nuovi_blocchi.append({
                "numero": max_num,
                "lettera": None,
                "testo": extra,
                "significati": []
            })

    return nuovi_blocchi


def popola_significati(blocchi: list[dict]) -> list[dict]:
    """
    Regole:
    - se un numero NON ha sottovoci a./b./c., il blocco numero=X, lettera=None
      viene trasformato in significati
    - se un numero HA sottovoci a./b./c., il blocco padre lettera=None resta
      descrittivo e si riempiono solo i blocchi con lettera
    """
    numeri_con_lettere = {
        b["numero"]
        for b in blocchi
        if b["numero"] is not None and b["lettera"] is not None
    }

    for b in blocchi:
        b["significati"] = []

        numero = b["numero"]
        lettera = b["lettera"]

        if numero is None:
            continue

        if numero not in numeri_con_lettere and lettera is None:
            b["significati"] = costruisci_significati(b["testo"])

        elif numero in numeri_con_lettere and lettera is not None:
            b["significati"] = costruisci_significati(b["testo"])

    return blocchi


def parse_definizione_html(p) -> list[dict]:
    blocchi = []

    corrente = {
        "numero": None,
        "lettera": None,
        "testo": "",
        "significati": []
    }

    numero_corrente = 0

    for node in p.children:
        if getattr(node, "name", None) == "strong":
            text = normalizza_spazi(node.get_text(strip=True))

            m_num = re.match(r"^(\d+)\.$", text)
            m_num_letter = re.match(r"^(\d+)\.\s*([a-z])\.$", text)
            m_letter = re.match(r"^([a-z])\.$", text)

            if m_num or m_num_letter or m_letter:
                if corrente["testo"].strip():
                    corrente["testo"] = normalizza_spazi(corrente["testo"])
                    blocchi.append(corrente)

                corrente = {
                    "numero": None,
                    "lettera": None,
                    "testo": "",
                    "significati": []
                }

                if m_num:
                    corrente["numero"] = int(m_num.group(1))
                    numero_corrente = corrente["numero"]

                elif m_num_letter:
                    corrente["numero"] = int(m_num_letter.group(1))
                    corrente["lettera"] = m_num_letter.group(2)
                    numero_corrente = corrente["numero"]

                elif m_letter:
                    corrente["numero"] = numero_corrente
                    corrente["lettera"] = m_letter.group(1)

                continue

        if getattr(node, "name", None) in {"style", "script"}:
            continue

        if getattr(node, "name", None):
            corrente["testo"] += node.get_text(" ", strip=False)
        else:
            corrente["testo"] += str(node)

    if corrente["testo"].strip():
        corrente["testo"] = normalizza_spazi(corrente["testo"])
        blocchi.append(corrente)

    blocchi = separa_testata_e_corpo(blocchi)
    blocchi = espandi_blocchi_diamante(blocchi)
    blocchi = popola_significati(blocchi)

    return blocchi


# =========================================================
# Parsing metadati parola
# =========================================================

def estrai_metadati_primo_blocco(
    testo_primo_blocco: str,
    nome_fallback: Optional[str] = None
) -> tuple[str, Optional[str], Optional[str], Optional[str]]:
    testo = normalizza_spazi(testo_primo_blocco)
    testo = testo.rstrip("–- ").strip()

    origine = None
    coniugazione = None
    categoria = None
    nome = nome_fallback

    # origine: contenuto tra [...]
    m_origine = re.search(r"\[(.*?)\]", testo)
    if m_origine:
        origine = normalizza_spazi(m_origine.group(1))

    # coniugazione: primo (...) fuori dalle []
    testo_senza_origine = re.sub(r"\[.*?\]", "", testo).strip()
    m_coniugazione = re.search(r"\((.*?)\)", testo_senza_origine)
    if m_coniugazione:
        coniugazione = normalizza_spazi(m_coniugazione.group(1))

    # prefisso prima di [ oppure (
    stop_idx = len(testo)
    idx_quad = testo.find("[")
    idx_tonda = testo.find("(")

    if idx_quad != -1:
        stop_idx = min(stop_idx, idx_quad)
    if idx_tonda != -1:
        stop_idx = min(stop_idx, idx_tonda)

    prefisso = normalizza_spazi(testo[:stop_idx]).strip(" ;:-–")

    # cerco la categoria nel prefisso
    m_categoria = CATEGORIA_REGEX.search(prefisso)
    if m_categoria:
        categoria = normalizza_spazi(m_categoria.group(1)).strip()

        nome_estratto = normalizza_spazi(prefisso[:m_categoria.start()]).strip(" .;:-–")
        if nome_estratto:
            nome = nome_estratto

    if not nome:
        raise ValueError("Impossibile determinare il nome della parola")

    return nome, categoria, origine, coniugazione


def estrai_nome_da_ps1(soup: BeautifulSoup) -> Optional[str]:
    ps = soup.find_all("p")
    if len(ps) > 1:
        testo = normalizza_spazi(ps[1].get_text(" ", strip=True))
        if testo:
            return testo
    return None


# =========================================================
# Conversione blocchi -> dataclass
# =========================================================

def blocchi_to_parola_read(
    blocchi: list[dict],
    nome_input_utente: str,
    nome_fallback: Optional[str] = None
) -> ParolaRead:
    if not blocchi:
        raise ValueError("Lista blocchi vuota")

    primo_blocco = blocchi[0]

    nome_accento, categoria, origine, coniugazione = estrai_metadati_primo_blocco(
        primo_blocco["testo"],
        nome_fallback=nome_fallback
    )

    nome = normalizza_spazi(nome_input_utente).lower()
    categoria_val = categoria or "undefined"

    punti_map: dict[int, PuntoRead] = {}

    for blocco in blocchi:
        numero_punto = blocco["numero"]
        lettera = blocco["lettera"]
        testo_blocco = blocco["testo"]
        significati_blocco = blocco.get("significati", [])

        if numero_punto is None:
            continue

        if numero_punto not in punti_map:
            punti_map[numero_punto] = PuntoRead(
                numero=numero_punto,
                nome_parola=nome,
                categoria_parola=categoria_val,
                descrizione=None,
                significati=[]
            )

        punto = punti_map[numero_punto]

        if lettera is None and not significati_blocco:
            if testo_blocco:
                punto.descrizione = testo_blocco
            continue

        if lettera is None and significati_blocco:
            for s in significati_blocco:
                esempi = [
                    EsempioRead(
                        numero_esempio=i,
                        lettera_significato=None,
                        numero_significato=s["indice"],
                        numero_punto=numero_punto,
                        nome_parola=nome,
                        categoria_parola=categoria_val,
                        testo=ex
                    )
                    for i, ex in enumerate(s.get("esempi", []), start=1)
                ]

                punto.significati.append(
                    SignificatoRead(
                        lettera=None,
                        numero=s["indice"],
                        numero_punto=numero_punto,
                        nome_parola=nome,
                        categoria_parola=categoria_val,
                        testo=s["testo"],
                        esempi=esempi
                    )
                )
            continue

        if lettera is not None:
            for s in significati_blocco:
                esempi = [
                    EsempioRead(
                        numero_esempio=i,
                        lettera_significato=lettera,
                        numero_significato=s["indice"],
                        numero_punto=numero_punto,
                        nome_parola=nome,
                        categoria_parola=categoria_val,
                        testo=ex
                    )
                    for i, ex in enumerate(s.get("esempi", []), start=1)
                ]

                punto.significati.append(
                    SignificatoRead(
                        lettera=lettera,
                        numero=s["indice"],
                        numero_punto=numero_punto,
                        nome_parola=nome,
                        categoria_parola=categoria_val,
                        testo=s["testo"],
                        esempi=esempi
                    )
                )

    punti = [punti_map[k] for k in sorted(punti_map.keys())]

    return ParolaRead(
        nome=nome,
        nome_accento=nome_accento,
        categoria=categoria,
        origine=origine,
        coniugazione=coniugazione,
        punti=punti
    )

# =========================================================
# HTML helpers
# =========================================================

def trova_paragrafo_definizione(soup: BeautifulSoup):
    ps = soup.find_all("p")
    if len(ps) > 2:
        return ps[2]
    raise ValueError("Paragrafo della definizione non trovato")


# =========================================================
# Scraper principale
# =========================================================

def scrape_treccani(parola: str) -> ParolaRead:
    url = f"https://www.treccani.it/vocabolario/{parola}"
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20, allow_redirects=True)

    if response.url.rstrip("/") == "https://www.treccani.it":
        raise ValueError(f"Parola non trovata: {parola}")

    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    p_definizione = trova_paragrafo_definizione(soup)

    if p_definizione is None:
        raise ValueError(f"Paragrafo definizione non trovato per: {parola}")

    blocchi = parse_definizione_html(p_definizione)

    nome_fallback = estrai_nome_da_ps1(soup) or parola
    parola_read = blocchi_to_parola_read(
        blocchi,
        nome_input_utente=parola,
        nome_fallback=nome_fallback
    )
    return parola_read

def scrape_treccani_multiple(parola: str) -> list[ParolaRead]:
    try:
        p_0 = scrape_treccani(parola)
        return [p_0]
    except ValueError:
        contatore = 1
        omonimi = []

        while True:
            try:
                p_n = scrape_treccani(parola + str(contatore))
                omonimi.append(p_n)
                contatore += 1
            except ValueError:
                return omonimi
