# Scores-apps (Dagscore, Werkscore, Ochtendscore)

Drie kleine web-apps om dagelijks scores in te vullen. Ze slaan op in Dropbox (map Apps › Scores).
Live via GitHub Pages:

| App | URL | Apparaat | Bestand in Dropbox |
|---|---|---|---|
| Dagscore | https://casperdijkvan-lgtm.github.io/dagscore/ | iPhone | `Scores.csv` |
| Werkscore | https://casperdijkvan-lgtm.github.io/dagscore/werk/ | Mac | `WorkScores.csv` |
| Ochtendscore | https://casperdijkvan-lgtm.github.io/dagscore/ochtend/ | iPhone | `MorningScores.csv` |

Het dashboard dat deze bestanden leest staat in een **andere repository**: `casperdijkvan-lgtm/dashboard`.

## Zo werkt deze repository

- **Bron:** `bron/dagscore.html` is de enige bron voor alle drie de apps. De instellingen van Dagscore
  staan in `<script id="app-config">` in dat bestand; die van Werkscore en Ochtendscore in `APPS` in
  `bron/build_site.py`.
- **Gebouwd:** `index.html`, `werk/index.html`, `ochtend/index.html` en de `apple-touch-icon.png`'s in de
  hoofdmap worden gemaakt door het bouwscript. **Nooit met de hand aanpassen.**
- **Online zetten:** GitHub Pages serveert de hoofdmap van `main`. Na een push staat het binnen ~1 minuut online.

### Een aanpassing doen (altijd deze stappen)

1. Pas `bron/dagscore.html` en/of `bron/build_site.py` aan.
2. Bouw: `python3 bron/build_site.py` (vanuit de hoofdmap). Pillow is optioneel; zonder Pillow blijven de
   bestaande iconen staan.
3. Commit **zowel de bron als de gebouwde bestanden** en push naar `main`.
4. Controleer na een minuut dat de live pagina de nieuwe versie heeft: de `<meta name="dagscore-versie">`
   in de live HTML moet gelijk zijn aan die in de gebouwde `index.html`.

De apps verversen zichzelf: bij openen vergelijken ze hun `dagscore-versie` met de site en laden opnieuw
als die anders is.

## Wensen van de gebruiker (belangrijk)

- Alles in het **Nederlands**.
- **Scrollen mag** (sinds november 2026, toen Vrienden en Robin erbij kwamen). Houd het wel compact; Werkscore en
  Ochtendscore passen nog op één iPhone 14-scherm (Safari, ca. 390×664) tot en met de opslaan-knop.
- **Eén regel per datum**: opnieuw opslaan voor dezelfde dag vervangt die regel (met waarschuwing +
  bevestiging als de dag al is opgeslagen). Bij het kiezen van een datum worden eerdere scores ingevuld.
- Standaarddatum: vóór 07:00 is het nog gisteren (`dayStartsAt`), behalve Ochtendscore (altijd vandaag).
- **Niets lokaal opslaan** behalve de Dropbox-login; alles komt uit Dropbox.
- CSV's: scheidingsteken `;`, geen kolom Tijd, gesorteerd op datum, halve punten met komma (`7,5`),
  Comment altijd tussen aanhalingstekens. Kolomvolgorde ligt vast (`COLUMNS`); de weergavevolgorde in de
  app regelt `"order"` in de config.
- Lege schaalwaarden worden als `0` opgeslagen.

## Vragen in Dagscore

Happiness, Energie, Privestress (0–5), Levenscontentheid, Vrienden (0–3: 0 geen contact, 1 berichtje, 2 gebeld of
kort gezien, 3 samen iets leuks), Robin (1–10: hoe ik naar Robin was), Alcohol, Ziek, Drugs, Comment. Vrienden en
Robin hebben bewust geen standaardwaarde: ze moeten elke dag gekozen worden. Oude regels hebben daar `0`;
het dashboard negeert die (Robin 0 valt buiten 1–10, Vrienden heeft `zero: 'after-first'`).

## Vraagtypes in de config

- `scale`: knoppen `min`…`max`, labels `low`/`high`, optioneel `default`, `compact: true` (twee compacte
  vragen naast elkaar).
- `slider`: `min`, `max`, `step` (bv. 0.5), optioneel `default` (Ochtendscore: Wakker staat standaard op 0,5).
- `text`: commentaarveld.
- `short` is de korte naam in het overzicht; `label` is de vraag en tevens de kolomnaam (zonder `?`).

## Dropbox

- Dropbox-app **DagScores**, app key `erjo5qemoyi1iu4` (niet geheim; inloggen via PKCE in de browser),
  toegang: App folder (`Apps/Scores`). Redirect-URI's moeten in de Dropbox-app staan voor elke app-URL.
- Opslaan: download → regel samenvoegen → upload met `update(rev)`, max. 3 pogingen bij een conflict.
- **Eenmalige omzettingen** (`"migrations"` in de config, `runMigration()` in de bron): zetten oude waarden
  in het Dropbox-bestand om, maken een reservekopie `…-voor-omzetting-<id>.csv` en een markeringsbestand
  `omzetting-<id>.txt` zodat het nooit twee keer gebeurt. Bestaand: `privestress-0-5` (Dagscore) en
  `werkstress-0-5` (Werkscore): 1–10 → 0–5 (v ≥ 5 → v − 5, anders 0). Soort `{ "drop": "Kolom" }` haalt een kolom
  helemaal uit het bestand: `test2-verwijderen` (Dagscore) haalde de testkolom Test2 weg. Soort `{ "rename": ["Oud", "Nieuw"] }`
  hernoemt een kolom (`readRows` leest de oude naam al als de nieuwe): `happiness-naam` (Dagscore) en
  `werk-happiness-naam` (Werkscore) maakten van Happyness Happiness. Id's moeten over alle apps uniek zijn
  (de markeringsbestanden staan samen in Apps › Scores). Verwijder een migratie-id nooit
  en hergebruik er nooit een.

## Samenhang met het dashboard

Het dashboard (`casperdijkvan-lgtm/dashboard`) leest de kolommen van deze CSV's op naam, met vaste
schalen. **Voeg je een vraag toe, hernoem je een kolom of verander je een schaal, dan moet het dashboard
ook aangepast worden** (metriek-register `M` in `bron/dashboard.html` daar). Zeg dat tegen de gebruiker als
je in deze sessie alleen bij deze repository kunt.

## Testen

Er is geen testsuite. Test in een browser met een nagebootste Dropbox: vervang `window.fetch` vóór het
app-script door een mock die `files/download`, `files/upload` (modes add/update/overwrite met rev-conflict)
en `files/delete_v2` in `localStorage` bijhoudt, en zet nep-inlog in `localStorage['dropbox.auth.v1']`
(`{access, refresh, exp}`). Zet testbestanden nooit in de repository.

## Veiligheid

Deze repository is openbaar. Zet er nooit sleutels of wachtwoorden in (de intervals.icu-sleutel van het
dashboard staat alleen in de browser van de gebruiker).
