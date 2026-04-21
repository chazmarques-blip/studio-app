"""Bible RAG — Passagens bíblicas em Português para BookFactory.

Phase 2 implementation: IDF-weighted retrieval over curated passages.
Interface compatible with future ChromaDB/pgvector swap.

To upgrade to vector RAG in the future:
  1. pip install chromadb sentence-transformers
  2. Build collection at import time using BIBLE_PASSAGES
  3. Replace search_bible_passages() internals — keep signature
"""
import re as _re
import math
import unicodedata


BIBLE_PASSAGES = {
    # Abraão narrative
    "genesis_12_1_3_ara": {
        "reference": "Gênesis 12:1-3",
        "translation": "Almeida Revista e Atualizada (ARA)",
        "theme": "Chamado de Abraão; promessa da grande nação",
        "keywords": ["abraão", "chamado", "promessa", "bênção", "nação"],
        "text": """Ora, disse o SENHOR a Abrão: Sai da tua terra, da tua parentela e da casa de teu pai e vai para a terra que te mostrarei;
de ti farei uma grande nação, e te abençoarei, e te engrandecerei o nome. Sê tu uma bênção!
Abençoarei os que te abençoarem e amaldiçoarei os que te amaldiçoarem; em ti serão benditas todas as famílias da terra.""",
    },
    "genesis_21_1_7_ara": {
        "reference": "Gênesis 21:1-7",
        "translation": "ARA",
        "theme": "Nascimento de Isaque; riso de Sara",
        "keywords": ["isaque", "sara", "nascimento", "velhice", "riso"],
        "text": """O SENHOR visitou a Sara, como lhe dissera, e lhe fez como lhe havia prometido. Sara concebeu e deu a Abraão um filho na sua velhice, ao tempo determinado, de que Deus lhe havia falado.
Ao filho que lhe nascera, que Sara lhe dera à luz, pôs Abraão o nome de Isaque.
E Abraão, ao nascer-lhe Isaque, seu filho, tinha cem anos.
Disse Sara: Deus me deu motivo de riso; e todo aquele que ouvir isso rir-se-á juntamente comigo.
E acrescentou: Quem teria dito a Abraão que Sara amamentaria um filho? Pois na sua velhice lhe dei um filho.""",
    },
    "genesis_22_1_14_ara": {
        "reference": "Gênesis 22:1-14",
        "translation": "ARA",
        "theme": "Sacrifício de Isaque; Deus provê o cordeiro; fé de Abraão",
        "keywords": ["abraão", "isaque", "sacrifício", "cordeiro", "moriá", "fé", "altar"],
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
        "translation": "ARA",
        "theme": "Bênção de Abraão; multiplicação da descendência",
        "keywords": ["abraão", "bênção", "descendência", "estrelas", "nações"],
        "text": """Do céu bradou pela segunda vez o Anjo do SENHOR a Abraão e disse:
Jurei por mim mesmo, diz o SENHOR, porquanto fizeste isto e não me negaste o teu único filho,
que deveras te abençoarei e certamente multiplicarei a tua descendência como as estrelas dos céus e como a areia na praia do mar; a tua descendência possuirá a cidade dos seus inimigos,
nela serão benditas todas as nações da terra, porquanto obedeceste à minha voz.""",
    },
    "hebreus_11_17_19_ara": {
        "reference": "Hebreus 11:17-19",
        "translation": "ARA",
        "theme": "Comentário do NT sobre a fé de Abraão",
        "keywords": ["fé", "abraão", "isaque", "ressurreição"],
        "text": """Pela fé, Abraão, quando posto à prova, ofereceu Isaque; sim, aquele que acolhera com alegria as promessas oferecia o seu unigênito,
a quem se tinha dito: Em Isaque será chamada a tua descendência;
porque considerou que Deus era poderoso até para o ressuscitar dentre os mortos, de onde também, figuradamente, o recobrou.""",
    },
    # Expanded — Creation & early chapters
    "genesis_1_1_5_ara": {
        "reference": "Gênesis 1:1-5",
        "translation": "ARA",
        "theme": "Criação — primeiro dia; luz e trevas",
        "keywords": ["criação", "céus", "terra", "luz", "trevas", "dia", "noite"],
        "text": """No princípio, criou Deus os céus e a terra.
A terra, porém, estava sem forma e vazia; havia trevas sobre a face do abismo, e o Espírito de Deus pairava por sobre as águas.
Disse Deus: Haja luz; e houve luz.
E viu Deus que a luz era boa; e fez separação entre a luz e as trevas.
Chamou Deus à luz Dia e às trevas, Noite. Houve tarde e manhã, o primeiro dia.""",
    },
    "genesis_1_26_31_ara": {
        "reference": "Gênesis 1:26-31",
        "translation": "ARA",
        "theme": "Criação do homem à imagem de Deus; sexto dia",
        "keywords": ["criação", "homem", "mulher", "imagem", "semelhança", "dominar"],
        "text": """Também disse Deus: Façamos o homem à nossa imagem, conforme a nossa semelhança; tenha ele domínio sobre os peixes do mar, sobre as aves dos céus, sobre os animais domésticos, sobre toda a terra e sobre todos os répteis que rastejam pela terra.
Criou Deus, pois, o homem à sua imagem, à imagem de Deus o criou; homem e mulher os criou.
E Deus os abençoou e lhes disse: Sede fecundos, multiplicai-vos, enchei a terra e sujeitai-a; dominai sobre os peixes do mar, sobre as aves dos céus e sobre todo animal que rasteja pela terra.
E disse Deus ainda: Eis que vos tenho dado todas as ervas que dão semente e se acham na superfície de toda a terra e todas as árvores em que há fruto que dê semente; ser-vos-ão para mantimento.
E a todos os animais da terra, e a todas as aves dos céus, e a todos os répteis da terra, em que há fôlego de vida, toda a erva verde lhes será para mantimento. E assim se fez.
Viu Deus tudo quanto fizera, e eis que era muito bom. Houve tarde e manhã, o sexto dia.""",
    },
    "genesis_3_1_7_ara": {
        "reference": "Gênesis 3:1-7",
        "translation": "ARA",
        "theme": "A queda — serpente, Eva e o fruto proibido",
        "keywords": ["adão", "eva", "serpente", "fruto", "queda", "jardim", "éden"],
        "text": """Ora, a serpente era o mais sagaz de todos os animais selváticos que o SENHOR Deus tinha feito. E esta disse à mulher: É assim que Deus disse: Não comereis de toda árvore do jardim?
Respondeu a mulher à serpente: Do fruto das árvores do jardim podemos comer,
mas do fruto da árvore que está no meio do jardim, disse Deus: Não comereis dele, nem nele tocareis, para que não morrais.
Então, a serpente disse à mulher: É certo que não morrereis.
Porque Deus sabe que no dia em que dele comerdes se vos abrirão os olhos e, como Deus, sereis conhecedores do bem e do mal.
Vendo a mulher que a árvore era boa para se comer, agradável aos olhos e árvore desejável para dar entendimento, tomou-lhe do fruto e comeu e deu também ao marido, e ele comeu.
Abriram-se, então, os olhos de ambos; e, percebendo que estavam nus, coseram folhas de figueira e fizeram cintas para si.""",
    },
    "genesis_6_13_22_ara": {
        "reference": "Gênesis 6:13-22",
        "translation": "ARA",
        "theme": "Noé — ordem para construir a arca",
        "keywords": ["noé", "arca", "dilúvio", "madeira", "animais", "aliança"],
        "text": """Então, disse Deus a Noé: Resolvi dar cabo de toda carne, porque a terra está cheia da violência dos homens; eis que os farei perecer juntamente com a terra.
Faze uma arca de madeira de cipreste; far-lhe-ás compartimentos e a calafetarás com betume por dentro e por fora.
Fá-la-ás deste modo: de trezentos côvados será o comprimento, de cinquenta, a largura e a altura, de trinta côvados.
À arca farás uma janela e a acabarás a um côvado do teto; a porta da arca colocarás do lado; far-lhe-ás andares, baixo, segundo e terceiro.
Porque eis que eu trago o dilúvio sobre a terra, para desfazer toda carne em que há fôlego de vida debaixo dos céus; tudo o que há na terra perecerá.
Mas contigo estabelecerei a minha aliança; entrarás na arca, tu e contigo teus filhos, e tua mulher, e as mulheres de teus filhos.
De tudo o que vive, de toda carne, dois de cada espécie, macho e fêmea, farás entrar na arca, para os conservares vivos contigo.""",
    },
    # New Testament key passages for book adaptations
    "lucas_2_1_7_ara": {
        "reference": "Lucas 2:1-7",
        "translation": "ARA",
        "theme": "Nascimento de Jesus em Belém",
        "keywords": ["jesus", "nascimento", "belém", "maria", "josé", "manjedoura"],
        "text": """Naqueles dias, foi publicado um decreto de César Augusto, convocando toda a população do império para o recenseamento.
Este, o primeiro, foi feito quando Quirino era governador da Síria.
Todos iam alistar-se, cada um à sua própria cidade.
José também subiu da Galileia, da cidade de Nazaré, para a Judéia, à cidade de Davi, chamada Belém, por ser ele da casa e família de Davi, a fim de alistar-se com Maria, sua esposa, que estava grávida.
Estando eles ali, aconteceu completarem-se-lhe os dias, e ela deu à luz o seu filho primogênito, enfaixou-o e o deitou numa manjedoura, porque não havia lugar para eles na hospedaria.""",
    },
    "mateus_5_3_12_ara": {
        "reference": "Mateus 5:3-12",
        "translation": "ARA",
        "theme": "Bem-aventuranças — Sermão do Monte",
        "keywords": ["bem-aventurança", "sermão", "monte", "reino", "jesus", "felicidade"],
        "text": """Bem-aventurados os humildes de espírito, porque deles é o reino dos céus.
Bem-aventurados os que choram, porque serão consolados.
Bem-aventurados os mansos, porque herdarão a terra.
Bem-aventurados os que têm fome e sede de justiça, porque serão fartos.
Bem-aventurados os misericordiosos, porque alcançarão misericórdia.
Bem-aventurados os limpos de coração, porque verão a Deus.
Bem-aventurados os pacificadores, porque serão chamados filhos de Deus.
Bem-aventurados os perseguidos por causa da justiça, porque deles é o reino dos céus.""",
    },
    # Exodus
    "exodo_3_1_6_ara": {
        "reference": "Êxodo 3:1-6",
        "translation": "ARA",
        "theme": "Moisés e a sarça ardente",
        "keywords": ["moisés", "sarça", "horebe", "deus", "fogo", "chamado"],
        "text": """Apascentava Moisés o rebanho de Jetro, seu sogro, sacerdote de Midiã; e, levando o rebanho para o lado ocidental do deserto, chegou a Horebe, o monte de Deus.
Apareceu-lhe o Anjo do SENHOR numa chama de fogo, no meio de uma sarça; Moisés olhou, e eis que a sarça ardia no fogo e não se consumia.
Então, disse consigo mesmo: Irei para lá e verei esta grande maravilha; por que a sarça não se queima?
Vendo o SENHOR que ele se voltava para ver, Deus, do meio da sarça, o chamou e disse: Moisés! Moisés! Ele respondeu: Eis-me aqui!
Disse Deus: Não te chegues para cá; tira as sandálias dos pés, porque o lugar em que estás é terra santa.
Disse mais: Eu sou o Deus de teu pai, o Deus de Abraão, o Deus de Isaque e o Deus de Jacó. Moisés escondeu o rosto, porque temeu olhar para Deus.""",
    },
    # Psalms
    "salmos_23_ara": {
        "reference": "Salmos 23",
        "translation": "ARA",
        "theme": "O Senhor é meu pastor",
        "keywords": ["salmo", "pastor", "senhor", "consolação", "sombras", "morte"],
        "text": """O SENHOR é o meu pastor; nada me faltará.
Ele me faz repousar em pastos verdejantes. Leva-me para junto das águas de descanso;
refrigera-me a alma. Guia-me pelas veredas da justiça por amor do seu nome.
Ainda que eu ande pelo vale da sombra da morte, não temerei mal nenhum, porque tu estás comigo; o teu bordão e o teu cajado me consolam.
Preparas-me uma mesa na presença dos meus adversários, unges-me a cabeça com óleo; o meu cálice transborda.
Bondade e misericórdia certamente me seguirão todos os dias da minha vida; e habitarei na Casa do SENHOR para todo o sempre.""",
    },
    # Daniel
    "daniel_6_16_23_ara": {
        "reference": "Daniel 6:16-23",
        "translation": "ARA",
        "theme": "Daniel na cova dos leões",
        "keywords": ["daniel", "leões", "cova", "dario", "anjo", "fé"],
        "text": """Então, o rei ordenou, e trouxeram Daniel e o lançaram na cova dos leões. Disse o rei a Daniel: O teu Deus, a quem tu continuamente serves, ele te livrará.
Foi trazida uma pedra e posta sobre a boca da cova; selou-a o rei com o seu próprio anel e com o anel dos seus grandes, para que nada se mudasse a respeito de Daniel.
Então, o rei se dirigiu para o seu palácio e passou a noite em jejum, e não deixou trazer à sua presença instrumentos de música; e fugiu dele o sono.
Pela manhã, ao amanhecer, levantou-se o rei e foi com pressa à cova dos leões. Chegando-se a ela, chamou por Daniel com voz triste e lhe disse: Daniel, servo do Deus vivo! Dar-se-ia o caso que o teu Deus, a quem tu continuamente serves, tenha podido livrar-te dos leões?
Então, Daniel falou ao rei: Ó rei, vive eternamente!
O meu Deus enviou o seu anjo e fechou a boca dos leões, para que não me fizessem dano, porque foi achada em mim inocência diante dele, e também contra ti, ó rei, não tenho cometido delito algum.
Então, o rei ficou muito alegre e mandou tirar a Daniel da cova; assim, foi retirado Daniel da cova, e nenhum dano se achou nele, porque crera no seu Deus.""",
    },
    # David
    "1samuel_17_45_50_ara": {
        "reference": "1 Samuel 17:45-50",
        "translation": "ARA",
        "theme": "Davi e Golias — vitória do pequeno sobre o gigante",
        "keywords": ["davi", "golias", "funda", "filisteu", "gigante", "pedra"],
        "text": """Davi, porém, disse ao filisteu: Tu vens contra mim com espada, e com lança, e com escudo; eu, porém, vou contra ti em nome do SENHOR dos Exércitos, o Deus dos exércitos de Israel, a quem tens afrontado.
Hoje mesmo, o SENHOR te entregará nas minhas mãos; ferir-te-ei, tirar-te-ei a cabeça e, ainda hoje, darei os cadáveres do arraial dos filisteus às aves do céu e às feras da terra; e toda a terra saberá que há Deus em Israel,
e sabe toda esta multidão que o SENHOR salva, não com espada, nem com lança; porque do SENHOR é a guerra, e ele vos entregará nas nossas mãos.
Aconteceu que, levantando-se o filisteu e aproximando-se para se opor a Davi, apressou-se este e correu ao combate, a encontrar-se com o filisteu.
E Davi, lançando a mão à bolsa, dela tomou uma pedra e com a funda lha atirou, e feriu o filisteu na testa; a pedra se lhe cravou na testa, e o filisteu caiu com o rosto em terra.
Assim, Davi, com uma funda e uma pedra, prevaleceu contra o filisteu; feriu-o e o matou. Davi, porém, não trazia espada na mão.""",
    },
}

# Pre-computed word frequency data for IDF scoring (done once on import)
_STOPWORDS = {
    "a", "o", "as", "os", "um", "uma", "de", "do", "da", "dos", "das",
    "e", "ou", "que", "se", "por", "para", "com", "em", "no", "na",
    "nos", "nas", "ao", "aos", "à", "às", "é", "são", "foi", "sua",
    "seu", "suas", "seus", "este", "esta", "isso", "mas", "já", "também",
    "como", "muito", "quando", "onde", "quem", "qual", "quais", "todos",
    "todas", "toda", "todo", "ser", "tem", "têm", "há", "tu", "eu", "ele",
    "ela", "nós", "vós", "ao", "me", "te", "lhe", "nos", "lhes", "se",
    "não", "sim",
}


def _normalize(s: str) -> str:
    """Remove accents + lowercase for matching."""
    return unicodedata.normalize("NFKD", s.lower()).encode("ascii", "ignore").decode()


def _tokenize(s: str) -> list:
    tokens = _re.findall(r'\w+', _normalize(s))
    return [t for t in tokens if t not in _STOPWORDS and len(t) > 1]


# Build IDF index at module load
def _build_index():
    docs = {}
    df = {}
    for key, p in BIBLE_PASSAGES.items():
        # Weight: keywords count 3x, theme 2x, reference 1x, text 1x
        tokens = (
            _tokenize(" ".join(p.get("keywords", []))) * 3
            + _tokenize(p.get("theme", "")) * 2
            + _tokenize(p.get("reference", ""))
            + _tokenize(p.get("text", ""))
        )
        docs[key] = tokens
        for tk in set(tokens):
            df[tk] = df.get(tk, 0) + 1
    N = len(docs)
    idf = {tk: math.log((N + 1) / (c + 0.5)) + 1 for tk, c in df.items()}
    return docs, idf

_DOCS, _IDF = _build_index()


def search_bible_passages(query: str, top_k: int = 5, min_score: float = 0.0) -> list:
    """Retrieve most relevant Bible passages using IDF-weighted term matching.

    Returns [{reference, translation, theme, text, score, key}, ...].

    This implementation is production-ready for the current corpus size (~15 passages).
    For 1000+ passages, swap internals to vector RAG (ChromaDB/pgvector):
      - Index passages at import time with sentence-transformers/all-MiniLM-L6-v2
      - Use cosine similarity for retrieval
      - Keep this function signature for backward compatibility
    """
    q_tokens = _tokenize(query)
    if not q_tokens:
        return []

    scores = {}
    for key, doc_tokens in _DOCS.items():
        # TF component: how often each query token appears in the doc
        tf = {}
        for tk in doc_tokens:
            tf[tk] = tf.get(tk, 0) + 1
        doc_len = max(1, len(doc_tokens))
        # Sum of tf-idf per query token present
        score = 0.0
        for qt in q_tokens:
            if qt in tf:
                score += (tf[qt] / doc_len) * _IDF.get(qt, 1.0)
        if score > min_score:
            scores[key] = score

    # Sort and return
    sorted_keys = sorted(scores.keys(), key=lambda k: -scores[k])[:top_k]
    results = []
    for k in sorted_keys:
        p = BIBLE_PASSAGES[k]
        results.append({
            "reference": p["reference"],
            "translation": p["translation"],
            "theme": p["theme"],
            "text": p["text"],
            "score": round(scores[k], 4),
            "key": k,
        })
    return results


def list_all_passages() -> list:
    """Return metadata for all available passages (for UI / debugging)."""
    return [
        {
            "key": key,
            "reference": p["reference"],
            "translation": p["translation"],
            "theme": p["theme"],
            "keywords": p.get("keywords", []),
        }
        for key, p in BIBLE_PASSAGES.items()
    ]


def get_corpus_stats() -> dict:
    """Stats about the RAG corpus."""
    total_chars = sum(len(p["text"]) for p in BIBLE_PASSAGES.values())
    return {
        "total_passages": len(BIBLE_PASSAGES),
        "total_characters": total_chars,
        "total_indexed_tokens": len(_IDF),
        "implementation": "idf_keyword_v2",
        "ready_for_vector_swap": True,
    }
