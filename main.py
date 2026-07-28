"""
API de reuniões online - recupera grade pública e (quando possível) salas ao vivo.
Deploy: Render / Railway / Fly.io
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="Reuniões Online API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BRT = timezone(timedelta(hours=-3))


class Meeting(BaseModel):
    fellowship: str
    group: str
    days: list[int]  # 0=Dom .. 6=Sáb
    start_min: int
    end_min: int
    link: str
    platform: str = "Zoom"
    zoom_id: Optional[str] = None
    password: Optional[str] = None
    note: Optional[str] = None
    live: bool = False
    source: str = ""


# ---------- Grade pública conhecida (links diretos quando existem) ----------
STATIC_MEETINGS: list[dict] = [
    {
        "fellowship": "CCA – Comedores Compulsivos",
        "group": "IGV CCA Online",
        "days": [1, 2, 3, 4, 5],
        "start_min": 20 * 60,
        "end_min": 21 * 60 + 30,
        "link": "https://us06web.zoom.us/j/89410304220",
        "platform": "Zoom",
        "zoom_id": "894 1030 4220",
        "password": "120912",
        "source": "https://ccaonline.com.br/",
    },
    {
        "fellowship": "CCA – Comedores Compulsivos",
        "group": "CCA 12 Passos",
        "days": [6],
        "start_min": 14 * 60,
        "end_min": 16 * 60,
        "link": "https://us06web.zoom.us/j/89410304220",
        "platform": "Zoom",
        "zoom_id": "894 1030 4220",
        "password": "120912",
        "source": "https://ccaonline.com.br/",
    },
    {
        "fellowship": "CCA – Comedores Compulsivos",
        "group": "CCA Domingo / Livro Azul",
        "days": [0, 6],
        "start_min": 18 * 60,
        "end_min": 21 * 60,
        "link": "https://us06web.zoom.us/j/89410304220",
        "platform": "Zoom",
        "zoom_id": "894 1030 4220",
        "password": "120912",
        "source": "https://ccaonline.com.br/",
    },
    {
        "fellowship": "Amor-Exigente",
        "group": "Sempre É Tempo",
        "days": [3],
        "start_min": 15 * 60,
        "end_min": 16 * 60 + 30,
        "link": "https://zoom.us/j/99206362967?pwd=ae102020",
        "platform": "Zoom",
        "zoom_id": "992 0636 2967",
        "password": "ae102020",
        "source": "https://amorexigente.org/online/",
    },
    {
        "fellowship": "Amor-Exigente",
        "group": "AE para Todos",
        "days": [5],
        "start_min": 20 * 60,
        "end_min": 21 * 60 + 30,
        "link": "https://zoom.us/j/95642248635?pwd=790488",
        "platform": "Zoom",
        "zoom_id": "956 4224 8635",
        "password": "790488",
        "source": "https://amorexigente.org/online/",
    },
    {
        "fellowship": "Amor-Exigente",
        "group": "Cônjuges",
        "days": [6],
        "start_min": 18 * 60,
        "end_min": 19 * 60 + 30,
        "link": "https://zoom.us/j/96404208932?pwd=101020",
        "platform": "Zoom",
        "zoom_id": "964 0420 8932",
        "password": "101020",
        "source": "https://amorexigente.org/online/",
    },
    {
        "fellowship": "Procrastinadores Anônimos",
        "group": "Grupo Vida Nova",
        "days": [0, 1, 2, 3, 4, 5, 6],
        "start_min": 8 * 60,
        "end_min": 10 * 60,
        "link": "https://us04web.zoom.us/j/5557400965?pwd=STljOEYzaUF6TzlNb09sVVFYaDM1dz09",
        "platform": "Zoom",
        "zoom_id": "555 740 0965",
        "password": "0000",
        "note": "Confirme no site se o link mudou",
        "source": "https://www.procrastinadoresanonimos.com/",
    },
    {
        "fellowship": "Nicotina Anônimos",
        "group": "VOREN",
        "days": [0, 1, 2, 3, 4, 5],
        "start_min": 20 * 60,
        "end_min": 21 * 60 + 30,
        "link": "https://meet.google.com/etg-wukn-kvy",
        "platform": "Google Meet",
        "source": "https://nicotine-anonymous.org/portugues/",
    },
    {
        "fellowship": "Nicotina Anônimos",
        "group": "Grupo Jabaquara",
        "days": [1, 3, 5],
        "start_min": 20 * 60,
        "end_min": 21 * 60 + 30,
        "link": "https://chat.whatsapp.com/GL7TPWKYbv533cmoMjXvG2",
        "platform": "WhatsApp → Zoom",
        "note": "Entre no WhatsApp do grupo para o link do Zoom",
        "source": "https://nicotine-anonymous.org/portugues/",
    },
    {
        "fellowship": "CoDA",
        "group": "CoDA Brasil (sala comum)",
        "days": [0, 1, 2, 3, 4, 5, 6],
        "start_min": 8 * 60,
        "end_min": 23 * 60,
        "link": "https://zoom.us/j/9380749731?pwd=121212",
        "platform": "Zoom",
        "zoom_id": "938 0749 731",
        "password": "121212",
        "note": "Vários horários – confirme no site",
        "source": "https://www.codabrasil.org.br/",
    },
    {
        "fellowship": "Narcóticos Anônimos",
        "group": "CSR Brasil – ver salas AO VIVO",
        "days": [0, 1, 2, 3, 4, 5, 6],
        "start_min": 0,
        "end_min": 24 * 60,
        "link": "https://csrbrasil.org.br/#reunioes-online",
        "platform": "Zoom",
        "password": "000000",
        "note": "Senha padrão das salas CSR: 000000. Abra o site e clique em Entrar na sala desejada.",
        "source": "https://csrbrasil.org.br/",
    },
    {
        "fellowship": "Alcoólicos Anônimos",
        "group": "Intergrupos Online",
        "days": [0, 1, 2, 3, 4, 5, 6],
        "start_min": 5 * 60,
        "end_min": 23 * 60,
        "link": "https://intergrupos-aa.org.br/",
        "platform": "Meet/Zoom",
        "note": "Várias salas – grade do dia no site",
        "source": "https://intergrupos-aa.org.br/",
    },
    {
        "fellowship": "Jogadores Anônimos",
        "group": "JA Online",
        "days": [0, 1, 2, 3, 4, 5, 6],
        "start_min": 8 * 60,
        "end_min": 22 * 60,
        "link": "https://jogadoresanonimos.com.br/",
        "platform": "Zoom/Teams",
        "source": "https://jogadoresanonimos.com.br/",
    },
    {
        "fellowship": "Devedores Anônimos",
        "group": "DA Online",
        "days": [0, 1, 2, 3, 4, 5, 6],
        "start_min": 6 * 60,
        "end_min": 21 * 60 + 30,
        "link": "https://devedoresanonimosbrasil.org/",
        "platform": "Zoom",
        "source": "https://devedoresanonimosbrasil.org/",
    },
    {
        "fellowship": "CMA",
        "group": "CMA Brasil",
        "days": [0, 1, 2, 3, 4],
        "start_min": 18 * 60 + 30,
        "end_min": 20 * 60 + 30,
        "link": "https://www.cmabr.org/reunioes",
        "platform": "Zoom",
        "source": "https://www.cmabr.org/reunioes",
    },
    {
        "fellowship": "Ansiedade / Pânico",
        "group": "GAPDAP",
        "days": [0, 1, 2, 3, 4, 5, 6],
        "start_min": 19 * 60,
        "end_min": 21 * 60,
        "link": "https://www.gapdap.org.br/",
        "platform": "Zoom",
        "source": "https://www.gapdap.org.br/",
    },
    {
        "fellowship": "ABRATA",
        "group": "GAO Adultos",
        "days": [2, 3, 5],
        "start_min": 19 * 60,
        "end_min": 20 * 60 + 30,
        "link": "https://www.abrata.org.br/site2025/grupo-de-apoio-online/",
        "platform": "Zoom",
        "note": "Inscrição prévia no site",
        "source": "https://www.abrata.org.br/",
    },
    {
        "fellowship": "CVV",
        "group": "Apoio emocional 24h (188)",
        "days": [0, 1, 2, 3, 4, 5, 6],
        "start_min": 0,
        "end_min": 24 * 60,
        "link": "https://cvv.org.br/",
        "platform": "Telefone",
        "note": "Ligue 188",
        "source": "https://cvv.org.br/",
    },
]

# Cache de salas extraídas do CSR (preenchido em background quando possível)
_csr_live_cache: list[dict] = []
_csr_last_fetch: Optional[datetime] = None


def now_brt() -> datetime:
    return datetime.now(BRT)


def mins_now() -> int:
    n = now_brt()
    return n.hour * 60 + n.minute


def is_happening(m: dict) -> bool:
    n = now_brt()
    if n.weekday() == 6:
        day = 0  # domingo
    else:
        day = n.weekday() + 1  # Python: seg=0 → nosso seg=1
    # Corrige: Python weekday Mon=0..Sun=6. Nosso: Sun=0..Sat=6
    py_to_ours = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 0}
    today = py_to_ours[n.weekday()]
    if today not in m["days"]:
        return False
    t = mins_now()
    # salas 24h
    if m["end_min"] - m["start_min"] >= 20 * 60:
        return True
    return m["start_min"] - 10 <= t <= m["end_min"] + 5


def is_today(m: dict) -> bool:
    n = now_brt()
    py_to_ours = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 0}
    return py_to_ours[n.weekday()] in m["days"]


async def try_fetch_csr_meetings() -> list[dict]:
    """
    Tenta obter salas do CSR. O site carrega via JS; sem headless browser
    muitas vezes só vem o HTML vazio. Mantemos o link da seção AO VIVO.
    Em deploys com Playwright dá para melhorar depois.
    """
    global _csr_live_cache, _csr_last_fetch
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            r = await client.get(
                "https://csrbrasil.org.br/",
                headers={"User-Agent": "Mozilla/5.0 (compatible; ReunioesBot/1.0)"},
            )
            if r.status_code != 200:
                return _csr_live_cache
            # procura qualquer zoom.us/j/ no HTML (caso venha embutido)
            soup = BeautifulSoup(r.text, "lxml")
            found = []
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if "zoom.us/j/" in href or "zoom.us/w/" in href:
                    name = (a.get_text() or "Sala NA").strip()[:80]
                    found.append(
                        {
                            "fellowship": "Narcóticos Anônimos",
                            "group": name or "Sala CSR",
                            "days": [0, 1, 2, 3, 4, 5, 6],
                            "start_min": 0,
                            "end_min": 24 * 60,
                            "link": href,
                            "platform": "Zoom",
                            "password": "000000",
                            "note": "Extraído do CSR – senha padrão 000000",
                            "source": "https://csrbrasil.org.br/",
                            "live": True,
                        }
                    )
            if found:
                _csr_live_cache = found
                _csr_last_fetch = now_brt()
            return _csr_live_cache
    except Exception:
        return _csr_live_cache


@app.on_event("startup")
async def startup():
    asyncio.create_task(try_fetch_csr_meetings())


@app.get("/api/health")
def health():
    return {
        "ok": True,
        "time_brt": now_brt().isoformat(),
        "csr_cache": len(_csr_live_cache),
        "csr_last_fetch": _csr_last_fetch.isoformat() if _csr_last_fetch else None,
    }


@app.get("/api/meetings")
async def list_meetings(
    mode: str = Query("today", pattern="^(now|today|all)$"),
    q: str = Query(""),
):
    """
    mode=now  → só acontecendo agora
    mode=today → todas de hoje
    mode=all  → grade completa
    """
    # tenta atualizar CSR se cache velho (>30 min)
    if _csr_last_fetch is None or (now_brt() - _csr_last_fetch).seconds > 1800:
        await try_fetch_csr_meetings()

    items = list(STATIC_MEETINGS) + list(_csr_live_cache)
    q = (q or "").lower().strip()

    result = []
    for m in items:
        if mode == "now" and not is_happening(m):
            continue
        if mode == "today" and not is_today(m):
            continue
        if q and q not in m["group"].lower() and q not in m["fellowship"].lower():
            continue
        row = dict(m)
        row["live"] = is_happening(m)
        result.append(row)

    result.sort(key=lambda x: (0 if x["live"] else 1, x["start_min"]))
    return {
        "mode": mode,
        "count": len(result),
        "time_brt": now_brt().isoformat(),
        "meetings": result,
    }


@app.get("/")
async def index():
    return FileResponse("static/index.html")


# monta arquivos estáticos
import os
if os.path.isdir("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")
