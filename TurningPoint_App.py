import pandas as pd
import streamlit as st
import yfinance as yf

# পেজ কনফিগারেশন
st.set_page_config(
    page_title="Ultimate Higher Low & Candlestick Screener", layout="wide"
)
st.title("🎯 Ultimate Higher Low & Candlestick Screener")
st.caption(
    "পূর্ণাঙ্গ স্টক লিস্ট, Higher Low সাপোর্ট জোন এবং আপনার পছন্দের সকল বুলিশ"
    " ক্যান্ডেলস্টিক প্যাটার্ন স্ক্যানার।"
)

# আপনার দেওয়া সম্পূর্ণ স্টক লিস্ট (SUB_SECTORS)
SUB_SECTORS = {
    "🏦 1. Banking, Finance & NBFC (260 Stocks)": [
        "HDFCBANK.NS",
        "ICICIBANK.NS",
        "SBIN.NS",
        "AXISBANK.NS",
        "KOTAKBANK.NS",
        "BAJFINANCE.NS",
        "BAJAJFINSV.NS",
        "MUTHOOTFIN.NS",
        "INDUSINDBK.NS",
        "BANKBARODA.NS",
        "PNB.NS",
        "FEDERALBNK.NS",
        "IDFCFIRSTB.NS",
        "AUBANK.NS",
        "CANBK.NS",
        "UNIONBANK.NS",
        "BANDHANBNK.NS",
        "CHOLAFIN.NS",
        "SHRIRAMFIN.NS",
        "M&MFIN.NS",
        "LICHSGFIN.NS",
        "RECLTD.NS",
        "PFC.NS",
        "MANAPPURAM.NS",
        "J&KBANK.NS",
        "KARURVYSYA.NS",
        "SOUTHBANK.NS",
        "CUB.NS",
        "EQUITASBNK.NS",
        "UJJIVANSFB.NS",
        "MAHABANK.NS",
        "CENTRALBK.NS",
        "IOB.NS",
        "BANKINDIA.NS",
        "UCOBANK.NS",
        "POONAWALLA.NS",
        "IIFL.NS",
        "PEL.NS",
        "CANFINHOME.NS",
        "HOMEFIRST.NS",
        "HUDCO.NS",
        "ABCAPITAL.NS",
        "ICICIPRULI.NS",
        "HDFCLIFE.NS",
        "SBILIFE.NS",
        "LICI.NS",
        "PAYTM.NS",
        "POLICYBZR.NS",
        "PSB.NS",
        "DCBBANK.NS",
        "FINPIPE.NS",
        "MOTILALOFS.NS",
        "ANGELONE.NS",
        "5PAISA.NS",
        "ISEC.NS",
        "BSE.NS",
        "MCX.NS",
        "UTIAMC.NS",
        "NAM-INDIA.NS",
        "HDFCAMC.NS",
        "STARHEALTH.NS",
        "ICICIGI.NS",
        "GICRE.NS",
        "NIACL.NS",
        "PNBHOUSING.NS",
        "AAVAS.NS",
        "REPCOHOME.NS",
        "MASFIN.NS",
        "ARMANFIN.NS",
        "SURYODAY.NS",
        "ESAFSFB.NS",
        "UTKARSHBNK.NS",
        "FINOPB.NS",
        "KALYANKJIL.NS",
        "SBICARD.NS",
        "SUNDARMFIN.NS",
        "NUVAMA.NS",
        "360ONE.NS",
        "KFINTECH.NS",
        "CAMSLTD.NS",
        "CDSL.NS",
        "GICHSGFIN.NS",
        "IFCI.NS",
        "RELIGARE.NS",
        "VAKRANGEE.NS",
        "L&TFH.NS",
        "MUTHOOTCAP.NS",
        "BAJAJHFL.NS",
        "SBFC.NS",
        "NORTHERNARC.NS",
        "IXIGO.NS",
        "EASEMYTRIP.NS",
        "FIVESTAR.NS",
        "KIMS.NS",
        "MEDANTA.NS",
        "SMCGLOBAL.NS",
        "MONEYBOXX.NS",
        "FINCABLES.NS",
        "CAPITALSFB.NS",
        "SPANDANA.NS",
        "SATIN.NS",
        "MUTHOOTMF.NS",
        "FUSION.NS",
        "INDOSTAR.NS",
        "AHLUWALIA.NS",
        "CANTABIL.NS",
        "AMBER.NS",
        "FINEOTEX.NS",
        "ASTEC.NS",
        "DCW.NS",
        "SHARDACROP.NS",
        "CAMLINFINE.NS",
        "THIRUMALAI.NS",
        "AVADHSUGAR.NS",
        "KIRLOSENG.NS",
        "AMIORG.NS",
        "AETHER.NS",
        "TATVA.NS",
        "EPIGRAL.NS",
        "PARAMOUNT.NS",
        "DILIPBUILD.NS",
        "SELAN.NS",
        "VIMTALABS.NS",
        "COROMANDEL.NS",
        "GUFICBIO.NS",
        "HESTERBIO.NS",
        "MALLCOM.NS",
        "MOREPENLAB.NS",
        "ORIENTBELL.NS",
        "RUBYMILLS.NS",
        "TASTYBITE.NS",
        "UNIVCABLES.NS",
        "VALIANTORG.NS",
        "VASCONEQ.NS",
        "ZOTA.NS",
        "KIRLOSIND.NS",
        "IFBAGRO.NS",
        "ADFFOODS.NS",
        "MIRZAINT.NS",
        "LIBERTSHOE.NS",
        "KHADIM.NS",
        "ZODIACLOTH.NS",
        "SPENCERS.NS",
        "LANDMARK.NS",
        "ETHOSLTD.NS",
        "VMART.NS",
        "GOKEX.NS",
        "VIPIND.NS",
        "REDINGTON.NS",
        "SAKSOFT.NS",
        "SUBEXLTD.NS",
        "INFOBEAN.NS",
        "GENESYS.NS",
        "MTNL.NS",
        "TEJASNET.NS",
        "HFCL.NS",
        "RAILTEL.NS",
        "OPTIEMUS.NS",
        "ITI.NS",
        "STERTOOLS.NS",
        "NELCO.NS",
        "EXPLEOSOL.NS",
        "CIGNITI.NS",
        "RAMCOSYS.NS",
        "QUESS.NS",
        "TEAMLEASE.NS",
        "SIS.NS",
        "FIRSTSOURCE.NS",
        "ALLSEC.NS",
        "MPSLTD.NS",
        "DATAMATICS.NS",
        "SIGNPOST.NS",
        "GTLINFRA.NS",
        "SOFTTECH.NS",
        "INNOVANA.NS",
        "AXISCADES.NS",
        "ONWARDTEC.NS",
        "TRIGYN.NS",
        "DREAMFOLKS.NS",
        "E2E.NS",
        "XELPMOC.NS",
        "JSL.NS",
        "MIDHANI.NS",
        "GALLANTT.NS",
        "ISMTLTD.NS",
        "GODAWARI.NS",
        "KAJARIRCER.NS",
        "SOMANYCERA.NS",
        "CERA.NS",
        "PRINCEPIPE.NS",
        "ASTRAL.NS",
        "SUPREMEIND.NS",
        "STARCEMENT.NS",
        "ORIENTCEM.NS",
        "NCLIND.NS",
        "BHARATWIRE.NS",
        "SHANKARA.NS",
        "PENIND.NS",
        "GOODLUCK.NS",
        "CENTURYTEX.NS",
        "RAYMOND.NS",
        "SWANENERGY.NS",
        "ALOKINDS.NS",
        "KPRMILL.NS",
        "LUXIND.NS",
        "PAGEIND.NS",
        "RUPA.NS",
        "DOLLAR.NS",
        "TRIDENT.NS",
        "WELSPUNLIV.NS",
        "INDOCOUNT.NS",
        "FILATEX.NS",
        "RSWM.NS",
        "SUTLEJTEX.NS",
        "GARFIBRES.NS",
        "GOCOLORS.NS",
        "VEDANTFASH.NS",
    ],
    "⛽ 2. Oil, Gas, Energy & Chemicals (180 Stocks)": [
        "RELIANCE.NS",
        "ONGC.NS",
        "IOC.NS",
        "BPCL.NS",
        "HPCL.NS",
        "GAIL.NS",
        "OIL.NS",
        "ATGL.NS",
        "PETRONET.NS",
        "MGL.NS",
        "IGL.NS",
        "GUJGASLTD.NS",
        "COALINDIA.NS",
        "NTPC.NS",
        "POWERGRID.NS",
        "TATAPOWER.NS",
        "IREDA.NS",
        "SUZLON.NS",
        "ADANIGREEN.NS",
        "ADANIPOWER.NS",
        "NHPC.NS",
        "INOXWIND.NS",
        "KPIGREEN.NS",
        "TORNTPOWER.NS",
        "CESC.NS",
        "JSWENERGY.NS",
        "ADANIENT.NS",
        "BHEL.NS",
        "DEEPAKNTR.NS",
        "GSPL.NS",
        "CHAMBLFERT.NS",
        "UPL.NS",
        "GNFC.NS",
        "NFL.NS",
        "RCF.NS",
        "FACT.NS",
        "COROMANDEL.NS",
        "PIIND.NS",
        "SRF.NS",
        "AARTIIND.NS",
        "ATUL.NS",
        "SUMICHEM.NS",
        "LINDEINDIA.NS",
        "SOLARINDS.NS",
        "CASTROLIND.NS",
        "AEGISCHEM.NS",
        "FINEORG.NS",
        "ALKYLAMINE.NS",
        "BALAMINES.NS",
        "TATACHEM.NS",
        "GHCL.NS",
        "DCMSRIRAM.NS",
        "FLUOROCHEM.NS",
        "VINATIORGA.NS",
        "NAVINFLUOR.NS",
        "CLEAN.NS",
        "ROSSARI.NS",
        "GRAVITA.NS",
        "EXIDEIND.NS",
        "EPL.NS",
        "SUPRIYA.NS",
        "CHEMCON.NS",
        "HERANBA.NS",
        "INDIAGLYCO.NS",
        "BALRAMCHIN.NS",
        "TRIVENI.NS",
        "RENUKA.NS",
        "EIDPARRY.NS",
        "BAJAJHIND.NS",
        "PRAJIND.NS",
        "JINDALSAW.NS",
        "WELCORP.NS",
        "MAHSEAMLES.NS",
        "APLAPOLLO.NS",
        "RATNAMANI.NS",
        "MOIL.NS",
        "HINDZINC.NS",
        "HINDCOPPER.NS",
        "NMDC.NS",
        "GMDC.NS",
        "KIOCL.NS",
        "SAIL.NS",
        "TATASTEEL.NS",
        "JSWSTEEL.NS",
        "JINDALSTEL.NS",
        "ELECTCAST.NS",
        "GODREJAGRO.NS",
        "SURYALAXMI.NS",
        "GIPCL.NS",
        "SANGHIIND.NS",
        "PRIVISCL.NS",
        "FINEOTEX.NS",
        "ASTEC.NS",
        "DCW.NS",
        "SHARDACROP.NS",
        "CAMLINFINE.NS",
        "THIRUMALAI.NS",
        "AVADHSUGAR.NS",
        "KIRLOSENG.NS",
        "AMIORG.NS",
        "AETHER.NS",
        "TATVA.NS",
        "SURYODAY.NS",
        "LAXMICHEM.NS",
        "EPIGRAL.NS",
        "PARAMOUNT.NS",
        "DILIPBUILD.NS",
        "SELAN.NS",
        "BASF.NS",
        "BAYERCROP.NS",
        "DHANUKA.NS",
        "INSECTICID.NS",
        "VALIANTORG.NS",
        "NOCIL.NS",
        "HIKAL.NS",
        "GUJALKALI.NS",
        "MOL.NS",
    ],
    "🏥 3. Pharma, Healthcare & Biotech (170 Stocks)": [
        "SUNPHARMA.NS",
        "CIPLA.NS",
        "DRREDDY.NS",
        "DIVISLAB.NS",
        "APOLLOHOSP.NS",
        "FORTIS.NS",
        "MAXHEALTH.NS",
        "NH.NS",
        "LALPATHLAB.NS",
        "MANKIND.NS",
        "TORNTPHARM.NS",
        "LUPIN.NS",
        "ZYDUSLIFE.NS",
        "AUROPHARMA.NS",
        "GLENMARK.NS",
        "ALKEM.NS",
        "IPCALAB.NS",
        "BIOCON.NS",
        "SYNGENE.NS",
        "METROPOLIS.NS",
        "LAURUSLABS.NS",
        "GRANULES.NS",
        "JBCHEPHY.NS",
        "NATCOPHARM.NS",
        "CAPLIPOINT.NS",
        "ERIS.NS",
        "GLAXO.NS",
        "PFIZER.NS",
        "ABBOTINDIA.NS",
        "SANOFI.NS",
        "AJANTPHARM.NS",
        "MARKSANS.NS",
        "HIKAL.NS",
        "ASTRAZEN.NS",
        "AARTIDRUGS.NS",
        "GLAND.NS",
        "KIMS.NS",
        "ASTERDM.NS",
        "RAINBOW.NS",
        "MEDANTA.NS",
        "VIJAYA.NS",
        "SUVENPHAR.NS",
        "NEULANDLAB.NS",
        "SHILPAMED.NS",
        "FDC.NS",
        "THYROCARE.NS",
        "PGHL.NS",
        "ALEMBICLTD.NS",
        "APLLTD.NS",
        "BLUEJET.NS",
        "CONCORD.NS",
        "KOPRAN.NS",
        "LINCOLN.NS",
        "MOREPENLAB.NS",
        "PANACEABIO.NS",
        "RPGLIFE.NS",
        "SEQUENT.NS",
        "SMSPHARMA.NS",
        "TTKHLTCARE.NS",
        "UNICHEMLAB.NS",
        "VENUSREM.NS",
        "WOCKPHARMA.NS",
        "ZEEL.NS",
        "YATHARTH.NS",
        "ARTEMISMED.NS",
        "INDOCO.NS",
        "HESTERBIO.NS",
        "BLISSGVS.NS",
        "SHALBY.NS",
        "SIGACHI.NS",
        "TARSONS.NS",
        "NOVARTIND.NS",
        "RALLIS.NS",
        "INNOVA.NS",
        "AKUMS.NS",
        "JUBILANT.NS",
        "NGLFINE.NS",
        "MEDPLUS.NS",
        "KRSNAA.NS",
        "ENTERO.NS",
        "WINDLAS.NS",
        "AMRUTANJAN.NS",
        "VIMTALABS.NS",
        "COROMANDEL.NS",
        "GUFICBIO.NS",
        "NECTARLIFE.NS",
        "ORIENTBELL.NS",
        "RUBYMILLS.NS",
        "TASTYBITE.NS",
        "UNIVCABLES.NS",
        "VALIANTORG.NS",
        "VASCONEQ.NS",
        "ZOTA.NS",
    ],
    "💻 4. IT, Software & Tech Services (160 Stocks)": [
        "TCS.NS",
        "INFY.NS",
        "WIPRO.NS",
        "TECHM.NS",
        "HCLTECH.NS",
        "PERSISTENT.NS",
        "COFORGE.NS",
        "LTIM.NS",
        "MPHASIS.NS",
        "LTTS.NS",
        "TATAELXSI.NS",
        "KPITTECH.NS",
        "CYIENT.NS",
        "OFSS.NS",
        "ZENSARTECH.NS",
        "BSOFT.NS",
        "HAPPSTMNDS.NS",
        "INTELLECT.NS",
        "TATACOMM.NS",
        "MASTEK.NS",
        "SONATSOFTW.NS",
        "ECLERX.NS",
        "DATAPATTNS.NS",
        "NETWEB.NS",
        "TATATECH.NS",
        "NEWGEN.NS",
        "TANLA.NS",
        "RATEGAIN.NS",
        "FSL.NS",
        "LATENTVIEW.NS",
        "KAYNES.NS",
        "ROUTE.NS",
        "CEINFO.NS",
        "BLS.NS",
        "AFFLE.NS",
        "JUSTDIAL.NS",
        "NAUKRI.NS",
        "ZOMATO.NS",
        "CAMS.NS",
        "CDSL.NS",
        "INDIAMART.NS",
        "RSYSTEMS.NS",
        "NUCLEUS.NS",
        "REDINGTON.NS",
        "SAKSOFT.NS",
        "SUBEXLTD.NS",
        "INFOBEAN.NS",
        "GENESYS.NS",
        "BHARTIARTL.NS",
        "IDEA.NS",
        "MTNL.NS",
        "TEJASNET.NS",
        "HFCL.NS",
        "RAILTEL.NS",
        "OPTIEMUS.NS",
        "ITI.NS",
        "STERTOOLS.NS",
        "NELCO.NS",
        "EXPLEOSOL.NS",
        "BIRLASOFT.NS",
        "CIGNITI.NS",
        "RAMCOSYS.NS",
        "QUESS.NS",
        "TEAMLEASE.NS",
        "SIS.NS",
        "FIRSTSOURCE.NS",
        "ALLSEC.NS",
        "MPSLTD.NS",
        "DATAMATICS.NS",
        "SIGNPOST.NS",
        "GTLINFRA.NS",
        "SOFTTECH.NS",
        "INNOVANA.NS",
        "AXISCADES.NS",
        "VAKRANGEE.NS",
        "ONWARDTEC.NS",
        "TRIGYN.NS",
        "DREAMFOLKS.NS",
        "MAPMYINDIA.NS",
        "E2E.NS",
        "XELPMOC.NS",
    ],
    "🚂 5. Railways, Logistics & Infrastructure (150 Stocks)": [
        "IRFC.NS",
        "RVNL.NS",
        "IRCON.NS",
        "RAILTEL.NS",
        "RITES.NS",
        "TEXRAIL.NS",
        "TITAGARH.NS",
        "BEML.NS",
        "CONCOR.NS",
        "GPPL.NS",
        "MAZDOCK.NS",
        "COCHINSHIP.NS",
        "GRSE.NS",
        "DELHIVERY.NS",
        "BLUEDART.NS",
        "TCIEXP.NS",
        "MAHLOG.NS",
        "VRLLOG.NS",
        "ALLCARGO.NS",
        "AEGISCHEM.NS",
        "GMRINFRA.NS",
        "ADANIPORTS.NS",
        "JSWINFRA.NS",
        "IRB.NS",
        "PNCINFRA.NS",
        "KNRCON.NS",
        "HGINFRA.NS",
        "GRINFRA.NS",
        "DILIPBUILD.NS",
        "ITD.NS",
        "NCC.NS",
        "ASHOKA.NS",
        "ENGINERSIN.NS",
        "NBCC.NS",
        "PSPPROJECT.NS",
        "CAPACITE.NS",
        "AHLUCONT.NS",
        "MANINFRA.NS",
        "DLF.NS",
        "LODHA.NS",
        "GODREJPROP.NS",
        "OBERREALTY.NS",
        "PHOENIXLTD.NS",
        "PRESTAGE.NS",
        "BRIGADE.NS",
        "SOBHA.NS",
        "SIGNATURE.NS",
        "MAHLIFE.NS",
        "SUNTECK.NS",
        "KOLTEPATIL.NS",
        "ASHIANA.NS",
        "PURVA.NS",
        "AJMERA.NS",
        "MARATHON.NS",
        "DBREALTY.NS",
        "RAMKY.NS",
        "GPTINFRA.NS",
        "RPPINFRA.NS",
        "OMAXE.NS",
        "ARKADE.NS",
        "KROSS.NS",
        "DREDGECORP.NS",
        "NAVNETEDUL.NS",
        "SEPC.NS",
        "INDOSTAR.NS",
    ],
    "🛒 6. FMCG, Retail & Consumer Durables (140 Stocks)": [
        "HINDUNILVR.NS",
        "ITC.NS",
        "NESTLEIND.NS",
        "BRITANNIA.NS",
        "TATACONSUM.NS",
        "DABUR.NS",
        "GODREJCP.NS",
        "MARICO.NS",
        "COLPAL.NS",
        "VBL.NS",
        "AWL.NS",
        "EMAMILTD.NS",
        "RADICO.NS",
        "UBL.NS",
        "MCDOWELL-N.NS",
        "TITAN.NS",
        "KALYANKJIL.NS",
        "SENCO.NS",
        "TRENT.NS",
        "DMART.NS",
        "ABFRL.NS",
        "MANYAVAR.NS",
        "BATAINDIA.NS",
        "RELAXO.NS",
        "CAMPUS.NS",
        "METROBRAND.NS",
        "HAVELLS.NS",
        "POLYCAB.NS",
        "CROMPTON.NS",
        "VOLTAS.NS",
        "BLUESTARCO.NS",
        "WHIRLPOOL.NS",
        "DIXON.NS",
        "AMBER.NS",
        "SYRMA.NS",
        "KEI.NS",
        "RRKABEL.NS",
        "FINCABLES.NS",
        "BAJAJELEC.NS",
        "ORIENTELEC.NS",
        "SYMPHONY.NS",
        "VGUARD.NS",
        "TTKPRESTIG.NS",
        "HAWKINS.NS",
        "PGHH.NS",
        "GILLETTE.NS",
        "JYOTHYLAB.NS",
        "BAJAJCON.NS",
        "GODREJAGRO.NS",
        "ZOMATO.NS",
        "JUBLFOOD.NS",
        "DEVYANI.NS",
        "WESTLIFE.NS",
        "SAPPHIRE.NS",
        "BARBEQUE.NS",
        "HONASA.NS",
        "PATANJALI.NS",
        "HERITGFOOD.NS",
        "DODLA.NS",
        "HATSUN.NS",
        "PARAGMILK.NS",
        "KRBL.NS",
        "LTFOODS.NS",
        "VENKEYS.NS",
        "AVANTIFEED.NS",
        "CCL.NS",
        "TCPLPACK.NS",
        "PVRINOX.NS",
        "TIPSMUSIC.NS",
        "SAREGAMA.NS",
        "SUNTV.NS",
        "ZEEL.NS",
        "NAZARA.NS",
        "DELTACORP.NS",
        "EASEMYTRIP.NS",
        "THOMASCOOK.NS",
        "YATRA.NS",
        "LEMONTREE.NS",
        "INDHOTEL.NS",
        "EIHOTEL.NS",
        "CHALET.NS",
        "SAMHI.NS",
        "PARKHOTELS.NS",
        "WONDERLA.NS",
        "BALRAMCHIN.NS",
        "RENUKA.NS",
        "BORORENEW.NS",
        "ADFFOODS.NS",
        "TASTYBITE.NS",
        "MIRZAINT.NS",
        "KHADIM.NS",
        "ETHOSLTD.NS",
        "VMART.NS",
        "GOKEX.NS",
        "CANTABIL.NS",
        "VIPIND.NS",
    ],
    "🚗 7. Auto, EV & Auto Components (130 Stocks)": [
        "TATAMOTORS.NS",
        "MARUTI.NS",
        "M&M.NS",
        "HEROMOTOCO.NS",
        "BAJAJ-AUTO.NS",
        "EICHERMOT.NS",
        "SONACOMS.NS",
        "MOTHERSON.NS",
        "BOSCHLTD.NS",
        "EXIDEIND.NS",
        "OLECTRA.NS",
        "TUBEINVEST.NS",
        "BALKRISIND.NS",
        "BHARATFORG.NS",
        "ASHOKLEY.NS",
        "TVSMOTOR.NS",
        "AMARAJA.NS",
        "FORCEPOL.NS",
        "CRAFTSMAN.NS",
        "SUPRAJIT.NS",
        "LUMAXIND.NS",
        "ENDURANCE.NS",
        "UNOMINDA.NS",
        "ESCORTS.NS",
        "SCHAEFFLER.NS",
        "TIMKEN.NS",
        "SKFINDIA.NS",
        "SUBROS.NS",
        "SWARAJENG.NS",
        "SUNDRMFAST.NS",
        "JBMA.NS",
        "GREAVESCOTT.NS",
        "SJS.NS",
        "PRICOLLTD.NS",
        "SANSERA.NS",
        "APOLLOTYRE.NS",
        "CEATLTD.NS",
        "MRF.NS",
        "JKTYRE.NS",
        "VARROC.NS",
        "BANCOINDIA.NS",
        "GABRIEL.NS",
        "FIEMIND.NS",
        "AUTOAXLES.NS",
        "JAMNAAUTO.NS",
        "WHEELS.NS",
        "TALBROSAUTO.NS",
        "LUMAXTECH.NS",
        "MUNJALSHOW.NS",
        "SMLISUZU.NS",
        "ATULAUTO.NS",
        "MAHSCOOTER.NS",
        "VSTTILLERS.NS",
        "GNA.NS",
        "MENONBE.NS",
        "RICOAUTO.NS",
        "INDNIPPON.NS",
        "LGBALAKR.NS",
        "JAYBARMARU.NS",
        "SANDHAR.NS",
        "SSWL.NS",
        "MINDACORP.NS",
        "SALZERELEC.NS",
        "SHARDAMOTR.NS",
        "AUTOMOTIVE.NS",
        "PITTIENG.NS",
        "NELCAST.NS",
        "DIVGIITTS.NS",
        "LANDMARK.NS",
        "EUREKAFORB.NS",
        "KROSS.NS",
    ],
    "🛡️ 8. Defense, Aerospace & Capital Goods (130 Stocks)": [
        "HAL.NS",
        "BEL.NS",
        "MAZDOCK.NS",
        "COCHINSHIP.NS",
        "GRSE.NS",
        "BDL.NS",
        "DATAPATTNS.NS",
        "PARAS.NS",
        "MTARTECH.NS",
        "IDEAFORGE.NS",
        "L&T.NS",
        "SIEMENS.NS",
        "ABB.NS",
        "CGPOWER.NS",
        "SUZLON.NS",
        "INOXWIND.NS",
        "BHEL.NS",
        "CUMMINSIND.NS",
        "THERMAX.NS",
        "TRIVENI.NS",
        "TDPOWERSYS.NS",
        "KIRLOSENG.NS",
        "AIAENG.NS",
        "ELECTCAST.NS",
        "KEC.NS",
        "KALPATPOWR.NS",
        "ENGINERSIN.NS",
        "VATECH.NS",
        "IONEXCHANG.NS",
        "PRAJIND.NS",
        "TEXRAIL.NS",
        "TITAGARH.NS",
        "RAILTEL.NS",
        "RITES.NS",
        "RVNL.NS",
        "IRCON.NS",
    ],
    "🏗️ 9. Metals, Mining & Cement (100 Stocks)": [
        "TATASTEEL.NS",
        "JSWSTEEL.NS",
        "HINDALCO.NS",
        "JINDALSTEL.NS",
        "VEDL.NS",
        "SAIL.NS",
        "NMDC.NS",
        "NATIONALUM.NS",
        "HINDZINC.NS",
        "HINDCOPPER.NS",
        "ULTRACEMCO.NS",
        "GRASIM.NS",
        "AMBUJACEM.NS",
        "ACC.NS",
        "DALBHARAT.NS",
        "SHREECEM.NS",
        "JKCEMENT.NS",
        "RAMCOCEM.NS",
        "BIRLACORPN.NS",
        "APLAPOLLO.NS",
        "RATNAMANI.NS",
        "JSL.NS",
        "JINDALSAW.NS",
        "WELCORP.NS",
        "MAHSEAMLES.NS",
        "MOIL.NS",
        "GMDC.NS",
        "KIOCL.NS",
        "ELECTCAST.NS",
        "MIDHANI.NS",
        "GALLANTT.NS",
        "ISMTLTD.NS",
        "GODAWARI.NS",
        "SardaENERGY.NS",
        "SURYAROSH.NS",
        "KAJARIRCER.NS",
        "SOMANYCERA.NS",
        "CERA.NS",
        "ORIENTBELL.NS",
        "PRINCEPIPE.NS",
        "ASTRAL.NS",
        "SUPREMEIND.NS",
        "FINPIPE.NS",
        "KESORAMIND.NS",
        "STARCEMENT.NS",
        "ORIENTCEM.NS",
        "NCLIND.NS",
        "BHARATWIRE.NS",
        "SHANKARA.NS",
        "PENIND.NS",
        "GOODLUCK.NS",
        "CENTURYTEX.NS",
        "RAYMOND.NS",
        "SWANENERGY.NS",
        "ALOKINDS.NS",
        "KPRMILL.NS",
        "LUXIND.NS",
        "PAGEIND.NS",
        "RUPA.NS",
        "DOLLAR.NS",
        "TRIDENT.NS",
        "WELSPUNLIV.NS",
        "INDOCOUNT.NS",
        "FILATEX.NS",
        "RSWM.NS",
        "BANSWR.NS",
        "SUTLEJTEX.NS",
        "GARFIBRES.NS",
        "GOCOLORS.NS",
        "VEDANTFASH.NS",
        "ETHOSLTD.NS",
        "TITAN.NS",
    ],
    "⚡ 10. Renewable Energy, Power & Utilities (80 Stocks)": [
        "NTPC.NS",
        "POWERGRID.NS",
        "TATAPOWER.NS",
        "IREDA.NS",
        "SUZLON.NS",
        "ADANIGREEN.NS",
        "ADANIPOWER.NS",
        "NHPC.NS",
        "INOXWIND.NS",
        "KPIGREEN.NS",
        "TORNTPOWER.NS",
        "CESC.NS",
        "JSWENERGY.NS",
        "ADANIENT.NS",
        "BHEL.NS",
        "BORORENEW.NS",
        "GENUSPOWER.NS",
        "SCHNEIDER.NS",
        "CGPOWER.NS",
        "SIEMENS.NS",
        "ABB.NS",
        "CUMMINSIND.NS",
        "KEC.NS",
        "KALPATPOWR.NS",
        "RITES.NS",
        "ENGINERSIN.NS",
        "VATECH.NS",
        "IONEXCHANG.NS",
        "AIAENG.NS",
        "THERMAX.NS",
        "TDPOWERSYS.NS",
        "KIRLOSENG.NS",
        "TRIVENI.NS",
        "PRAJIND.NS",
        "GAIL.NS",
        "PETRONET.NS",
        "MGL.NS",
        "IGL.NS",
        "GUJGASLTD.NS",
        "ATGL.NS",
        "GSPL.NS",
        "RELIANCE.NS",
        "ONGC.NS",
        "OIL.NS",
    ],
}

# ইউজার ইন্টারফেস কন্ট্রোলস
c_top1, c_top2 = st.columns([2, 2])
with c_top1:
    selected_category = st.selectbox(
        "একটি সাব-সেক্টর বেছে নিন:", list(SUB_SECTORS.keys())
    )
with c_top2:
    timeframe_option = st.selectbox(
        "ক্যান্ডেল টাইমফ্রেম (Timeframe):",
        ["1 Day (Daily)", "4 Hours (4h)", "1 Hour (1h)", "15 Minutes (15m)"],
    )

selected_price_status = st.multiselect(
    "🎯 প্রাইস রেঞ্জ সিলেক্ট করুন:",
    ["🟢 In Range (₹500 - ₹2,000)", "🔴 Above ₹2,000", "🟡 Below ₹500"],
    default=["🟢 In Range (₹500 - ₹2,000)", "🔴 Above ₹2,000", "🟡 Below ₹500"],
)

st.write("")
start_scan = st.button(
    "🔍 স্ক্যান শুরু করুন", use_container_width=True, type="primary"
)


def fetch_stock_data(ticker, tf_choice):
    stock = yf.Ticker(ticker)
    if tf_choice == "1 Day (Daily)":
        return stock.history(period="3mo", interval="1d")
    elif tf_choice == "4 Hours (4h)":
        df = stock.history(period="2mo", interval="1h")
        if not df.empty:
            df = (
                df.resample("4h")
                .agg({
                    "Open": "first",
                    "High": "max",
                    "Low": "min",
                    "Close": "last",
                    "Volume": "sum",
                })
                .dropna()
            )
        return df
    elif tf_choice == "1 Hour (1h)":
        return stock.history(period="1mo", interval="1h")
    elif tf_choice == "15 Minutes (15m)":
        return stock.history(period="5d", interval="15m")
    return pd.DataFrame()


def analyze_stock(df):
    if len(df) < 50:
        return None

    c1 = df.iloc[-1]
    c2 = df.iloc[-2]
    open1, close1, high1, low1 = c1["Open"], c1["Close"], c1["High"], c1["Low"]
    open2, close2, high2, low2 = c2["Open"], c2["Close"], c2["High"], c2["Low"]

    # প্রাইস ক্যাটাগরি নির্ধারণ
    if close1 < 500:
        price_status = "🟡 Below ₹500"
    elif 500 <= close1 <= 2000:
        price_status = "🟢 In Range (₹500 - ₹2,000)"
    else:
        price_status = "🔴 Above ₹2,000"

    body1 = abs(close1 - open1)
    range1 = high1 - low1
    if range1 == 0:
        return None

    lower_shadow1 = min(open1, close1) - low1
    upper_shadow1 = high1 - max(open1, close1)

    # ৫০ দিনের ডেটা ও Higher Low লজিক
    full_history = df.iloc[-50:]
    sma_50 = full_history["Close"].mean()
    recent_low = full_history["Low"].min()
    recent_high = full_history["High"].max()

    # ট্রেন্ড এবং Higher Low জোন ভ্যালিডেশন
    is_not_in_heavy_downtrend = close1 >= sma_50 * 0.85
    is_higher_low = low1 >= recent_low * 0.95 and low1 <= recent_low * 1.15
    is_at_support = low1 <= recent_low * 1.05 or close1 <= sma_50 * 1.05
    is_at_resistance = high1 >= recent_high * 0.98

    pattern = "⚪ No Pattern"
    type_tag = "None"

    # 🟢 Higher Low এবং সাপোর্টে আপনার নির্দিষ্ট ক্যান্ডেলস্টিক প্যাটার্নসমূহ
    if is_not_in_heavy_downtrend and (is_higher_low or is_at_support):

        # ১. Hammer (হ্যামার)
        if (
            (close1 > open1)
            and (lower_shadow1 >= 2 * body1)
            and (upper_shadow1 <= 0.3 * body1)
        ):
            pattern = "🔨 Bullish Hammer (HL Support)"
            type_tag = "Bullish"

        # ২. Inverse Hammer (ইনভার্স হ্যামার)
        elif (
            (close1 > open1)
            and (upper_shadow1 >= 2 * body1)
            and (lower_shadow1 <= 0.3 * body1)
        ):
            pattern = "🔨 Inverse Hammer (HL Support)"
            type_tag = "Bullish"

        # ৩. Bullish Engulfing (বুলিশ এনগাল্ফিং)
        elif (
            (c2["Close"] < c2["Open"])
            and (close1 > open1)
            and (close1 >= c2["Open"])
            and (open1 <= c2["Close"])
        ):
            pattern = "🔥 Bullish Engulfing (HL Support)"
            type_tag = "Bullish"

        # ৪. Piercing Line (পিয়ার্সিং লাইন)
        elif (
            (c2["Close"] < c2["Open"])
            and (close1 > open1)
            and (open1 < c2["Low"])
            and (close1 >= (c2["Open"] + c2["Close"]) / 2)
        ):
            pattern = "⚡ Piercing Line (HL Support)"
            type_tag = "Bullish"

        # ৫. Dragonfly Doji (ড্রাগনফ্লাই ডোজি)
        elif (
            abs(close1 - open1) <= 0.1 * range1
            and (lower_shadow1 >= 0.6 * range1)
            and (upper_shadow1 <= 0.1 * range1)
        ):
            pattern = "🪲 Dragonfly Doji (HL Support)"
            type_tag = "Bullish"

        # ৬. Doji (ডোজি)
        elif (
            abs(close1 - open1) <= 0.1 * range1
            and lower_shadow1 >= 0.3 * range1
            and upper_shadow1 >= 0.3 * range1
        ):
            pattern = "➕ Standard Doji (HL Support)"
            type_tag = "Bullish"

        # ৭. Spinning Top (স্পিনিং টপ)
        elif (
            body1 <= 0.3 * range1
            and lower_shadow1 >= 0.3 * range1
            and upper_shadow1 >= 0.3 * range1
        ):
            pattern = "🌀 Spinning Top (HL Support)"
            type_tag = "Bullish"

    # 🔴 বেয়ারিশ প্যাটার্ন (রেজিস্ট্যান্সের জন্য)
    if is_at_resistance and type_tag == "None":
        if (
            (c2["Close"] > c2["Open"])
            and (close1 < open1)
            and (close1 <= c2["Open"])
            and (open1 >= c2["Close"])
        ):
            pattern = "❄️ Bearish Engulfing"
            type_tag = "Bearish"

    if type_tag == "None":
        return None

    buyer_power = round(((close1 - low1) / range1) * 100, 1)
    seller_power = round(((high1 - close1) / range1) * 100, 1)

    return {
        "Price": round(close1, 2),
        "Price_Status": price_status,
        "Pattern": pattern,
        "Type": type_tag,
        "Buyer Power (%)": buyer_power,
        "Seller Power (%)": seller_power,
    }


def render_cards(items):
    for item in items:
        with st.container():
            c1, c2, c3, c4 = st.columns([2.5, 2, 3, 2])
            stock_name = item["Stock"]
            groww_url = f"https://groww.in/stocks/{stock_name.lower()}"
            tv_url = (
                f"https://in.tradingview.com/chart/?symbol=NSE:{stock_name}"
            )

            with c1:
                st.markdown(f"### {stock_name}")
                st.caption(
                    f"LTP: ₹{item['Price']} | {item['Price_Status']}"
                )
            with c2:
                st.write(f"**{item['Pattern']}**")
            with c3:
                b_pow = item["Buyer Power (%)"]
                s_pow = item["Seller Power (%)"]
                st.progress(
                    int(b_pow),
                    text=f"🟢 {b_pow}% Buyers | 🔴 {s_pow}% Sellers",
                )
            with c4:
                st.link_button("🚀 Open in Groww", groww_url)
                st.link_button("📈 TradingView", tv_url)
            st.divider()


if start_scan:
    st.write(
        f"**{selected_category}** সেকশনে সম্পূর্ণ স্টক লিস্ট এবং Higher Low"
        " ক্যান্ডেল প্যাটার্ন স্ক্যান করা হচ্ছে..."
    )

    bullish_results = []
    bearish_results = []
    tickers = SUB_SECTORS[selected_category]
    progress = st.progress(0)

    for idx, ticker in enumerate(tickers):
        try:
            data = fetch_stock_data(ticker, timeframe_option)
            res = analyze_stock(data)
            if res and res["Pattern"] != "⚪ No Pattern":
                if res["Price_Status"] in selected_price_status:
                    clean_name = ticker.replace(".NS", "")
                    card_data = {
                        "Stock": clean_name,
                        "Price": res["Price"],
                        "Price_Status": res["Price_Status"],
                        "Pattern": res["Pattern"],
                        "Buyer Power (%)": res["Buyer Power (%)"],
                        "Seller Power (%)": res["Seller Power (%)"],
                    }
                    if res["Type"] == "Bullish":
                        bullish_results.append(card_data)
                    elif res["Type"] == "Bearish":
                        bearish_results.append(card_data)
        except Exception:
            pass
        progress.progress((idx + 1) / len(tickers))

    st.success("স্ক্যানিং সম্পন্ন!")

    tab_bullish, tab_bearish = st.tabs([
        f"🟢 Bullish Setups ({len(bullish_results)})",
        f"🔴 Bearish Setups ({len(bearish_results)})",
    ])

    with tab_bullish:
        if bullish_results:
            st.subheader(
                "🟢 Higher Low ও সাপোর্টে তৈরি হওয়া বুলিশ প্যাটার্ন সেটআপ:"
            )
            render_cards(bullish_results)
        else:
            st.info(
                "⚠️ নির্বাচিত ফিল্টার অনুযায়ী এই মুহূর্তে কোনো স্টকে এই প্যাটার্নগুলো"
                " পাওয়া যায়নি।"
            )

    with tab_bearish:
        if bearish_results:
            st.subheader("🔴 রেজিস্ট্যান্সে তৈরি হওয়া বেয়ারিশ সেটআপ:")
            render_cards(bearish_results)
        else:
            st.info(
                "⚠️ নির্বাচিত ফিল্টার অনুযায়ী এই মুহূর্তে কোনো বেয়ারিশ সেটআপ"
                " পাওয়া যায়নি।"
            )
