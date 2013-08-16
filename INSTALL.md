## Esivaatimukset

1. Python - j�rjestelm�ss� pit�� olla Python asennettuna. Jos k�ytt�j�ll� on 
   ArcGIS asennettuna, l�ytyy j�rjestelm�st� my�s Python. Zupportia on testattu
   Pythonin versioilla 2.6.x (ArcGIS 10.0) ja 2.7.x (ArcGIS 10.1).
   
   Oletusarvoisesti Python-tulkkia (python.exe) ei ole lis�tty k�ytt�j�n 
   ohjelmapolkuun (ymp�rist�muuttuja PATH), joten Windows ei tunnista 
   Python-tulkin kutsua komentorivilt�. Lis�� siis Python ohjelmapolkuun:
   
   1. "Start menu" -> "Control panel" -> "System and security" -> "System"
      -> "Advanced system settings" -> "Advanced"-v�lilehti 
      -> "Environment Variables" -> "System Variables"
   2. Etsi listasta ymp�rist�muuttuja "Path", aktivoi se ja paina "Edit..."
   3. Lis�� kohtaan "Variable value" polku
   
   		"C:\Python26\ArcGIS10.0" (ArcGIS 10.0)
   		
   		tai

		"C:\Python27\ArcGIS10.1" (ArcGIS 10.1)
		
   4. Paina "OK" ja sulje kaikki ikkunat
   5. Testaa avaamalla komentorivi-ikkuna (paina win + r ja kirjoita 
      suoriteikkunaan "cmd")
   6. Kirjoita komentoriville "python". Jos tulkki k�ynnistyy, kaikki meni 
   	  hyvin.

## Kehitysversio

### Asennus

1. Asenna Tortoisehg (http://tortoisehg.bitbucket.org/)

2. Navigoi kansioon, johon Zuppportin l�hdekoodi ladataan (esim. C:\dev\Zupport)

3. Klikkaa kansion sis�ll� hiiren oikeaa nappia ja valitse

	"TortoiseHg" -> "Clone..."
	
4. Laita kenntt��n "Source" seuraava osoite:

    http://hg.assembla.com/zupport
    
5. Paina nappulaa "Clone"

6. Zupportin asennuskansiossa, tuplaklikkaa tiedostoa "install.bat". T�m� ajaa
   asennusskriptin, joka asentaa sek� Zupportin riippuvuudet ett� itse 
   Zupportin. (HUOM! jotta t�m� toimisi, on Python-tulkin l�ydytt�v� 
   ohjelmapolusta, kts. "Esivaatimukset")
   
7. Asennusskpripti tallentaa kaikki viestit loki-tiedostoon "install_log.txt",
   tarkista sielt�, ett� kaikki meni hyvin.
 
8. Voit testata asennuksen onnistumista k�ynnist�m�ll� komentorivin (kts. 
   "Esivaatimukset" yll�) -> "python" -> "import zupport". Jos virheilmoituksia
   ei n�y, kaikki meni hyvin.
 
### Ty�kalupakki
   
9. Avaa ArcMap

10. "ArcToolbox" -> "Add Toolbox" ja navigoi Zupportin latauskansioon (kts. 
    kohta 2) -> kansio "thirdparty" -> "toolboxes" -> "Zupport.tbx"
