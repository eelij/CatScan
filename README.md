# CatScan

CatScan on komentorivipohjainen kehittäjän työkalu Scratch-projektien (`.sb3`) analysointiin, tarkasteluun ja purkamiseen.

CatScan on suunniteltu erityisesti Scratch-projektien rakenteen tutkimiseen suoraan terminaalista.

## Ominaisuudet

- **Interactive Shell**
  - Valittu `.sb3`-projekti pysyy muistissa komentojen välillä.
  - Projektia voi tarkastella useilla komennoilla ilman tiedoston uudelleen määrittämistä.

- **Project Inspector (`inspect`)**
  - Näyttää projektin rakenteen ja tilastot.
  - Hahmot ja Stage
  - Skriptit
  - Lohkot
  - Muuttujat
  - Listat
  - Broadcastit
  - Asut
  - Äänet
  - Kohdekohtaiset tiedot

- **Project Extraction (`extract`)**
  - Purkaa `.sb3`-tiedoston sisällön hakemistoon.
  - Sisältää esimerkiksi:
    - `project.json`
    - Asut
    - Äänet
    - Muut projektin resurssit

- **Script Inspector (`script`)**
  - Näyttää Scratch-projektin skriptit suoraan terminaalissa.
  - Kohteen ja skriptin voi valita interaktiivisesti.
  - Tukee sisäkkäisiä rakenteita.
  - Tukee ehtolauseita.
  - Tukee silmukoita.
  - Tukee mukautettuja lohkoja.
  - Tukee `procedures_call`-kutsuja.
  - Näyttää lohkot, kentät ja parametrit selkeästi sisennettynä.
  - Tulostus toimii Unix-työkalujen, kuten `grep`, `awk` ja `sed`, kanssa.

- **Script Saving (`script save`)**
  - Skriptit voi tallentaa tekstitiedostoksi.
  - Tiedostonimen voi antaa itse tai CatScan voi luoda sen automaattisesti.

- **ANSI-värit**
  - Selkeä värikoodattu terminaalitulostus.
  - Värit voi poistaa käytöstä `--no-color`-optiolla.
  - Sopii hyvin komentojen pipe-käyttöön.

## Vaatimukset

- Python 3.10 tai uudempi
- Linux tai macOS

Interaktiiviset valikot käyttävät Pythonin `termios`- ja `tty`-moduuleita.

## Asennus

Kloonaa repository:

```bash
git clone <repository-url>
cd CatScan