import discord
from discord import app_commands
import json
import os
import random
from datetime import datetime, timedelta

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

DATA_FILE = "kazino.json"
GUILD_ID = 1520542974432252025

def ucitaj():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def sacuvaj(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_igrac(data, user_id):
    uid = str(user_id)
    if uid not in data:
        data[uid] = {
            "balans": 1000,
            "poslednja_dnevnica": None,
            "dobijeno_danas": 0,
            "datum_resetovanja": str(datetime.now().date())
        }
    danas = str(datetime.now().date())
    if data[uid]["datum_resetovanja"] != danas:
        data[uid]["dobijeno_danas"] = 0
        data[uid]["datum_resetovanja"] = danas
    return data, uid

@bot.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)
    tree.copy_global_to(guild=guild)
    await tree.sync(guild=guild)
    print(f"Bot je online! {bot.user}")
    print("Komande sinhronizovane!")

# ==================== BANKA ====================
@tree.command(name="banka", description="Pogledaj svoje stanje")
async def banka(interaction: discord.Interaction):
    data = ucitaj()
    data, uid = get_igrac(data, interaction.user.id)
    sacuvaj(data)
    balans = data[uid]["balans"]
    await interaction.response.send_message(
        f"💰 **{interaction.user.name}**, tvoje stanje: **{balans} dinara**"
    )

# ==================== DNEVNICA ====================
@tree.command(name="dnevnica", description="Uzmi dnevnih 1000 dinara")
async def dnevnica(interaction: discord.Interaction):
    data = ucitaj()
    data, uid = get_igrac(data, interaction.user.id)

    poslednja = data[uid]["poslednja_dnevnica"]
    sad = datetime.now()

    if poslednja:
        poslednja_dt = datetime.fromisoformat(poslednja)
        razlika = sad - poslednja_dt
        if razlika < timedelta(hours=24):
            preostalo = timedelta(hours=24) - razlika
            sati = int(preostalo.total_seconds() // 3600)
            minuti = int((preostalo.total_seconds() % 3600) // 60)
            await interaction.response.send_message(
                f"⏰ Moraš da sačekaš još **{sati}h {minuti}min** za sledeću dnevnicu!"
            )
            return

    data[uid]["balans"] += 1000
    data[uid]["poslednja_dnevnica"] = sad.isoformat()
    sacuvaj(data)

    await interaction.response.send_message(
        f"✅ **{interaction.user.name}** uzeo dnevnicu! +1000 dinara\n"
        f"💰 Novo stanje: **{data[uid]['balans']} dinara**"
    )

# ==================== RULET ====================
@tree.command(name="rulet", description="Igraj rulet")
@app_commands.describe(ulog="Koliko dinara ulazes", boja="crvena, crna ili zelena")
async def rulet(interaction: discord.Interaction, ulog: int, boja: str):
    data = ucitaj()
    data, uid = get_igrac(data, interaction.user.id)

    boja = boja.lower()
    if boja not in ["crvena", "crna", "zelena"]:
        await interaction.response.send_message("❌ Boja mora biti: **crvena**, **crna** ili **zelena**")
        return

    if ulog <= 0:
        await interaction.response.send_message("❌ Ulog mora biti veći od 0!")
        return

    if data[uid]["balans"] < ulog:
        await interaction.response.send_message(
            f"❌ Nemaš dovoljno dinara! Tvoje stanje: **{data[uid]['balans']} dinara**"
        )
        return

    prekoracen = data[uid]["dobijeno_danas"] >= 100000

    if prekoracen:
        rezultat = random.choices(
            ["crvena", "crna", "zelena"],
            weights=[16.5, 16.5, 67],
            k=1
        )[0]
    else:
        rezultat = random.choices(
            ["crvena", "crna", "zelena"],
            weights=[49.5, 49.5, 1],
            k=1
        )[0]

    if rezultat == boja:
        if boja == "zelena":
            dobitak = ulog * 35
        else:
            dobitak = ulog * 2
        data[uid]["balans"] += dobitak - ulog
        data[uid]["dobijeno_danas"] += dobitak
        sacuvaj(data)
        await interaction.response.send_message(
            f"🎰 Rulet stao na: **{rezultat}**\n"
            f"✅ Pobedio si! Dobitak: **{dobitak} dinara**\n"
            f"💰 Novo stanje: **{data[uid]['balans']} dinara**"
        )
    else:
        data[uid]["balans"] -= ulog
        sacuvaj(data)
        await interaction.response.send_message(
            f"🎰 Rulet stao na: **{rezultat}**\n"
            f"❌ Izgubio si **{ulog} dinara**\n"
            f"💰 Novo stanje: **{data[uid]['balans']} dinara**"
        )

# ==================== BLACKJACK ====================
def napravi_spil():
    karte = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A'] * 4
    random.shuffle(karte)
    return karte

def vrednost_karata(karte):
    vrednost = 0
    asovi = 0
    for karta in karte:
        if karta in ['J', 'Q', 'K']:
            vrednost += 10
        elif karta == 'A':
            vrednost += 11
            asovi += 1
        else:
            vrednost += int(karta)
    while vrednost > 21 and asovi:
        vrednost -= 10
        asovi -= 1
    return vrednost

bj_igre = {}

@tree.command(name="blackjack", description="Igraj blackjack")
@app_commands.describe(ulog="Koliko dinara ulazes")
async def blackjack(interaction: discord.Interaction, ulog: int):
    data = ucitaj()
    data, uid = get_igrac(data, interaction.user.id)

    if ulog <= 0:
        await interaction.response.send_message("❌ Ulog mora biti veći od 0!")
        return

    if data[uid]["balans"] < ulog:
        await interaction.response.send_message(
            f"❌ Nemaš dovoljno dinara! Tvoje stanje: **{data[uid]['balans']} dinara**"
        )
        return

    spil = napravi_spil()
    igrac_karte = [spil.pop(), spil.pop()]
    diler_karte = [spil.pop(), spil.pop()]

    bj_igre[uid] = {
        "ulog": ulog,
        "igrac": igrac_karte,
        "diler": diler_karte,
        "spil": spil
    }

    sacuvaj(data)

    igrac_vrednost = vrednost_karata(igrac_karte)
    await interaction.response.send_message(
        f"🃏 **Tvoje karte:** {' | '.join(igrac_karte)} = **{igrac_vrednost}**\n"
        f"🃏 **Dilerova karta:** {diler_karte[0]} | ?\n\n"
        f"Ukucaj **/hit** da uzmeš kartu ili **/stand** da staješ!"
    )

@tree.command(name="hit", description="Uzmi jos jednu kartu u blackjacku")
async def hit(interaction: discord.Interaction):
    uid = str(interaction.user.id)

    if uid not in bj_igre:
        await interaction.response.send_message("❌ Nisi u igri! Koristi /blackjack da počneš.")
        return

    igra = bj_igre[uid]
    nova_karta = igra["spil"].pop()
    igra["igrac"].append(nova_karta)

    igrac_vrednost = vrednost_karata(igra["igrac"])

    if igrac_vrednost > 21:
        data = ucitaj()
        data, uid2 = get_igrac(data, interaction.user.id)
        data[uid2]["balans"] -= igra["ulog"]
        sacuvaj(data)
        del bj_igre[uid]
        await interaction.response.send_message(
            f"🃏 **Tvoje karte:** {' | '.join(igra['igrac'])} = **{igrac_vrednost}**\n"
            f"💥 Prešao si 21! Izgubio si **{igra['ulog']} dinara**\n"
            f"💰 Novo stanje: **{data[uid2]['balans']} dinara**"
        )
        return

    await interaction.response.send_message(
        f"🃏 **Tvoje karte:** {' | '.join(igra['igrac'])} = **{igrac_vrednost}**\n"
        f"🃏 **Dilerova karta:** {igra['diler'][0]} | ?\n\n"
        f"Ukucaj **/hit** da uzmeš kartu ili **/stand** da staješ!"
    )

@tree.command(name="stand", description="Stani u blackjacku")
async def stand(interaction: discord.Interaction):
    uid = str(interaction.user.id)

    if uid not in bj_igre:
        await interaction.response.send_message("❌ Nisi u igri! Koristi /blackjack da počneš.")
        return

    igra = bj_igre[uid]
    igrac_vrednost = vrednost_karata(igra["igrac"])

    # Diler vuče karte dok nema 17+
    while vrednost_karata(igra["diler"]) < 17:
        igra["diler"].append(igra["spil"].pop())

    diler_vrednost = vrednost_karata(igra["diler"])

    data = ucitaj()
    data, uid2 = get_igrac(data, interaction.user.id)

    rezultat = (
        f"🃏 **Tvoje karte:** {' | '.join(igra['igrac'])} = **{igrac_vrednost}**\n"
        f"🃏 **Dilerove karte:** {' | '.join(igra['diler'])} = **{diler_vrednost}**\n\n"
    )

    if diler_vrednost > 21 or igrac_vrednost > diler_vrednost:
        dobitak = igra["ulog"] * 2
        data[uid2]["balans"] += igra["ulog"]
        data[uid2]["dobijeno_danas"] += dobitak
        rezultat += f"✅ Pobedio si! Dobitak: **{dobitak} dinara**\n"
    elif igrac_vrednost == diler_vrednost:
        rezultat += f"🤝 Nerešeno! Vraćamo ti ulog: **{igra['ulog']} dinara**\n"
    else:
        data[uid2]["balans"] -= igra["ulog"]
        rezultat += f"❌ Diler pobedio! Izgubio si **{igra['ulog']} dinara**\n"

    rezultat += f"💰 Novo stanje: **{data[uid2]['balans']} dinara**"

    sacuvaj(data)
    del bj_igre[uid]

    await interaction.response.send_message(rezultat)

# ==================== APARAT ====================
SIMBOLI = ["🍋", "🍒", "🍇", "⭐", "💎", "7️⃣"]

KOEFICIJENTI = {
    "🍋": 2,
    "🍒": 3,
    "🍇": 4,
    "⭐": 5,
    "💎": 10,
    "7️⃣": 20
}

@tree.command(name="aparat", description="Igraj aparat")
@app_commands.describe(ulog="Koliko dinara ulazes")
async def aparat(interaction: discord.Interaction, ulog: int):
    data = ucitaj()
    data, uid = get_igrac(data, interaction.user.id)

    if ulog <= 0:
        await interaction.response.send_message("❌ Ulog mora biti veći od 0!")
        return

    if data[uid]["balans"] < ulog:
        await interaction.response.send_message(
            f"❌ Nemaš dovoljno dinara! Tvoje stanje: **{data[uid]['balans']} dinara**"
        )
        return

    prekoracen = data[uid]["dobijeno_danas"] >= 100000

    # Tezine za simbole
    if prekoracen:
        tezine = [40, 30, 20, 8, 2, 0]  # Bez dzekpota kad je prekoracen
    else:
        tezine = [35, 25, 20, 12, 6, 2]

    rezultat = random.choices(SIMBOLI, weights=tezine, k=3)

    data[uid]["balans"] -= ulog

    if rezultat[0] == rezultat[1] == rezultat[2]:
        koef = KOEFICIJENTI[rezultat[0]]
        dobitak = ulog * koef
        data[uid]["balans"] += dobitak
        data[uid]["dobijeno_danas"] += dobitak
        sacuvaj(data)
        await interaction.response.send_message(
            f"🎰 **{rezultat[0]} {rezultat[1]} {rezultat[2]}**\n"
            f"✅ DŽEKPOT! Koeficijent x{koef} – Dobitak: **{dobitak} dinara**\n"
            f"💰 Novo stanje: **{data[uid]['balans']} dinara**"
        )
    else:
        sacuvaj(data)
        await interaction.response.send_message(
            f"🎰 **{rezultat[0]} {rezultat[1]} {rezultat[2]}**\n"
            f"❌ Nisi pogodio! Izgubio si **{ulog} dinara**\n"
            f"💰 Novo stanje: **{data[uid]['balans']} dinara**"
        )

# ==================== POKER ====================
BOJE_KARATA = ["♠", "♥", "♦", "♣"]
VREDNOSTI_KARATA = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]

def napravi_poker_spil():
    spil = [f"{v}{b}" for b in BOJE_KARATA for v in VREDNOSTI_KARATA]
    random.shuffle(spil)
    return spil

def vrednost_karte(karta):
    v = karta[:-1]
    if v in ["J", "Q", "K"]:
        return 10
    elif v == "A":
        return 14
    return int(v)

def oceni_ruku(karte):
    vrednosti = sorted([vrednost_karte(k) for k in karte], reverse=True)
    boje = [k[-1] for k in karte]
    
    flush = len(set(boje)) == 1
    straight = vrednosti == list(range(vrednosti[0], vrednosti[0]-5, -1))
    
    from collections import Counter
    brojevi = Counter(vrednosti)
    grupe = sorted(brojevi.values(), reverse=True)
    
    if flush and straight:
        return (8, "Straight Flush")
    if grupe[0] == 4:
        return (7, "Poker (4 iste)")
    if grupe[0] == 3 and grupe[1] == 2:
        return (6, "Full House")
    if flush:
        return (5, "Flush")
    if straight:
        return (4, "Straight")
    if grupe[0] == 3:
        return (3, "Tris (3 iste)")
    if grupe[0] == 2 and grupe[1] == 2:
        return (2, "Dva para")
    if grupe[0] == 2:
        return (1, "Par")
    return (0, "Visoka karta")

poker_igre = {}

@tree.command(name="poker", description="Igraj poker")
@app_commands.describe(ulog="Koliko dinara ulazes")
async def poker(interaction: discord.Interaction, ulog: int):
    data = ucitaj()
    data, uid = get_igrac(data, interaction.user.id)

    if ulog <= 0:
        await interaction.response.send_message("❌ Ulog mora biti veći od 0!")
        return

    if data[uid]["balans"] < ulog:
        await interaction.response.send_message(
            f"❌ Nemaš dovoljno dinara! Tvoje stanje: **{data[uid]['balans']} dinara**"
        )
        return

    spil = napravi_poker_spil()
    igrac_karte = [spil.pop() for _ in range(5)]
    diler_karte = [spil.pop() for _ in range(5)]

    poker_igre[uid] = {
        "ulog": ulog,
        "igrac": igrac_karte,
        "diler": diler_karte,
        "spil": spil
    }

    sacuvaj(data)

    prikaz = " | ".join([f"{i+1}:{k}" for i, k in enumerate(igrac_karte)])
    await interaction.response.send_message(
        f"🃏 **Tvoje karte:**\n{prikaz}\n\n"
        f"Koje karte želiš da zameniš? Ukucaj **/zameni** i brojeve karata (npr. `/zameni 2 4`)\n"
        f"Ili **/zameni 0** ako nećeš da menjaš ništa!"
    )

@tree.command(name="zameni", description="Zameni karte u pokeru")
@app_commands.describe(karte="Brojevi karata za zamenu (1-5) ili 0 za bez zamene")
async def zameni(interaction: discord.Interaction, karte: str):
    uid = str(interaction.user.id)

    if uid not in poker_igre:
        await interaction.response.send_message("❌ Nisi u igri! Koristi /poker da počneš.")
        return

    igra = poker_igre[uid]

    if karte.strip() != "0":
        try:
            indeksi = [int(x)-1 for x in karte.split()]
            if any(i < 0 or i > 4 for i in indeksi):
                await interaction.response.send_message("❌ Brojevi karata moraju biti između 1 i 5!")
                return
            for i in indeksi:
                igra["igrac"][i] = igra["spil"].pop()
        except:
            await interaction.response.send_message("❌ Neispravan unos! Primer: `/zameni 1 3` ili `/zameni 0`")
            return

    igrac_ruka = oceni_ruku(igra["igrac"])
    diler_ruka = oceni_ruku(igra["diler"])

    data = ucitaj()
    data, uid2 = get_igrac(data, interaction.user.id)

    igrac_prikaz = " | ".join(igra["igrac"])
    diler_prikaz = " | ".join(igra["diler"])

    rezultat = (
        f"🃏 **Tvoje karte:** {igrac_prikaz}\n"
        f"🏆 **Tvoja ruka:** {igrac_ruka[1]}\n\n"
        f"🃏 **Dilerove karte:** {diler_prikaz}\n"
        f"🏆 **Dilerova ruka:** {diler_ruka[1]}\n\n"
    )

    if igrac_ruka[0] > diler_ruka[0]:
        dobitak = igra["ulog"] * 2
        data[uid2]["balans"] += igra["ulog"]
        data[uid2]["dobijeno_danas"] += dobitak
        rezultat += f"✅ Pobedio si! Dobitak: **{dobitak} dinara**\n"
    elif igrac_ruka[0] == diler_ruka[0]:
        rezultat += f"🤝 Nerešeno! Vraćamo ti ulog: **{igra['ulog']} dinara**\n"
    else:
        data[uid2]["balans"] -= igra["ulog"]
        rezultat += f"❌ Diler pobedio! Izgubio si **{igra['ulog']} dinara**\n"

    rezultat += f"💰 Novo stanje: **{data[uid2]['balans']} dinara**"

    sacuvaj(data)
    del poker_igre[uid]

    await interaction.response.send_message(rezultat)

import os

TOKEN = os.environ.get("TOKEN")
bot.run(TOKEN)
