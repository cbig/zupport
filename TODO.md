1. Copying plugin definition files to user folder is redundant, is this even
   needed?


VESALTA:

1. Asennus: Funktiomuunnosta k�ynnistett�ess� tuli virheilmoitus, ett� scipy-moduulia
   ei l�ydy. Kokeilin lis�t� riippuvuuden setup.py:hyn numpyn per��n, mutta asennus
   kaatui lukuisiin virheilmoituksiin. Hain paketin erikseen ja sen asentamisen j�lkeen
   funktiomuunnos alkoi toimimaan.
   
   -> 30.8.2012: korjaattu, scipy poistettu kokonaan riippuvuuksista

2. Funktiomuunnos: Jos puulaji-osite -rasteroinnit laittaa File Geodatabaseen,
   funktiomuunnos kaatuu virheilmoitukseen (ks. liitetiedosto). Ilmeisesti ty�kalu
   ei l�yd� rastereita. Rasterointi on siis teht�v� kansioon esim. Imagine-formaattiin.
   
   -> 

3. Funktiomuunnos: Wildcard-kentt��n ei saa kirjoittaa haluamaansa merkkijonoa. Jos
   yritt�� k�ytt�� jotain muuta kuin tyhj�� tai alasvetovalikon vaihtoehtoja,
   tulee virheilmoitus 'The value is not a member of...'. Voisi olla joskus
   hy�dyllist�, ett� villej� merkkej� voisi k�ytt�� vapaasti tilanteissa, joissa
   Input Workspacessa on muutakin kamaa kuin rasteroinnin tulokset.

   ->

4. Yksi vakavampi toimimattomuus l�ytyi, kun aloin Zonationin ajamista valmistelemaan.
   Batch Convert Raster -ty�kalu ei tottele Extent-m��rityst�. Lopputuloksena kaikki
   puulaji-osite -rasterit on extentilt��n alkuper�isen kuviodatan mukainen eik�
   ty�kalun dialogi-ikkunassa m��ritellyn tason mukainen. K�yt�mme Extent- ja Snap -rastereina
   aina samaa tasoa, jotta kaikki datat kattaa varmasti t�sm�lleen saman alueen.

   J�ljitin ongelmakohdan MultiConvertRaster.py:hyn ja sain homman toimimaan
   alla olevan kohdan muokkauksella. Koska ty�kalun v�litt�m� extent-parametri on aina
   merkkijono ja se kelpaa sellaisenaan analyysialueen m��ritykseen (ei tarvitse konvertointia
   float-listaksi), niin ohitinkin vertailu- ja muunnoskohdan kylm�sti kommentoimalla 'tarpeettoman'
   ja asettamalla extentiksi alkup. parametrin arvon. Ainakin nyt tulosrasterit ovat oikean kokoisia.

         # Set the extent if provided
         if extent is not None and extent != '':
#           if type(extent) is types.StringType:
#              extent = [float(coord) for coord in extent.split(',')]
#           self.gp.env.extent = self.gp.Extent(extent)
            self.gp.env.extent = extent
            self.log.debug('Extent set to %s' % extent)

   -> 30.8.2012: korjaattu Vesan ehdottamalla tavalla
