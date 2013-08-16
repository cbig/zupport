## Esivaatimukset

### Python

järjestelmässä pitää olla Python asennettuna. Jos käyttäjällä on ArcGIS asennettuna, löytyy järjestelmästä myös Python. Zupportia on testattu Pythonin versioilla 2.6.x (ArcGIS 10.0) ja 2.7.x (ArcGIS 10.1).
   
Oletusarvoisesti Python-tulkkia (python.exe) ei ole lisätty käyttäjän ohjelmapolkuun (ympäristömuuttuja PATH), joten Windows ei tunnista Python-tulkin kutsua komentoriviltä. Lisää siis Python ohjelmapolkuun:
   
1. "Start menu" -> "Control panel" -> "System and security" -> "System" -> "Advanced system settings" -> "Advanced"-välilehti 
-> "Environment Variables" -> "System Variables"
2. Etsi listasta ympäristömuuttuja "Path", aktivoi se ja paina "Edit..."
3. Lisää kohtaan "Variable value" polku
   
"C:\Python26\ArcGIS10.0" (ArcGIS 10.0)
   		
tai

"C:\Python27\ArcGIS10.1" (ArcGIS 10.1)
		
4. Paina "OK" ja sulje kaikki ikkunat
5. Testaa avaamalla komentorivi-ikkuna (paina win + r ja kirjoita suoriteikkunaan "cmd")
6. Kirjoita komentoriville "python". Jos tulkki käynnistyy, kaikki meni hyvin.

## Lähdekoodin hakeminen

### Kehitysversio

1. Asenna Tortoisehg (http://tortoisehg.bitbucket.org/)

2. Navigoi kansioon, johon Zuppportin lähdekoodi ladataan (esim. C:\dev\Zupport)

3. Klikkaa kansion sisällä hiiren oikeaa nappia ja valitse

	"TortoiseHg" -> "Clone..."
	
4. Laita kennttään "Source" seuraava osoite:

    http://hg.assembla.com/zupport
    
5. Paina nappulaa "Clone"

### Julkaisuversio

1. Lataa lähdekoodi [zip-pakettina](https://github.com/cbig/zupport/archive/master.zip).

2. Pura zip-paketti haluamaasi paikkaan.

## Asennus

1. Mene lähdekoodikansioosn ja tuplaklikkaa tiedostoa "install.bat". Tämä ajaa asennusskriptin, joka asentaa sekä Zupportin riippuvuudet että itse Zupportin. (HUOM! jotta tämä toimisi, on Python-tulkin löydyttävä ohjelmapolusta, kts. "Esivaatimukset")
   
2. Asennusskpripti tallentaa kaikki viestit loki-tiedostoon "install_log.txt", tarkista sieltä, ett? kaikki meni hyvin.
 
3. Voit testata asennuksen onnistumista käynnistämällä komentorivin (kts. "Esivaatimukset" yllä) -> "python" -> "import zupport". Jos virheilmoituksia ei näy, kaikki meni hyvin.
 
### Työkalupakki
   
1. Avaa ArcMap

2. "ArcToolbox" -> "Add Toolbox" ja navigoi Zupportin latauskansioon (kts. kohta 2) -> kansio "thirdparty" -> "toolboxes" -> "Zupport.tbx"
