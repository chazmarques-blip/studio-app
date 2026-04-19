"""Bible RAG — Passagens bíblicas em Português para BookFactory.

MVP: dict em memória com passagens-chave. Interface compatível com ChromaDB/pgvector.
Fase 2: substituir por embeddings reais com ingestão completa.
"""
import re as _re


BIBLE_PASSAGES = {
    "genesis_22_1_14_ara": {
        "reference": "Gênesis 22:1-14",
        "translation": "Almeida Revista e Atualizada (ARA)",
        "theme": "Sacrifício de Isaque; Deus provê o cordeiro",
        "text": """Passado isto, pôs Deus Abraão à prova e lhe disse: Abraão! Ele respondeu: Eis-me aqui!
Acrescentou Deus: Toma teu filho, teu único filho, Isaque, a quem amas, e vai-te à terra de Moriá; oferece-o ali em holocausto, sobre uma das montanhas, que eu te mostrarei.
Levantou-se, pois, Abraão de madrugada, e, tendo preparado o seu jumento, tomou consigo dois dos seus servos e a Isaque, seu filho; rachou lenha para o holocausto e foi para o lugar que Deus lhe havia indicado.
Ao terceiro dia, erguendo Abraão os olhos, viu o lugar de longe.
Então, disse a seus servos: Esperai aqui com o jumento; eu e o rapaz iremos até lá e, havendo adorado, voltaremos para junto de vós.
Tomou Abraão a lenha do holocausto e a colocou sobre Isaque, seu filho; ele, porém, levava nas mãos o fogo e o cutelo. Assim, caminhavam ambos juntos.
Disse Isaque a Abraão, seu pai: Meu pai! Respondeu Abraão: Eis-me aqui, meu filho! Perguntou-lhe Isaque: Eis o fogo e a lenha, mas onde está o cordeiro para o holocausto?
Respondeu Abraão: Deus proverá para si, meu filho, o cordeiro para o holocausto; e seguiam ambos juntos.
Chegaram ao lugar que Deus lhe havia designado; ali edificou Abraão um altar, sobre ele dispôs a lenha, amarrou Isaque, seu filho, e o deitou no altar, em cima da lenha.
E, estendendo a mão, tomou o cutelo para imolar o filho.
Mas do céu lhe bradou o Anjo do SENHOR: Abraão! Abraão! Ele respondeu: Eis-me aqui!
Então, lhe disse: Não estendas a mão sobre o rapaz e nada lhe faças; pois agora sei que temes a Deus, porquanto não me negaste o filho, o teu único filho.
Tendo Abraão erguido os olhos, viu atrás de si um carneiro preso pelos chifres num mato; tomou Abraão o carneiro e o ofereceu em holocausto, em lugar de seu filho.
E pôs Abraão por nome àquele lugar — O SENHOR Proverá. Daí dizer-se até ao dia de hoje: No monte do SENHOR se proverá.""",
    },
    "genesis_22_15_18_ara": {
        "reference": "Gênesis 22:15-18",
        "translation": "Almeida Revista e Atualizada (ARA)",
        "theme": "Bênção de Abraão",
        "text": """Do céu bradou pela segunda vez o Anjo do SENHOR a Abraão e disse:
Jurei por mim mesmo, diz o SENHOR, porquanto fizeste isto e não me negaste o teu único filho,
que deveras te abençoarei e certamente multiplicarei a tua descendência como as estrelas dos céus e como a areia na praia do mar; a tua descendência possuirá a cidade dos seus inimigos,
nela serão benditas todas as nações da terra, porquanto obedeceste à minha voz.""",
    },
    "hebreus_11_17_19_ara": {
        "reference": "Hebreus 11:17-19",
        "translation": "Almeida Revista e Atualizada (ARA)",
        "theme": "Comentário NT sobre a fé de Abraão",
        "text": """Pela fé, Abraão, quando posto à prova, ofereceu Isaque; sim, aquele que acolhera com alegria as promessas oferecia o seu unigênito,
a quem se tinha dito: Em Isaque será chamada a tua descendência;
porque considerou que Deus era poderoso até para o ressuscitar dentre os mortos, de onde também, figuradamente, o recobrou.""",
    },
    "genesis_12_1_3_ara": {
        "reference": "Gênesis 12:1-3",
        "translation": "ARA",
        "theme": "Chamado de Abraão",
        "text": """Ora, disse o SENHOR a Abrão: Sai da tua terra, da tua parentela e da casa de teu pai e vai para a terra que te mostrarei;
de ti farei uma grande nação, e te abençoarei, e te engrandecerei o nome. Sê tu uma bênção!
Abençoarei os que te abençoarem e amaldiçoarei os que te amaldiçoarem; em ti serão benditas todas as famílias da terra.""",
    },
    "genesis_21_1_7_ara": {
        "reference": "Gênesis 21:1-7",
        "translation": "ARA",
        "theme": "Nascimento de Isaque",
        "text": """O SENHOR visitou a Sara, como lhe dissera, e lhe fez como lhe havia prometido. Sara concebeu e deu a Abraão um filho na sua velhice, ao tempo determinado, de que Deus lhe havia falado.
Ao filho que lhe nascera, que Sara lhe dera à luz, pôs Abraão o nome de Isaque.
E Abraão, ao nascer-lhe Isaque, seu filho, tinha cem anos.
Disse Sara: Deus me deu motivo de riso; e todo aquele que ouvir isso rir-se-á juntamente comigo.
E acrescentou: Quem teria dito a Abraão que Sara amamentaria um filho? Pois na sua velhice lhe dei um filho.""",
    },
}


def _normalize(s: str) -> str:
    """Remove accents + lowercase for matching."""
    import unicodedata
    return unicodedata.normalize("NFKD", s.lower()).encode("ascii", "ignore").decode()


def search_bible_passages(query: str, top_k: int = 5) -> list:
    """Naive keyword search over Bible passages.

    Returns [{reference, translation, theme, text, score}, ...].
    Replace with real vector retrieval in Phase 2 without changing caller code.
    """
    q_norm = _normalize(query)
    q_words = set(_re.findall(r'\w+', q_norm))
    if not q_words:
        return []

    results = []
    for key, p in BIBLE_PASSAGES.items():
        haystack = _normalize(f"{p['reference']} {p['theme']} {p['text']}")
        text_words = set(_re.findall(r'\w+', haystack))
        overlap = len(q_words & text_words)
        score = overlap / max(1, len(q_words))
        if score > 0 or any(k in haystack for k in q_norm.split()):
            results.append({**p, "score": score, "key": key})

    results.sort(key=lambda x: -x["score"])
    return results[:top_k]
