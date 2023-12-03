"""
This file contains a list of languages and labels which can be set
on captions for files on Wikimedia Commons.

There are two variables in this file.

== SUPPORTED_LANGUAGES ==

I got this list by opening the language picker in my browser, and running
the following JS in my browser dev tools:

    var languages =
      Array.from(document.querySelectorAll('.uls-language-list li'))
        .map(function(listElem) {
          const dataCode = listElem.getAttribute("data-code");
          const title = listElem.getAttribute("title");
          return [dataCode, title];
        });

    console.log(JSON.stringify(Array.from(new Set(languages))));

Having this list allows us to build a UI similar to the one on
Wikimedia Commons.

We use the wbsetlabel API to set file captions, and its documentation has
a list of supported languages [1], but this list doesn't match what's
allowed through the Wikimedia UI.  Two examples:

*   Wikimedia allows you to set languages in Efịk (efi), but that's not
    a language on that list.
*   That list mentions ``bqz``, which I think corresponds to "Bakaka",
    but you can't create captions with that language on Wikimedia [2][3].

It seems like you can put any ID in the "language" field of wbsetlabel,
but it may not render properly in the Wikimedia web UI.  e.g. if I use the
API to create a caption with language ``bqz``, that same ID shows in the UI.

[1]: https://www.wikidata.org/w/api.php?action=help&modules=wbsetlabel#wbsetlabel:language
[2]: https://en.wikipedia.org/wiki/Manenguba_languages
[3]: https://iso639-3.sil.org/code/bqz

== LANGUAGE_FREQUENCIES ==

This is a tally of the languages used in a sample of ~45k captions, taken
from a Wikimedia Commons snapshot.  It's not meant to be wholly indicative,
more to give us a way to loosely order language results.

"""

import collections
from typing import TypedDict


class LanguageMatch(TypedDict):
    id: str
    label: str
    match_text: str | None


def order_language_list(query: str, results: dict[str, str]) -> list[LanguageMatch]:
    """
    Given a list of matching languages returned from the Wikimedia
    ``languagesearch`` API, sort them into an ordered list of results
    to show in a language picker.

    This API allows us to search by the different labels for a language,
    e.g. you could search "español" or "spanish" and get the same result.

    When a user types in a query, we want to show them a list of languages
    which is useful, and where it's somewhat obvious to them why that
    list has been selected.
    """
    matching_languages: list[LanguageMatch] = []

    # First we filter for languages which can be used for captions on
    # WMC files.
    #
    # e.g. the languagesearch API can return an "en-simple" language,
    # which is "Simple English", but you can't create captions in that
    # language, so we don't want it here.
    for lang_id, match_text in results.items():
        try:
            label = SUPPORTED_LANGUAGES[lang_id]
        except KeyError:
            continue

        if match_text.lower() == label.lower() or query.lower() in label.lower():
            matching_languages.append(
                {"id": lang_id, "label": label, "match_text": None}
            )
        else:
            matching_languages.append(
                {"id": lang_id, "label": label, "match_text": match_text}
            )

    # Every language has a "canonical" label (usually how it's named in
    # itself) and then alternative labels in other languages.
    #
    # Two examples:
    #
    #   * the canonical label for Danish is "dansk", but it's also
    #     known as "deens" (in Dutch) or "kideni" (in Swahili)
    #   * the canonical label for German is "deutsch", but it's also
    #     known as "allemand" (in French) or "tedesca" (in Italian)
    #
    # The Wikimedia API will search across all these fields, so that
    # you could find Danish by searching for "dansk" or "deens".
    #
    # We want to prioritise matches in the canonical label over the
    # alternative labels.  e.g. if you search for "de", we should
    # boost "deutsch" over "deens".
    #
    # After boosting for matches in the canonical label, we sort by
    # descending frequency, so the most widely-used languages float
    # to the top.
    #
    # This gives priority to people typing a language in its native name,
    # and should make the results somewhat explicable.
    has_label_match = [
        m for m in matching_languages if query.lower() in m["label"].lower()
    ]
    no_label_match = [
        m for m in matching_languages if query.lower() not in m["label"].lower()
    ]

    assert len(has_label_match + no_label_match) == len(matching_languages)

    has_label_match.sort(
        key=lambda m: LANGUAGE_FREQUENCIES.get(m["id"], 0), reverse=True
    )
    no_label_match.sort(
        key=lambda m: LANGUAGE_FREQUENCIES.get(m["id"], 0), reverse=True
    )

    return has_label_match + no_label_match


def top_n_languages(n: int) -> list[tuple[str, str]]:
    """
    Returns a list of tuples (lang ID, lang name) for the top N languages,
    sorted by frequency.
    """
    result = [
        (lang_id, SUPPORTED_LANGUAGES[lang_id])
        for lang_id, _ in LANGUAGE_FREQUENCIES.most_common(n)
    ]

    assert all(lang_id in SUPPORTED_LANGUAGES for lang_id, _ in result)

    return result


SUPPORTED_LANGUAGES = dict(
    [
        ["en", "English"],
        ["es", "español"],
        ["es-formal", "español (formal)"],
        ["eo", "Esperanto"],
        ["fr", "français"],
        ["io", "Ido"],
        ["ia", "interlingua"],
        ["ie", "Interlingue"],
        ["avk", "Kotava"],
        ["lfn", "Lingua Franca Nova"],
        ["jbo", "la .lojban."],
        ["nov", "Novial"],
        ["pt", "português"],
        ["simple", "Simple English"],
        ["tok", "toki pona"],
        ["vo", "Volapük"],
        ["zh", "中文"],
        ["zh-hans", "中文（简体）"],
        ["zh-hant", "中文（繁體）"],
        ["en-us", "American English"],
        ["atj", "Atikamekw"],
        ["gn", "Avañe'ẽ"],
        ["ay", "Aymar aru"],
        ["en-ca", "Canadian English"],
        ["cho", "Chahta anumpa"],
        ["sei", "Cmique Itom"],
        ["pdc", "Deitsch"],
        ["nv", "Diné bizaad"],
        ["es", "español"],
        ["es-formal", "español (formal)"],
        ["es-419", "español de América Latina"],
        ["fr", "français"],
        ["frc", "français cadien"],
        ["haw", "Hawaiʻi"],
        ["hrx", "Hunsrik"],
        ["ike-latn", "inuktitut"],
        ["ik", "Iñupiatun"],
        ["quc", "Qatzijob\\ʼal"],
        ["kl", "kalaallisut"],
        ["cak", "Kaqchikel"],
        ["ht", "Kreyòl ayisyen"],
        ["gcr", "kriyòl gwiyannen"],
        ["lad", "Ladino"],
        ["arn", "mapudungun"],
        ["srq", "mbia cheë"],
        ["mus", "Mvskoke"],
        ["nl", "Nederlands"],
        ["nl-informal", "Nederlands (informeel)"],
        ["yrl", "Nhẽẽgatú"],
        ["nah", "Nāhuatl"],
        ["ojb", "Ojibwemowin"],
        ["pap-aw", "Papiamento"],
        ["pap", "Papiamentu"],
        ["jam", "Patois"],
        ["pdt", "Plautdietsch"],
        ["pt", "português"],
        ["pt-br", "português do Brasil"],
        ["qug", "Runa shimi"],
        ["qu", "Runa Simi"],
        ["srn", "Sranantongo"],
        ["chy", "Tsetsêhestâhese"],
        ["vec", "vèneto"],
        ["guc", "wayuunaiki"],
        ["yi", "ייִדיש"],
        ["ike-cans", "ᐃᓄᒃᑎᑐᑦ"],
        ["iu", "ᐃᓄᒃᑎᑐᑦ / inuktitut"],
        ["cr", "Nēhiyawēwin / ᓀᐦᐃᔭᐍᐏᐣ"],
        ["chr", "ᏣᎳᎩ"],
        ["ase", "American sign language"],
        ["kk-arab", "قازاقشا (تٴوتە)"],
        ["kk-cn", "قازاقشا (جۇنگو)"],
        ["ku-arab", "كوردي (عەرەبی)"],
        ["ota", "لسان عثمانى"],
        ["av", "авар"],
        ["ady", "адыгабзэ"],
        ["ady-cyrl", "адыгабзэ"],
        ["kbd", "адыгэбзэ"],
        ["kbd-cyrl", "адыгэбзэ"],
        ["alt", "алтай тил"],
        ["ab", "аԥсшәа"],
        ["ba", "башҡортса"],
        ["be", "беларуская"],
        ["be-tarask", "беларуская (тарашкевіца)"],
        ["be-x-old", "беларуская (тарашкевіца)"],
        ["bg", "български"],
        ["ruq", "Vlăheşte"],
        ["ruq-cyrl", "Влахесте"],
        ["inh", "гӀалгӀай"],
        ["os", "ирон"],
        ["kv", "коми"],
        ["krc", "къарачай-малкъар"],
        ["kum", "къумукъ"],
        ["crh-cyrl", "къырымтатарджа (Кирилл)"],
        ["mrj", "кырык мары"],
        ["sjd", "кӣллт са̄мь кӣлл"],
        ["lbe", "лакку"],
        ["lez", "лезги"],
        ["mk", "македонски"],
        ["mdf", "мокшень"],
        ["mo", "молдовеняскэ"],
        ["nog", "ногайша"],
        ["ce", "нохчийн"],
        ["mhr", "олык марий"],
        ["koi", "перем коми"],
        ["rue", "русиньскый"],
        ["rsk", "руски"],
        ["ru", "русский"],
        ["sah", "саха тыла"],
        ["sty", "себертатар"],
        ["cu", "словѣньскъ / ⰔⰎⰑⰂⰡⰐⰠⰔⰍⰟ"],
        ["sr", "српски / srpski"],
        ["sr-ec", "српски (ћирилица)"],
        ["sh-cyrl", "српскохрватски (ћирилица)"],
        ["tt", "татарча / tatarça"],
        ["tt-cyrl", "татарча"],
        ["tly-cyrl", "толыши"],
        ["udm", "удмурт"],
        ["uk", "українська"],
        ["xal", "хальмг"],
        ["cv", "чӑвашла"],
        ["myv", "эрзянь"],
        ["kk", "қазақша"],
        ["kk-cyrl", "қазақша (кирил)"],
        ["kk-kz", "қазақша (Қазақстан)"],
        ["el", "Ελληνικά"],
        ["pnt", "Ποντιακά"],
        ["grc", "Ἀρχαία ἑλληνικὴ"],
        ["als", "Alemannisch"],
        ["gsw", "Alemannisch"],
        ["smn", "anarâškielâ"],
        ["an", "aragonés"],
        ["roa-rup", "armãneashti"],
        ["rup", "armãneashti"],
        ["frp", "arpetan"],
        ["ast", "asturianu"],
        ["az", "azərbaycanca"],
        ["sje", "bidumsámegiella"],
        ["bar", "Boarisch"],
        ["bs", "bosanski"],
        ["br", "brezhoneg"],
        ["en-gb", "British English"],
        ["ca", "català"],
        ["co", "corsu"],
        ["cy", "Cymraeg"],
        ["da", "dansk"],
        ["se", "davvisámegiella"],
        ["se-no", "davvisámegiella (Norgga bealde)"],
        ["se-se", "davvisámegiella (Ruoŧa bealde)"],
        ["se-fi", "davvisámegiella (Suoma bealde)"],
        ["pdc", "Deitsch"],
        ["de", "Deutsch"],
        ["de-formal", "Deutsch (Sie-Form)"],
        ["dsb", "dolnoserbski"],
        ["et", "eesti"],
        ["egl", "Emiliàn"],
        ["eml", "emiliàn e rumagnòl"],
        ["es", "español"],
        ["es-formal", "español (formal)"],
        ["ext", "estremeñu"],
        ["eu", "euskara"],
        ["fr", "français"],
        ["fy", "Frysk"],
        ["fur", "furlan"],
        ["fo", "føroyskt"],
        ["ga", "Gaeilge"],
        ["gv", "Gaelg"],
        ["gag", "Gagauz"],
        ["gl", "galego"],
        ["aln", "Gegë"],
        ["gd", "Gàidhlig"],
        ["hsb", "hornjoserbsce"],
        ["hr", "hrvatski"],
        ["it", "italiano"],
        ["smj", "julevsámegiella"],
        ["jut", "jysk"],
        ["rmf", "kaalengo tšimb"],
        ["kl", "kalaallisut"],
        ["krl", "karjal"],
        ["csb", "kaszëbsczi"],
        ["kw", "kernowek"],
        ["ku", "kurdî"],
        ["ku-latn", "kurdî (latînî)"],
        ["fkv", "kvääni"],
        ["kiu", "Kırmancki"],
        ["lld", "Ladin"],
        ["lad", "Ladino"],
        ["ltg", "latgaļu"],
        ["la", "Latina"],
        ["lv", "latviešu"],
        ["lzz", "Lazuri"],
        ["lt", "lietuvių"],
        ["lij", "Ligure"],
        ["li", "Limburgs"],
        ["olo", "livvinkarjala"],
        ["lmo", "lombard"],
        ["lb", "Lëtzebuergesch"],
        ["liv", "Līvõ kēļ"],
        ["hu", "magyar"],
        ["hu-formal", "magyar (formal)"],
        ["vmf", "Mainfränkisch"],
        ["mt", "Malti"],
        ["fit", "meänkieli"],
        ["mwl", "Mirandés"],
        ["nap", "Napulitano"],
        ["nl", "Nederlands"],
        ["nl-informal", "Nederlands (informeel)"],
        ["nds-nl", "Nedersaksies"],
        ["frr", "Nordfriisk"],
        ["no", "norsk"],
        ["nb", "norsk bokmål"],
        ["nn", "norsk nynorsk"],
        ["nrm", "Nouormand"],
        ["sms", "nuõrttsääʹmǩiõll"],
        ["oc", "occitan"],
        ["pcd", "Picard"],
        ["pms", "Piemontèis"],
        ["nds", "Plattdüütsch"],
        ["pdt", "Plautdietsch"],
        ["pl", "polski"],
        ["pt", "português"],
        ["prg", "prūsiskan"],
        ["pfl", "Pälzisch"],
        ["kk-latn", "qazaqşa (latın)"],
        ["kk-tr", "qazaqşa (Türkïya)"],
        ["crh", "qırımtatarca"],
        ["crh-latn", "qırımtatarca (Latin)"],
        ["ksh", "Ripoarisch"],
        ["rmy", "romani čhib"],
        ["rmc", "romaňi čhib"],
        ["ro", "română"],
        ["rgn", "Rumagnôl"],
        ["rm", "rumantsch"],
        ["sc", "sardu"],
        ["sro", "sardu campidanesu"],
        ["sdc", "Sassaresu"],
        ["sli", "Schläsch"],
        ["de-ch", "Schweizer Hochdeutsch"],
        ["sco", "Scots"],
        ["stq", "Seeltersk"],
        ["sq", "shqip"],
        ["scn", "sicilianu"],
        ["sk", "slovenčina"],
        ["sl", "slovenščina"],
        ["srn", "Sranantongo"],
        ["sr-el", "srpski (latinica)"],
        ["sh", "srpskohrvatski / српскохрватски"],
        ["sh-latn", "srpskohrvatski (latinica)"],
        ["fi", "suomi"],
        ["sv", "svenska"],
        ["kab", "Taqbaylit"],
        ["roa-tara", "tarandíne"],
        ["tt-latn", "tatarça"],
        ["crh-ro", "tatarşa"],
        ["tly", "tolışi"],
        ["tr", "Türkçe"],
        ["sju", "ubmejesámiengiälla"],
        ["vot", "Vaďďa"],
        ["vep", "vepsän kel’"],
        ["ruq-latn", "Vlăheşte"],
        ["vec", "vèneto"],
        ["fiu-vro", "võro"],
        ["vro", "võro"],
        ["wa", "walon"],
        ["vls", "West-Vlams"],
        ["diq", "Zazaki"],
        ["zea", "Zeêuws"],
        ["sma", "åarjelsaemien"],
        ["ang", "Ænglisc"],
        ["is", "íslenska"],
        ["de-at", "Österreichisches Deutsch"],
        ["cs", "čeština"],
        ["szl", "ślůnski"],
        ["bat-smg", "žemaitėška"],
        ["sgs", "žemaitėška"],
        ["got", "𐌲𐌿𐍄𐌹𐍃𐌺"],
        ["yi", "ייִדיש"],
        ["hyw", "Արեւմտահայերէն"],
        ["hy", "հայերեն"],
        ["xmf", "მარგალური"],
        ["ka", "ქართული"],
        ["ur", "اردو"],
        ["ary", "الدارجة"],
        ["ar", "العربية"],
        ["bqi", "بختیاری"],
        ["azb", "تۆرکجه"],
        ["arq", "جازايرية"],
        ["bcc", "جهلسری بلوچی"],
        ["bgn", "روچ کپتین بلوچی"],
        ["acm", "عراقي"],
        ["fa", "فارسی"],
        ["ku-arab", "كوردي (عەرەبی)"],
        ["luz", "لئری دوٙمینی"],
        ["lrc", "لۊری شومالی"],
        ["lki", "لەکی"],
        ["mzn", "مازِرونی"],
        ["arz", "مصرى"],
        ["pnb", "پنجابی"],
        ["ps", "پښتو"],
        ["ckb", "کوردی"],
        ["sdh", "کوردی خوارگ"],
        ["khw", "کھوار"],
        ["glk", "گیلکی"],
        ["ady", "адыгабзэ"],
        ["ady-cyrl", "адыгабзэ"],
        ["kbd", "адыгэбзэ"],
        ["kbd-cyrl", "адыгэбзэ"],
        ["ru", "русский"],
        ["tly-cyrl", "толыши"],
        ["az", "azərbaycanca"],
        ["brh", "Bráhuí"],
        ["ku", "kurdî"],
        ["ku-latn", "kurdî (latînî)"],
        ["kiu", "Kırmancki"],
        ["lad", "Ladino"],
        ["lzz", "Lazuri"],
        ["kk-latn", "qazaqşa (latın)"],
        ["kk-tr", "qazaqşa (Türkïya)"],
        ["tly", "tolışi"],
        ["tr", "Türkçe"],
        ["yi", "ייִדיש"],
        ["he", "עברית"],
        ["arc", "ܐܪܡܝܐ"],
        ["mr", "मराठी"],
        ["ml", "മലയാളം"],
        ["hyw", "Արեւմտահայերէն"],
        ["hy", "հայերեն"],
        ["nqo", "ߒߞߏ"],
        ["ti", "ትግርኛ"],
        ["am", "አማርኛ"],
        ["tzm", "ⵜⴰⵎⴰⵣⵉⵖⵜ"],
        ["zgh", "ⵜⴰⵎⴰⵣⵉⵖⵜ ⵜⴰⵏⴰⵡⴰⵢⵜ"],
        ["shi-tfng", "ⵜⴰⵛⵍⵃⵉⵜ"],
        ["ary", "الدارجة"],
        ["ar", "العربية"],
        ["aeb", "تونسي / Tûnsî"],
        ["aeb-arab", "تونسي"],
        ["arq", "جازايرية"],
        ["arz", "مصرى"],
        ["af", "Afrikaans"],
        ["agq", "Aghem"],
        ["ksf", "Bafia"],
        ["bm", "bamanankan"],
        ["ny", "Chi-Chewa"],
        ["sn", "chiShona"],
        ["tum", "chiTumbuka"],
        ["dga", "Dagaare"],
        ["dag", "dagbanli"],
        ["efi", "Efịk"],
        ["vmw", "emakhuwa"],
        ["es", "español"],
        ["es-formal", "español (formal)"],
        ["ee", "eʋegbe"],
        ["gur", "farefare"],
        ["ff", "Fulfulde"],
        ["fon", "fɔ̀ngbè"],
        ["gaa", "Ga"],
        ["gpe", "Ghanaian Pidgin"],
        ["guw", "gungbe"],
        ["ki", "Gĩkũyũ"],
        ["ha", "Hausa"],
        ["igl", "Igala"],
        ["ig", "Igbo"],
        ["rw", "Ikinyarwanda"],
        ["rn", "ikirundi"],
        ["xh", "isiXhosa"],
        ["zu", "isiZulu"],
        ["bkm", "Kom"],
        ["kea", "kabuverdianu"],
        ["kbp", "Kabɩyɛ"],
        ["kr", "kanuri"],
        ["kai", "Karai-karai"],
        ["sw", "Kiswahili"],
        ["kg", "Kongo"],
        ["ses", "Koyraboro Senni"],
        ["kri", "Krio"],
        ["kj", "Kwanyama"],
        ["kus", "Kʋsaal"],
        ["ln", "lingála"],
        ["lg", "Luganda"],
        ["mg", "Malagasy"],
        ["fat", "mfantse"],
        ["mos", "moore"],
        ["pcm", "Naijá"],
        ["nmz", "nawdm"],
        ["ann", "Obolo"],
        ["om", "Oromoo"],
        ["ng", "Oshiwambo"],
        ["hz", "Otsiherero"],
        ["pt", "português"],
        ["aa", "Qafár af"],
        ["nyn", "runyankore"],
        ["st", "Sesotho"],
        ["nso", "Sesotho sa Leboa"],
        ["tn", "Setswana"],
        ["loz", "Silozi"],
        ["ss", "SiSwati"],
        ["so", "Soomaaliga"],
        ["sg", "Sängö"],
        ["shy", "tacawit"],
        ["shy-latn", "tacawit"],
        ["shi", "Taclḥit"],
        ["shi-latn", "Taclḥit"],
        ["kab", "Taqbaylit"],
        ["rif", "Tarifit"],
        ["din", "Thuɔŋjäŋ"],
        ["ve", "Tshivenda"],
        ["tw", "Twi"],
        ["kcg", "Tyap"],
        ["aeb-latn", "Tûnsî"],
        ["mcn", "vùn màsànà"],
        ["bci", "wawle"],
        ["wal", "wolaytta"],
        ["wo", "Wolof"],
        ["ts", "Xitsonga"],
        ["yo", "Yorùbá"],
        ["bas", "Basaa"],
        ["ug", "ئۇيغۇرچە / Uyghurche"],
        ["ug-arab", "ئۇيغۇرچە"],
        ["ur", "اردو"],
        ["bqi", "بختیاری"],
        ["ms-arab", "بهاس ملايو"],
        ["azb", "تۆرکجه"],
        ["bcc", "جهلسری بلوچی"],
        ["bgn", "روچ کپتین بلوچی"],
        ["skr", "سرائیکی"],
        ["skr-arab", "سرائیکی"],
        ["sd", "سنڌي"],
        ["fa", "فارسی"],
        ["kk-arab", "قازاقشا (تٴوتە)"],
        ["kk-cn", "قازاقشا (جۇنگو)"],
        ["ota", "لسان عثمانى"],
        ["lrc", "لۊری شومالی"],
        ["lki", "لەکی"],
        ["mzn", "مازِرونی"],
        ["pnb", "پنجابی"],
        ["ps", "پښتو"],
        ["ks", "कॉशुर / کٲشُر"],
        ["ks-arab", "کٲشُر"],
        ["khw", "کھوار"],
        ["glk", "گیلکی"],
        ["hno", "ہندکو"],
        ["ryu", "沖縄口"],
        ["zh", "中文"],
        ["zh-cn", "中文（中国大陆）"],
        ["zh-tw", "中文（臺灣）"],
        ["zh-sg", "中文（新加坡）"],
        ["zh-mo", "中文（澳門）"],
        ["zh-hans", "中文（简体）"],
        ["zh-hant", "中文（繁體）"],
        ["zh-hk", "中文（香港）"],
        ["zh-my", "中文（马来西亚）"],
        ["wuu-hant", "吳語（正體）"],
        ["wuu", "吴语"],
        ["wuu-hans", "吴语（简体）"],
        ["lzh", "文言"],
        ["zh-classical", "文言"],
        ["ja", "日本語"],
        ["hsn", "湘语"],
        ["yue", "粵語"],
        ["zh-yue", "粵語"],
        ["yue-hant", "粵語（繁體）"],
        ["yue-hans", "粵语（简体）"],
        ["cpx", "莆仙語 / Pó-sing-gṳ̂"],
        ["cpx-hant", "莆仙語（繁體）"],
        ["cpx-hans", "莆仙语（简体）"],
        ["gan", "贛語"],
        ["gan-hant", "贛語（繁體）"],
        ["gan-hans", "赣语（简体）"],
        ["nan-hani", "閩南語"],
        ["ii", "ꆇꉙ"],
        ["ko-kp", "조선말"],
        ["ko", "한국어"],
        ["alt", "алтай тил"],
        ["bxr", "буряад"],
        ["ky", "кыргызча"],
        ["mn", "монгол"],
        ["gld", "на̄ни"],
        ["ru", "русский"],
        ["sah", "саха тыла"],
        ["sty", "себертатар"],
        ["tly-cyrl", "толыши"],
        ["tg", "тоҷикӣ"],
        ["tg-cyrl", "тоҷикӣ"],
        ["tyv", "тыва дыл"],
        ["kjh", "хакас"],
        ["uz-cyrl", "ўзбекча"],
        ["kk", "қазақша"],
        ["kk-cyrl", "қазақша (кирил)"],
        ["kk-kz", "қазақша (Қазақстан)"],
        ["ace", "Acèh"],
        ["abs", "bahasa ambon"],
        ["gor", "Bahasa Hulontalo"],
        ["id", "Bahasa Indonesia"],
        ["ms", "Bahasa Melayu"],
        ["bdr", "Bajau Sama"],
        ["ban", "Basa Bali"],
        ["bjn", "Banjar"],
        ["map-bms", "Basa Banyumasan"],
        ["bug", "Basa Ugi"],
        ["bbc", "Batak Toba"],
        ["bbc-latn", "Batak Toba"],
        ["bew", "Betawi"],
        ["bcl", "Bikol Central"],
        ["en-gb", "British English"],
        ["brh", "Bráhuí"],
        ["nan", "Bân-lâm-gú"],
        ["zh-min-nan", "Bân-lâm-gú"],
        ["cps", "Capiceño"],
        ["ceb", "Cebuano"],
        ["cbk-zam", "Chavacano de Zamboanga"],
        ["dtp", "Dusun Bundu-liwan"],
        ["hif", "Fiji Hindi"],
        ["hif-latn", "Fiji Hindi"],
        ["gom-latn", "Gõychi Konknni"],
        ["hak", "客家語/Hak-kâ-ngî"],
        ["ilo", "Ilokano"],
        ["hil", "Ilonggo"],
        ["bto", "Iriga Bicolano"],
        ["jv", "Jawa"],
        ["pam", "Kapampangan"],
        ["krj", "Kinaray-a"],
        ["cnh", "Hakha Chin"],
        ["nia", "Li Niha"],
        ["mad", "Madhurâ"],
        ["btm", "Batak Mandailing"],
        ["mrh", "Mara"],
        ["min", "Minangkabau"],
        ["lus", "Mizo ţawng"],
        ["cdo", "閩東語 / Mìng-dĕ̤ng-ngṳ̄"],
        ["uz", "oʻzbekcha / ўзбекча"],
        ["uz-latn", "oʻzbekcha"],
        ["pag", "Pangasinan"],
        ["ami", "Pangcah"],
        ["pwn", "pinayuanan"],
        ["pt", "português"],
        ["cpx-latn", "Pó-sing-gṳ̂ (Báⁿ-uā-ci̍)"],
        ["kaa", "Qaraqalpaqsha"],
        ["kk-latn", "qazaqşa (latın)"],
        ["kk-tr", "qazaqşa (Türkïya)"],
        ["xsy", "saisiyat"],
        ["szy", "Sakizaya"],
        ["trv", "Seediq"],
        ["su", "Sunda"],
        ["tl", "Tagalog"],
        ["tay", "Tayal"],
        ["tet", "tetun"],
        ["vi", "Tiếng Việt"],
        ["tg-latn", "tojikī"],
        ["tpi", "Tok Pisin"],
        ["tly", "tolışi"],
        ["tk", "Türkmençe"],
        ["ug-latn", "Uyghurche"],
        ["za", "Vahcuengh"],
        ["war", "Winaray"],
        ["diq", "Zazaki"],
        ["tru", "Ṫuroyo"],
        ["mnc", "ᠮᠠᠨᠵᡠ ᡤᡳᠰᡠᠨ"],
        ["dv", "ދިވެހިބަސް"],
        ["anp", "अंगिका"],
        ["awa", "अवधी"],
        ["ks-deva", "कॉशुर"],
        ["gom", "गोंयची कोंकणी / Gõychi Konknni"],
        ["gom-deva", "गोंयची कोंकणी"],
        ["dty", "डोटेली"],
        ["new", "नेपाल भाषा"],
        ["ne", "नेपाली"],
        ["pi", "पालि"],
        ["bh", "भोजपुरी"],
        ["bho", "भोजपुरी"],
        ["mag", "मगही"],
        ["mr", "मराठी"],
        ["rwr", "मारवाड़ी"],
        ["mai", "मैथिली"],
        ["sa", "संस्कृतम्"],
        ["hi", "हिन्दी"],
        ["as", "অসমীয়া"],
        ["bn", "বাংলা"],
        ["bpy", "বিষ্ণুপ্রিয়া মণিপুরী"],
        ["pa", "ਪੰਜਾਬੀ"],
        ["gu", "ગુજરાતી"],
        ["or", "ଓଡ଼ିଆ"],
        ["ta", "தமிழ்"],
        ["te", "తెలుగు"],
        ["kn", "ಕನ್ನಡ"],
        ["tcy", "ತುಳು"],
        ["ml", "മലയാളം"],
        ["si", "සිංහල"],
        ["dz", "ཇོང་ཁ"],
        ["bo", "བོད་ཡིག"],
        ["sat", "ᱥᱟᱱᱛᱟᱲᱤ"],
        ["syl", "ꠍꠤꠟꠐꠤ"],
        ["mni", "ꯃꯤꯇꯩ ꯂꯣꯟ"],
        ["th", "ไทย"],
        ["lo", "ລາວ"],
        ["ksw", "စှီၤ"],
        ["blk", "ပအိုဝ်ႏဘာႏသာႏ"],
        ["kjp", "ဖၠုံလိက်"],
        ["mnw", "ဘာသာ မန်"],
        ["my", "မြန်မာဘာသာ"],
        ["rki", "ရခိုင်"],
        ["shn", "ၽႃႇသႃႇတႆး "],
        ["km", "ភាសាខ្មែរ"],
        ["tdd", "ᥖᥭᥰᥖᥬᥳᥑᥨᥒᥰ"],
        ["nod", "ᨣᩤᩴᨾᩮᩬᩥᨦ"],
        ["ban-bali", "ᬩᬲᬩᬮᬶ"],
        ["zh", "中文"],
        ["zh-hans", "中文（简体）"],
        ["zh-hant", "中文（繁體）"],
        ["ace", "Acèh"],
        ["id", "Bahasa Indonesia"],
        ["ban", "Basa Bali"],
        ["bug", "Basa Ugi"],
        ["bi", "Bislama"],
        ["en-gb", "British English"],
        ["ch", "Chamoru"],
        ["na", "Dorerin Naoero"],
        ["mh", "Ebon"],
        ["es", "español"],
        ["wls", "Fakaʻuvea"],
        ["hif", "Fiji Hindi"],
        ["hif-latn", "Fiji Hindi"],
        ["sm", "Gagana Samoa"],
        ["haw", "Hawaiʻi"],
        ["ho", "Hiri Motu"],
        ["jv", "Jawa"],
        ["niu", "Niuē"],
        ["to", "lea faka-Tonga"],
        ["mi", "Māori"],
        ["fj", "Na Vosa Vakaviti"],
        ["pih", "Norfuk / Pitkern"],
        ["nys", "Nyunga"],
        ["pt", "português"],
        ["ty", "reo tahiti"],
        ["tet", "tetun"],
        ["tpi", "Tok Pisin"],
        ["ban-bali", "ᬩᬲᬩᬮᬶ"],
    ]
)

LANGUAGE_FREQUENCIES = collections.Counter(
    dict(
        [
            ("en", 20354),
            ("de", 6585),
            ("fr", 2726),
            ("ru", 1741),
            ("es", 1421),
            ("nl", 1087),
            ("it", 1036),
            ("ar", 849),
            ("pl", 619),
            ("fa", 465),
            ("tr", 451),
            ("pt", 432),
            ("sv", 349),
            ("uk", 348),
            ("ja", 330),
            ("he", 265),
            ("eo", 250),
            ("cs", 245),
            ("en-gb", 235),
            ("id", 227),
            ("hi", 221),
            ("ca", 190),
            ("bn", 175),
            ("vi", 167),
            ("hu", 152),
            ("ko", 127),
            ("zh-hans", 103),
            ("pt-br", 96),
            ("ro", 92),
            ("el", 88),
            ("fi", 87),
            ("zh-hant", 85),
            ("gl", 84),
            ("nb", 77),
            ("ta", 75),
            ("zh", 70),
            ("da", 67),
            ("sr", 66),
            ("ig", 62),
            ("az", 61),
            ("ml", 57),
            ("sk", 48),
            ("te", 46),
            ("my", 46),
            ("ur", 44),
            ("be", 41),
            ("th", 39),
            ("es-formal", 38),
            ("la", 37),
            ("mr", 36),
            ("hsb", 36),
            ("uz", 34),
            ("eu", 32),
            ("tl", 29),
            ("simple", 28),
            ("zh-tw", 27),
            ("bg", 26),
            ("lt", 25),
            ("es-419", 25),
            ("af", 25),
            ("gu", 25),
            ("ms", 24),
            ("ka", 23),
            ("si", 23),
            ("yi", 23),
            ("hr", 22),
            ("kn", 21),
            ("mk", 21),
            ("de-at", 21),
            ("tg", 20),
            ("zh-cn", 19),
            ("tt", 19),
            ("en-us", 19),
            ("kk", 17),
            ("ne", 16),
            ("nqo", 16),
            ("sw", 16),
            ("sl", 16),
            ("et", 16),
            ("de-ch", 16),
            ("ku", 15),
            ("am", 15),
            ("ban", 15),
            ("ha", 15),
            ("sq", 14),
            ("ckb", 14),
            ("de-formal", 13),
            ("hy", 13),
            ("lv", 13),
            ("nn", 12),
            ("ga", 12),
            ("szy", 12),
            ("sd", 12),
            ("as", 11),
            ("or", 11),
            ("pa", 11),
            ("ti", 10),
            ("be-tarask", 10),
            ("oc", 9),
            ("yo", 9),
            ("bs", 9),
            ("frc", 9),
            ("br", 8),
            ("nan", 8),
            ("zh-hk", 7),
            ("cy", 7),
            ("zh-yue", 7),
            ("als", 7),
            ("tzm", 7),
            ("bar", 7),
            ("lb", 7),
            ("zgh", 6),
            ("ug", 6),
            ("rsk", 6),
            ("sa", 6),
            ("jv", 6),
            ("zu", 6),
            ("zh-my", 5),
            ("nl-informal", 5),
            ("hyw", 5),
            ("mn", 5),
            ("no", 5),
            ("ary", 5),
            ("rue", 5),
            ("wa", 5),
            ("en-ca", 4),
            ("vec", 4),
            ("shi-tfng", 4),
            ("arz", 4),
            ("pdc", 4),
            ("yue", 4),
            ("ks", 3),
            ("anp", 3),
            ("gsw", 3),
            ("su", 3),
            ("km", 3),
            ("is", 3),
            ("kw", 3),
            ("mt", 3),
            ("arq", 3),
            ("ku-arab", 3),
            ("ky", 3),
            ("nds", 3),
            ("sn", 3),
            ("ff", 3),
            ("io", 3),
            ("ast", 3),
            ("li", 3),
            ("syl", 3),
            ("pnb", 3),
            ("gpe", 3),
            ("aa", 3),
            ("ps", 3),
            ("sc", 2),
            ("zh-sg", 2),
            ("rmy", 2),
            ("an", 2),
            ("tcy", 2),
            ("cv", 2),
            ("tk", 2),
            ("hu-formal", 2),
            ("ht", 2),
            ("sh", 2),
            ("sah", 2),
            ("ami", 2),
            ("ia", 2),
            ("ace", 2),
            ("aln", 2),
            ("bug", 2),
            ("frp", 2),
            ("sdc", 2),
            ("gn", 2),
            ("hif", 2),
            ("lo", 2),
            ("vls", 2),
            ("aeb", 2),
            ("ug-arab", 2),
            ("mni", 2),
            ("zh-mo", 1),
            ("tg-latn", 1),
            ("hak", 1),
            ("ve", 1),
            ("xh", 1),
            ("lg", 1),
            ("haw", 1),
            ("din", 1),
            ("ny", 1),
            ("lld", 1),
            ("nap", 1),
            ("xmf", 1),
            ("gag", 1),
            ("se-no", 1),
            ("be-x-old", 1),
            ("krc", 1),
            ("se-se", 1),
            ("cu", 1),
            ("se-fi", 1),
            ("cbk-zam", 1),
            ("dtp", 1),
            ("skr-arab", 1),
            ("sm", 1),
            ("new", 1),
            ("ku-latn", 1),
            ("tok", 1),
            ("bbc-latn", 1),
            ("ota", 1),
            ("fy", 1),
            ("sco", 1),
            ("ak", 1),
            ("ay", 1),
            ("ce", 1),
            ("szl", 1),
            ("tly-cyrl", 1),
            ("co", 1),
            ("ug-latn", 1),
            ("azb", 1),
            ("ase", 1),
            ("shn", 1),
            ("ms-arab", 1),
            ("roa-tara", 1),
            ("so", 1),
            ("inh", 1),
            ("mo", 1),
            ("ba", 1),
            ("udm", 1),
            ("grc", 1),
            ("bew", 1),
            ("avk", 1),
            ("lij", 1),
            ("ie", 1),
            ("lzh", 1),
            ("mzn", 1),
            ("glk", 1),
            ("scn", 1),
            ("nds-nl", 1),
            ("ab", 1),
            ("jbo", 1),
            ("myv", 1),
            ("sat", 1),
            ("tn", 1),
            ("lfn", 1),
            ("sr-ec", 1),
            ("tly", 1),
            ("shi", 1),
            ("lad", 1),
            ("rwr", 1),
            ("sr-el", 1),
            ("gan", 1),
            ("mnw", 1),
            ("ryu", 1),
            ("pam", 1),
            ("bm", 1),
            ("kab", 1),
            ("bho", 1),
        ]
    )
)
