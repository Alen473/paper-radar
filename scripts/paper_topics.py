"""Classify the feed from article metadata without requiring an API key."""

from __future__ import annotations

import re


_DASHES = str.maketrans("‐‑‒–—−", "------")

# These are common literal matches for biological words in unrelated fields.
_TECHNICAL_USES = re.compile(
    r"\b(?:(?:solar|photovoltaic|fuel|unit|battery|memory|electrochemical|"
    r"electroly[tz]\w*|perovskite|convection|anvil|pouch|coin|full|half|"
    r"symmetric|electrode|tandem)[ -]cells?|"
    r"cells? for (?:energy storage|electrolysis)|cell[ -]level energy|"
    r"(?:nuclear|power|industrial|chemical|desalination|manufacturing)[ -]plants?|"
    r"(?:artificial|deep|convolutional|recurrent|graph)[ -]neural networks?|"
    r"(?:evolutionary|genetic)[ -](?:algorithms?|optim[iz]\w*)|"
    r"immune to|(?:fault|defect|equipment)[ -]diagnos\w*)\b",
    re.IGNORECASE,
)

# Biology, medicine, ecology, and technology explicitly applied to them.
_BIOLOGY = re.compile(
    r"""
    \b(?:
        biolog\w* | biomedic\w* | biocompatib\w* | biomater\w* | biomimetic\w*
        | bioinspir\w* | biodegrad\w* | biosens\w* | biosynth\w* | biofilm\w* | bioimag\w*
        | bioinformatic\w* | biotechnolog\w* | biogeochem\w* | biomark\w*
        | organism\w* | eukary\w* | prokary\w* | bacteri\w* | microb\w*
        | archae(?:a|on)\w* | fung(?:al|i|us|icide)\w* | vir(?:us(?:es)?|al)
        | pathogen\w* | parasit(?:es?|ism|oid\w*|olog\w*) | yeast\w* | alga(?:e|l)?
        | animals? | mammals? | vertebrates? | invertebrates? | amphibians?
        | reptiles? | birds? | fishes | fish | insects? | mice | mouse | rodents?
        | primates? | drosophila | arabidopsis | zebrafish | nematodes?
        | plants? | crops? | pollen | pollinat\w* | photosynth\w* | chlorophyll
        | herbivor\w* | predator\w* | prey | livestock | aquaculture
        | ecolog\w* | ecosystems? | biodivers\w* | habitats? | vegetat\w* | corals?
        | deforestation | forests? | soil[ -]respiration | phytoplankton | plankton
        | fossilized | palaeo(?:ntolog|biolog)\w* | paleo(?:ntolog|biolog)\w*
        | phylogenom\w* | phylogeograph\w* | speciation[ -]events? | introgression
        | taxon\w* | interspecific | species[ -]richness | ortholog\w* | paralog\w*
        | cells? | cell(?:ular|ulose) | organoids? | organelles? | tissues?
        | embry\w* | epitheli\w* | endothel\w* | chondro\w* | cartilag\w* | bones? | skeletal | osteo\w*
        | fibroblast\w* | collagen\w* | muscles? | skin | wounds? | in[ -]vivo
        | in[ -]vitro | brain\w* | neuro(?!morphic)\w* | neurons? | synap\w*
        | cognit\w* | hippocamp\w* | neural | cerebr\w* | cortical | psycholog\w*
        | blood | cardiac | cardiovascular | pulmonary | lung\w* | hepatic
        | livers? | kidneys? | (?:sub)?retin\w* | dental | vascular | gastrointestinal
        | protein\w* | peptides? | enzymes? | enzymatic\w* | antibodies
        | antibody | amino[ -]acids? | lipids? | glycans? | receptors?
        | nucleic[ -]acids? | dna | (?:m|mi|sc|sn)?rna | genes? | genetic\w*
        | genom\w* | epigen\w* | transcriptom\w* | proteom\w* | chromatin | chromosom\w*
        | crispr | ribosom\w* | chloroplast\w* | mitochondri\w* | metabol\w*
        | medic(?:al|ine|inal) | clinic(?:al|ally|s)? | patients? | diseases?
        | implants? | prosthe\w* | blindness | ophthalm\w* | oncolog\w*
        | therap\w* | pharmac\w* | drug\w*
        | anti(?:biotic|microbial)\w* | vaccin\w* | infection\w* | epidemic\w*
        | immun\w* | inflammation | inflammatory | cancer\w* | tumou?r\w*
        | carcinom\w* | diabet\w* | obes\w* | arthrit\w* | syndrome\w*
        | physiolog\w* | epidemiolog\w* | toxicolog\w* | (?:human|public|global)[ -]health
        | mortality | morbidity | reproductive | reproduction
    )\b
    """,
    re.IGNORECASE | re.VERBOSE,
)

# Positive evidence of another field. General methods such as "simulation",
# "microscopy", and "machine learning" are deliberately insufficient.
_OTHER_FIELDS = re.compile(
    r"""
    \b(?:
        quantum | qubits? | rydberg | astrophys\w* | astronom\w* | cosmolog\w*
        | galact\w* | galax(?:y|ies) | exoplanet\w* | planetar\w* | stellar
        | asteroids? | supernov\w* | quasars? | (?:early|infant|observable)[ -]universe
        | black[ -]holes? | dark[ -](?:matter|energy) | neutron[ -]stars?
        | gravitational[ -]waves? | star[ -]formation | magnetospher\w*
        | magnetosheath | solar[ -](?:wind|flares?|cells?|energy|fuel)
        | hadrons? | baryon\w* | neutrinos? | particle[ -]physics | relativity | nuclear[ -]fusion
        | superconduct\w* | semiconduct\w* | ferromagnet\w* | antiferromagnet\w*
        | altermagnet\w* | ferroelectr\w* | magnetoresistan\w* | spintronic\w*
        | phonon\w* | photonic\w* | waveguid\w* | metamaterial\w* | topological[ -]insulat\w*
        | magnon\w* | polaritons? | spin[ -](?:glass\w*|peltier|seebeck) | superfluid\w*
        | moir[eé] | band[ -]?gaps? | electronic[ -](?:band|structure|devices?)
        | lithograph\w* | transistors? | optoelectro\w* | optomechan\w*
        | dielectr\w* | photodiod\w* | terahertz | electrochrom\w*
        | (?:electronic|excited)[ -]ground[ -]states? | thermal[ -]hall
        | perovskit\w* | photovoltaic\w* | graphene | mxenes? | carbon[ -]nanotubes?
        | electrocatal\w* | photocatal\w* | thermoelectric\w* | supercapacitor\w*
        | batter(?:y|ies) | fuel[ -]cells? | (?:lithium|sodium|zinc)[ -]ion
        | (?:hydrogen|oxygen)[ -](?:evolution|reduction)[ -]reaction
        | electrolys\w* | electrosynth\w* | electrolytes? | hydrogen[ -](?:production|storage|permeation)
        | carbon[ -](?:capture|sequestration) | metal[ -]organic[ -]frameworks?
        | (?:ring[ -]opening|supramolecular)[ -](?:co)?polymerization
        | organometallic\w* | (?:asymmetric|enantioselective|heterogeneous)[ -]catalys\w*
        | organic[ -]synthesis | chemical[ -]bond\w* | coordination[ -]chemistry
        | hydroformylation | photochem\w* | oil[ -]wells? | hydrocarbons?
        | electric[ -]charge | (?:plastic|polymer)[ -](?:waste|upcycling)
        | nanoindentation | alloy\w* | grain[ -](?:refinement|boundaries?) | dislocation[ -]motion
        | geophys\w* | (?:a)?seism\w* | earthquakes? | tecton\w* | volcan\w* | magmat\w*
        | bedrock | mantle[ -](?:convection|wedge|transition) | lithospher\w* | subduction
        | silicate[ -]weathering | deep[ -]earth
        | glacia\w* | cryospher\w* | pala?eoclimat\w* | aerosol\w*
        | ocean[ -](?:circulation|ventilation) | atmospheric[ -](?:circulation|rivers?)
        | (?:flood|landslide)[ -](?:hazards?|risks?) | ice[ -](?:sheets?|cores?|shel(?:f|ves))
        | sea[ -]ice | el[ -]ni[nñ]o | cumulus | monsoons? | walker[ -]circulation
        | heatwaves? | weather[ -](?:models?|forecast\w*) | typhoons? | hurricanes?
        | geomorpholog\w* | sediment[ -]transport | carbonate[ -]weathering
        | cryptograph\w* | wireless[ -](?:communication|networks?)
        | autonomous[ -]vehicles? | self[ -]driving[ -]cars? | robot\w* | ai[ -]agents?
        | recommender[ -]systems? | large[ -]language[ -]models? | computer[ -]vision
        | computer[ -]science | digital[ -]comput\w* | formal[ -]proofs?
        | differential[ -]privacy | llm[ -]multi[ -]agent
        | combinatorial[ -]optim\w* | game[ -]theory | graph[ -]theory | prime[ -]numbers?
        | (?:partial|fractional)[ -]differential[ -]equations? | navier[ -]stokes
        | random[ -]matri(?:x|ces) | arithmetic[ -]geometry
        | elections? | voting[ -](?:behavio[u]r|patterns?) | politic\w* | democracy
        | tariff\w* | policing | antislavery | congress | social[ -]science
        | financial[ -]markets? | economic[ -](?:growth|policy|inequality)
        | immigration | immigrants? | language[ -]use | syntactic[ -]change
    )\b
    """,
    re.IGNORECASE | re.VERBOSE,
)

# "Evolution" also describes changes over time in chemistry and physics.
_OTHER_EVOLUTION_USES = re.compile(
    r"\b(?:"
    r"(?:time|temporal|spatiotemporal|structural|conformational|phase|"
    r"electronic|thermal|strain|hydrogen|oxygen|gas|chlorine|carrier)[ -]evolution|"
    r"evolutionary[ -](?:algorithms?|optim\w*|comput\w*|search|robotics)"
    r")\b",
    re.IGNORECASE,
)

_EVOLUTION = re.compile(
    r"""
    \b(?:
        phylogen\w* | phylogeograph\w* | phylodynamic\w* | evo[ -]?devo
        | (?:macro|micro|co)[ -]?evolution\w* | paleogenom\w* | palaeogenom\w*
        | introgression | genetic[ -]drift | gene[ -]flow | hybrid[ -]zones?
        | reproductive[ -]isolation | ancestral[ -](?:state|sequence)[ -]reconstruction
        | (?:natural|sexual|purifying|balancing)[ -]selection | selective[ -]sweeps?
        | population[ -](?:genetics|genomics) | species[ -](?:divergence|diversification)
        | local[ -]adaptation | adaptive[ -](?:radiation|divergence)
        | (?:ecological|allopatric|sympatric|parapatric)[ -]speciation
        | (?:adaptive|biological|convergent|divergent|directed|experimental|genetic|
            molecular|neutral|parallel|regulatory|repeated|viral)[ -]evolution
        | evolutionary[ -](?:adaptation|change|conservation|constraint\w*|divergence|
            dynamics|history|innovations?|origins?|process\w*|relatedness|trajector\w*|
            transitions?|trade[ -]?offs?)
        | comparative[ -]genomics | cross[ -]species[ -](?:comparison|conservation|divergence)
    )\b
    """,
    re.IGNORECASE | re.VERBOSE,
)

_EVOLUTION_TITLE = re.compile(r"\b(?:evolution(?:ary|arily)?|speciation|domestication)\b", re.IGNORECASE)
_NON_BIOLOGICAL_EVOLUTION_TITLE = re.compile(
    r"\b(?:robots?|robotics|evolution of (?:syntax|programming languages?|the earth['’]s surface)|"
    r"(?:aqueous|chemical|metal|ionic|isotopic)[ -]speciation)\b",
    re.IGNORECASE,
)


def _normalize(text: str) -> str:
    return " ".join(text.translate(_DASHES).split())


def _has_biology(text: str) -> bool:
    return _BIOLOGY.search(_TECHNICAL_USES.sub(" ", text)) is not None


def is_clearly_outside_biology(title: str, abstract: str) -> bool:
    """Keep ambiguous records and papers with a biological application."""
    title, abstract = _normalize(title), _normalize(abstract)
    # Evidence in a title is strong. For abstracts, require two distinct
    # signals so a single passing reference does not remove a record.
    outside = _OTHER_FIELDS.search(title) or len({
        match.group().casefold() for match in _OTHER_FIELDS.finditer(abstract)
    }) >= 2
    return bool(outside) and not _has_biology(f"{title} {abstract}")


def is_evolutionary(title: str, abstract: str) -> bool:
    title, abstract = _normalize(title), _normalize(abstract)
    text = f"{title} {abstract}"
    if _NON_BIOLOGICAL_EVOLUTION_TITLE.search(title) or not _has_biology(text):
        return False
    title = _OTHER_EVOLUTION_USES.sub(" ", title)
    abstract = _OTHER_EVOLUTION_USES.sub(" ", abstract)
    return bool(_EVOLUTION_TITLE.search(title) or _EVOLUTION.search(f"{title} {abstract}"))
