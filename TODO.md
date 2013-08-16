1. Copying plugin definition files to user folder is redundant, is this even
   needed?


VESALTA:

1. Asennus: Funktiomuunnosta käynnistettäessä tuli virheilmoitus, että scipy-moduulia
   ei löydy. Kokeilin lisätä riippuvuuden setup.py:hyn numpyn perään, mutta asennus
   kaatui lukuisiin virheilmoituksiin. Hain paketin erikseen ja sen asentamisen jälkeen
   funktiomuunnos alkoi toimimaan.
   
   -> 30.8.2012: korjaattu, scipy poistettu kokonaan riippuvuuksista

2. Funktiomuunnos: Jos puulaji-osite -rasteroinnit laittaa File Geodatabaseen,
   funktiomuunnos kaatuu virheilmoitukseen (ks. liitetiedosto). Ilmeisesti työkalu
   ei löydä rastereita. Rasterointi on siis tehtävä kansioon esim. Imagine-formaattiin.
   
   -> 

3. Funktiomuunnos: Wildcard-kenttään ei saa kirjoittaa haluamaansa merkkijonoa. Jos
   yrittää käyttää jotain muuta kuin tyhjää tai alasvetovalikon vaihtoehtoja,
   tulee virheilmoitus 'The value is not a member of...'. Voisi olla joskus
   hyödyllistä, että villejä merkkejä voisi käyttää vapaasti tilanteissa, joissa
   Input Workspacessa on muutakin kamaa kuin rasteroinnin tulokset.

   ->

4. Yksi vakavampi toimimattomuus löytyi, kun aloin Zonationin ajamista valmistelemaan.
   Batch Convert Raster -työkalu ei tottele Extent-määritystä. Lopputuloksena kaikki
   puulaji-osite -rasterit on extentiltään alkuperäisen kuviodatan mukainen eikä
   työkalun dialogi-ikkunassa määritellyn tason mukainen. Käytämme Extent- ja Snap -rastereina
   aina samaa tasoa, jotta kaikki datat kattaa varmasti täsmälleen saman alueen.

   Jäljitin ongelmakohdan MultiConvertRaster.py:hyn ja sain homman toimimaan
   alla olevan kohdan muokkauksella. Koska työkalun välittämä extent-parametri on aina
   merkkijono ja se kelpaa sellaisenaan analyysialueen määritykseen (ei tarvitse konvertointia
   float-listaksi), niin ohitinkin vertailu- ja muunnoskohdan kylmästi kommentoimalla 'tarpeettoman'
   ja asettamalla extentiksi alkup. parametrin arvon. Ainakin nyt tulosrasterit ovat oikean kokoisia.

         # Set the extent if provided
         if extent is not None and extent != '':
#           if type(extent) is types.StringType:
#              extent = [float(coord) for coord in extent.split(',')]
#           self.gp.env.extent = self.gp.Extent(extent)
            self.gp.env.extent = extent
            self.log.debug('Extent set to %s' % extent)

   -> 30.8.2012: korjaattu Vesan ehdottamalla tavalla
