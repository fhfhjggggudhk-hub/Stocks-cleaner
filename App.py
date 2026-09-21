import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="AI Stock Screener Pro", layout="wide")

st.title("⚡ AI Stock Screener Pro (All-Stock Pattern Scanner)")
st.caption(
    "১০টি সাব-সেক্টরের ১,১০৫টি টপ স্টকের অল-প্রাইস ক্যান্ডেলস্টিক স্ক্যানার।"
    " দামের উপর ভিত্তি করে কালার-ট্যাগিং যুক্ত করা হয়েছে।"
)

# ১০টি সাব-সেক্টরে আপনার নির্দিষ্ট করা ১,১০৫টি স্টক
SUB_SECTORS = {
    "🏦 1. Banking, Finance & NBFC (160 Stocks)": [
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
        "CREDACC.NS",
        "POONAWALLA.NS",
        "IIFL.NS",
        "PEL.NS",
        "CANFINHOME.NS",
        "HOMEFIRST.NS",
        "HUDCO.NS",
        "MAXFIN.NS",
        "ABCAPITAL.NS",
        "ICICIPRULI.NS",
        "HDFCLIFE.NS",
        "SBILIFE.NS",
        "LICI.NS",
        "PAYTM.NS",
        "POLICYBZR.NS",
        "PSB.NS",
        "INDIABULLS.NS",
        "DCBBANK.NS",
        "FINPIPE.NS",
        "JMFINANCIL.NS",
        "IBULHSGFIN.NS",
        "EDELWEISS.NS",
        "MOTILALOFS.NS",
        "ANGELONE.NS",
        "5PAISA.NS",
        "ISEC.NS",
        "BSE.NS",
        "MCX.NS",
        "UTIAMC.NS",
        "NAM-INDIA.NS",
        "HDFCAMC.NS",
        "NIVAPUPA.NS",
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
        "JSFB.NS",
        "UTKARSHBNK.NS",
        "FINOPB.NS",
        "KOTAKGOLD.NS",
        "KALYANKJIL.NS",
        "GEOJITFSL.NS",
        "SMIFS.NS",
        "MONARCH.NS",
        "DBREALTY.NS",
        "CHAMBLFERT.NS",
        "GSFC.NS",
        "FACT.NS",
        "RCF.NS",
        "NFL.NS",
        "GNFC.NS",
        "SPIC.NS",
        "MANGCHEFER.NS",
        "MADRASFERT.NS",
        "ZUARI.NS",
        "DEEPAKFERT.NS",
        "SBICARD.NS",
        "SUNDARMFIN.NS",
        "NUVAMA.NS",
        "360ONE.NS",
        "KFINTECH.NS",
        "CAMSLTD.NS",
        "CDSL.NS",
        "INDIAGLYCO.NS",
        "NIFTYBEES.NS",
        "BANKBEES.NS",
        "GICHSGFIN.NS",
        "DHANI.NS",
        "IFCI.NS",
        "TFCI.NS",
        "SRTRANSFIN.NS",
        "RELIGARE.NS",
        "SREINFRA.NS",
        "SASTASUNDR.NS",
        "ALANKIT.NS",
        "VAKRANGEE.NS",
        "ISFT.NS",
        "L&TFH.NS",
        "MANGALAM.NS",
        "CANTABIL.NS",
        "STFC.NS",
        "AMBER.NS",
        "HATHWAY.NS",
        "DEN.NS",
        "J&KBANK.NS",
        "MUTHOOTCAP.NS",
        "BAJAJHFL.NS",
        "SBFC.NS",
        "NORTHERNARC.NS",
        "MANBA.NS",
        "IXIGO.NS",
        "PAYTM.NS",
        "EASEMYTRIP.NS",
        "FIVESTAR.NS",
        "AETHER.NS",
        "KIMS.NS",
        "MEDANTA.NS",
        "CHOICEIN.NS",
        "SMCGLOBAL.NS",
        "MONEYBOXX.NS",
        "DCMSRIRAM.NS",
        "KOTHARIPET.NS",
        "FINCABLES.NS",
        "SUMIT.NS",
        "SEPC.NS",
        "INDSTAR.NS",
        "MFS.NS",
        "SRG.NS",
        "GICRE.NS",
        "NOCIL.NS",
        "HIKAL.NS",
        "INVENTURE.NS",
        "BGRENERGY.NS",
        "DOLAT.NS",
        "ARIHANTCAP.NS",
    ],
    "⛽ 2. Oil, Gas, Energy & Chemicals (140 Stocks)": [
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
        "SJWN.NS",
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
        "JAYAGRO.NS",
        "BALRAMCHIN.NS",
        "TRIVENI.NS",
        "RENUKA.NS",
        "EIDPARRY.NS",
        "BAJAJHIND.NS",
        "DHARAMSI.NS",
        "PRAJIND.NS",
        "GOCLCORP.NS",
        "EXCELINDUS.NS",
        "SURYAROSH.NS",
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
        "SURAJEST.NS",
        "PRIVISCL.NS",
        "FINEOTEX.NS",
        "ASTEC.NS",
        "DCW.NS",
        "TINPLATE.NS",
        "SHARDACROP.NS",
        "CAMLINFINE.NS",
        "GOCL.NS",
        "CHEMFAB.NS",
        "ORIENTCARBON.NS",
        "THIRUMALAI.NS",
        "KOTARISUG.NS",
        "UGARSUGAR.NS",
        "MAGADSUGAR.NS",
        "DALMIASUG.NS",
        "DWARKESH.NS",
        "UTAMSUGAR.NS",
        "AVADHSUGAR.NS",
        "APCOTEXINFO.NS",
        "KIRLOSENG.NS",
        "SOTL.NS",
        "ANURAS.NS",
        "AMIORG.NS",
        "AETHER.NS",
        "TATVA.NS",
        "SURYODAY.NS",
        "LAXMICHEM.NS",
        "EPIGRAL.NS",
        "KROSS.NS",
        "PARAMOUNT.NS",
        "DILIPBUILD.NS",
        "JISLJALEQS.NS",
        "GIPCL.NS",
        "HINDOILEXP.NS",
        "SELAN.NS",
        "GEOJITFSL.NS",
        "CONFIPET.NS",
    ],
    "🏥 3. Pharma, Healthcare & Biotech (130 Stocks)": [
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
        "SOLARA.NS",
        "SHILPAMED.NS",
        "FDC.NS",
        "DISHMAN.NS",
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
        "SYNCOM.NS",
        "TTKHLTCARE.NS",
        "UNICHEMLAB.NS",
        "VENUSREM.NS",
        "WOCKPHARMA.NS",
        "ZEEL.NS",
        "YATHARTH.NS",
        "ARTEMISMED.NS",
        "INDOCO.NS",
        "HESTERBIO.NS",
        "JAGSNPHARM.NS",
        "BLISSGVS.NS",
        "SHALBY.NS",
        "SIGACHI.NS",
        "TARSONS.NS",
        "MEDICO.NS",
        "NOVARTIND.NS",
        "BAYERCROP.NS",
        "DHANUKA.NS",
        "BASF.NS",
        "RALLIS.NS",
        "INSECTICID.NS",
        "ASTEC.NS",
        "SHARDACROP.NS",
        "BHAGCHEM.NS",
        "BESTAGRO.NS",
        "AARTIIND.NS",
        "DEEPAKNTR.NS",
        "TATACHEM.NS",
        "SUMICHEM.NS",
        "FINEORG.NS",
        "INNOVA.NS",
        "AKUMS.NS",
        "JUBILANT.NS",
        "NGLFINE.NS",
        "BETA.NS",
        "SANSERA.NS",
        "SUVEN.NS",
        "MEDPLUS.NS",
        "HEALTHIUM.NS",
        "KRSNAA.NS",
        "ENTERO.NS",
        "WINDLAS.NS",
        "SANGHVI.NS",
        "AMRUTANJAN.NS",
        "VIMTALABS.NS",
        "BACIL.NS",
        "BLISSGVS.NS",
        "COROMANDEL.NS",
        "GUFICBIO.NS",
        "HESTERBIO.NS",
        "INDAG.NS",
        "KOPRAN.NS",
        "MALLCOM.NS",
        "NECTARLIFE.NS",
        "ORIENTBELL.NS",
        "PHARMACEUT.NS",
        "RUBYMILLS.NS",
        "SADBHAV.NS",
        "TASTYBITE.NS",
        "UNIVCABLES.NS",
        "VALIANTORG.NS",
        "VASCONEQ.NS",
        "ZOTA.NS",
    ],
    "🛒 4. FMCG, Retail & Consumer Durables (110 Stocks)": [
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
        "RESTAURANT.NS",
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
        "SKMEGGPROD.NS",
        "AVANTIFEED.NS",
        "APEX.NS",
        "CCL.NS",
        "TCPLPACK.NS",
        "UFO.NS",
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
        "KOTHARIPET.NS",
        "BALRAMCHIN.NS",
        "RENUKA.NS",
        "KIRLOSIND.NS",
        "BORORENEW.NS",
        "AGARIND.NS",
        "IFBAGRO.NS",
        "ADFFOODS.NS",
        "TASTYBITE.NS",
        "VAKRANGEE.NS",
        "MIRZAINT.NS",
        "LIBERTSHOE.NS",
        "KHADIM.NS",
        "ZODIACLOTH.NS",
        "SPENCERS.NS",
        "MOREPENLAB.NS",
        "LANDMARK.NS",
        "ETHOSLTD.NS",
        "VMART.NS",
        "GOKEX.NS",
        "CANTABIL.NS",
        "VIPIND.NS",
    ],
    "💻 5. IT, Software & Tech Services (105 Stocks)": [
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
        "CSOFT.NS",
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
        "HINDUJAVENT.NS",
        "ALLSEC.NS",
        "HOVS.NS",
        "MPSLTD.NS",
        "INTEGRA.NS",
        "INFOMEDIA.NS",
        "TREJHARA.NS",
        "PROZONER.NS",
        "DATAMATICS.NS",
        "SILLYMONKS.NS",
        "CREATIVE.NS",
        "VIRTUALG.NS",
        "SIGNPOST.NS",
        "GTLINFRA.NS",
        "SURANAIND.NS",
        "SOFTTECH.NS",
        "INNOVANA.NS",
        "AXISCADES.NS",
        "ALANKIT.NS",
        "VAKRANGEE.NS",
        "GIRESI.NS",
        "KALYANI.NS",
        "BSE.NS",
        "SADBHAV.NS",
        "ONWARDTEC.NS",
        "TRIGYN.NS",
        "SILLYMONK.NS",
        "DREAMFOLKS.NS",
        "AWANTECH.NS",
        "MAPMYINDIA.NS",
        "SILLYMONKS.NS",
        "AARTISC.NS",
        "KPIT.NS",
        "SADBHAV.NS",
        "BLS.NS",
        "E2E.NS",
        "XELPMOC.NS",
    ],
    "🏗️ 6. Metals, Mining & Cement (90 Stocks)": [
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
        "HEidelberg.NS",
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
        "MISHTI.NS",
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
        "SAGARDEEP.NS",
        "UBL.NS",
        "MCDOWELL-N.NS",
        "VBL.NS",
        "SANGHIIND.NS",
        "STARCEMENT.NS",
        "ORIENTCEM.NS",
        "DECCANCE.NS",
        "NCLIND.NS",
        "MANAKSTEEL.NS",
        "BHARATWIRE.NS",
        "SHANKARA.NS",
        "PENIND.NS",
        "GOODLUCK.NS",
        "HI-TECH.NS",
        "BOMDYEING.NS",
        "CENTURYTEX.NS",
        "RAYMOND.NS",
        "SWANENERGY.NS",
        "ALOKINDS.NS",
        "KPRMILL.NS",
        "LUXIND.NS",
        "PAGEIND.NS",
        "RUPA.NS",
        "DOLLAR.NS",
        "GOKEX.NS",
        "TRIDENT.NS",
        "WELSPUNLIV.NS",
        "SPENTEX.NS",
        "HIMATSEIDE.NS",
        "NITIIN.NS",
        "INDOCOUNT.NS",
        "FILATEX.NS",
        "RSWM.NS",
        "BANSWR.NS",
        "SUTLEJTEX.NS",
        "VARDHACRLC.NS",
        "GARFIBRES.NS",
        "JIKIND.NS",
        "TCNSBRANDS.NS",
        "GOCOLORS.NS",
        "VEDANTFASH.NS",
        "ETHOSLTD.NS",
        "TITAN.NS",
    ],
    "🚗 7. Auto, EV & Auto Components (95 Stocks)": [
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
        "TIINDIA.NS",
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
        "RAMKRASN.NS",
        "VARROC.NS",
        "BANCOINDIA.NS",
        "MHRIL.NS",
        "GABRIEL.NS",
        "FIEMIND.NS",
        "AUTOAXLES.NS",
        "JAMNAAUTO.NS",
        "WHEELS.NS",
        "TALBROSAUTO.NS",
        "RANEHOLDIN.NS",
        "LUMAXTECH.NS",
        "MUNJALSHOW.NS",
        "SMLISUZU.NS",
        "ATULAUTO.NS",
        "MAHSCOOTER.NS",
        "VSTTILLERS.NS",
        "GNA.NS",
        "MENONBE.NS",
        "RICOAUTO.NS",
        "PRECISION.NS",
        "ASAL.NS",
        "INDNIPPON.NS",
        "RANEENGINE.NS",
        "LGBALAKR.NS",
        "JAYBARMARU.NS",
        "SINTERCOM.NS",
        "SANDHAR.NS",
        "SSWL.NS",
        "MINDACORP.NS",
        "SETCO.NS",
        "SALZERELEC.NS",
        "SHARDAMOTR.NS",
        "AUTOMOTIVE.NS",
        "PITTIENG.NS",
        "NELCAST.NS",
        "INDOBORAX.NS",
        "MMFL.NS",
        "HLEGLAS.NS",
        "DIVGIITTS.NS",
        "LANDMARK.NS",
        "EUREKAFORB.NS",
        "HINDALCO.NS",
        "VEDL.NS",
        "JSL.NS",
        "NATIONALUM.NS",
        "BEL.NS",
        "HAL.NS",
        "MAZDOCK.NS",
        "GRSE.NS",
        "COCHINSHIP.NS",
        "KROSS.NS",
        "MOTHERSON.NS",
        "M&M.NS",
    ],
    "🚂 8. Railways, Logistics & Infrastructure (85 Stocks)": [
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
        "GATEWAY.NS",
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
        "J KUMAR.NS",
        "ITD.NS",
        "NCC.NS",
        "ASHOKA.NS",
        "NSPIL.NS",
        "SADBHAV.NS",
        "SIMPLEX.NS",
        "ENGINERSIN.NS",
        "NBCC.NS",
        "PSPPROJECT.NS",
        "CAPACITE.NS",
        "AHLUCONT.NS",
        "MANINFRA.NS",
        "TEXINFRA.NS",
        "WELENT.NS",
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
        "IBREALEST.NS",
        "KOLTEPATIL.NS",
        "GANESHIN.NS",
        "ASHIANA.NS",
        "PURVA.NS",
        "AJMERA.NS",
        "MARATHON.NS",
        "DBREALTY.NS",
        "PENINLAND.NS",
        "RAMKY.NS",
        "GPTINFRA.NS",
        "RPPINFRA.NS",
        "VPRPL.NS",
        "OMAXE.NS",
        "PARSVNATH.NS",
        "HUBTOWN.NS",
        "SURAJEST.NS",
        "ARKADE.NS",
        "KROSS.NS",
        "GPTHEALTH.NS",
        "GSHIP.NS",
        "ESSARSHPNG.NS",
        "DREDGECORP.NS",
        "SICAL.NS",
        "NAVNETEDUL.NS",
        "SEPC.NS",
        "INDOSTAR.NS",
    ],
    "⚡ 9. Renewable Energy, Power & Utilities (50 Stocks)": [
        "NTPC.NS",
        "POWERGRID.NS",
        "TATAPOWER.NS",
        "IREDA.NS",
        "SUZLON.NS",
        "ADANIGREEN.NS",
        "ADANIPOWER.NS",
        "SJWN.NS",
        "NHPC.NS",
        "INOXWIND.NS",
        "KPIGREEN.NS",
        "TORNTPOWER.NS",
        "CESC.NS",
        "JSWENERGY.NS",
        "ADANIENT.NS",
        "BHEL.NS",
        "BORORENEW.NS",
        "WEBELSOLAR.NS",
        "STERENERGY.NS",
        "SOLEX.NS",
        "GENUSPOWER.NS",
        "HPL.NS",
        "SCHNEIDER.NS",
        "CGPOWER.NS",
        "SIEMENS.NS",
        "ABB.NS",
        "HITACHI.NS",
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
    "🛡️ 10. Defense, Aerospace & Capital Goods (40 Stocks)": [
        "HAL.NS",
        "BEL.NS",
        "MAZDOCK.NS",
        "COCHINSHIP.NS",
        "GRSE.NS",
        "BDL.NS",
        "DATAPATTNS.NS",
        "PARAS.NS",
        "ASTRAENC.NS",
        "MTARTECH.NS",
        "IDEAFORGE.NS",
        "ZENITH.NS",
        "L&T.NS",
        "SIEMENS.NS",
        "ABB.NS",
        "CGPOWER.NS",
        "SUZLON.NS",
        "INOXWIND.NS",
        "HITACHI.NS",
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
        "ACTIONIND.NS",
        "TEXRAIL.NS",
        "TITAGARH.NS",
        "RAILTEL.NS",
        "RITES.NS",
        "RVNL.NS",
        "IRCON.NS",
    ],
}

# ফিল্টার এবং সিলেক্টর
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

# প্রাইস রেঞ্জ দেখার ফিল্টার (ডিফল্টভাবে সব সিলেক্ট করা থাকবে)
selected_price_status = st.multiselect(
    "🎯 যে প্রাইস রেঞ্জের স্টক অ্যাপে দেখতে চান তা টিক দিন:",
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
        df = stock.history(period="1mo", interval="1h")
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
    if len(df) < 21:
        return None

    c1 = df.iloc[-1]
    c2 = df.iloc[-2]
    c3 = df.iloc[-3]

    open1, close1, high1, low1 = c1["Open"], c1["Close"], c1["High"], c1["Low"]
    open2, close2, high2, low2 = c2["Open"], c2["Close"], c2["High"], c2["Low"]
    open3, close3, high3, low3 = c3["Open"], c3["Close"], c3["High"], c3["Low"]

    # 🏷️ কালার-ট্যাগ প্রাইস স্ট্যাটাস নির্ধারণ (কোনো স্টক বাদ দেওয়া হবে না)
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

    prev_df = df.iloc[-21:-1]
    recent_low = prev_df["Low"].min()
    recent_high = prev_df["High"].max()

    is_at_support = low1 <= recent_low * 1.008
    is_at_resistance = high1 >= recent_high * 0.992

    is_green1 = close1 > open1
    is_red1 = close1 < open1
    is_red2 = close2 < open2
    is_green2 = close2 > open2
    is_red3 = close3 < open3
    is_green3 = close3 > open3

    pattern = "⚪ No Pattern"
    type_tag = "None"

    # 🟢 বুলিশ প্যাটার্ন ফিল্টার (সাপোর্টে)
    if is_at_support:
        if (
            is_red3
            and (abs(close2 - open2) <= 0.3 * (high2 - low2))
            and is_green1
            and (close1 > (open3 + close3) / 2)
        ):
            pattern = "🌟 Morning Star"
            type_tag = "Bullish"
        elif (
            is_red2 and is_green1 and (close1 >= open2) and (open1 <= close2)
        ):
            pattern = "🔥 Bullish Engulfing"
            type_tag = "Bullish"
        elif (
            is_red2
            and is_green1
            and (open1 < close2)
            and (close1 > (open2 + close2) / 2)
            and (close1 < open2)
        ):
            pattern = "⚡ Piercing Line"
            type_tag = "Bullish"
        elif (
            is_green1
            and (lower_shadow1 >= 2 * body1)
            and (upper_shadow1 <= 0.2 * body1)
            and (body1 > 0)
        ):
            pattern = "🔨 Green Bullish Hammer"
            type_tag = "Bullish"
        elif (
            is_green1
            and (upper_shadow1 >= 2 * body1)
            and (lower_shadow1 <= 0.2 * body1)
            and (body1 > 0)
        ):
            pattern = "🙃 Inverted Hammer"
            type_tag = "Bullish"
        elif (
            (body1 <= 0.1 * range1)
            and (lower_shadow1 >= 0.6 * range1)
            and (upper_shadow1 <= 0.1 * range1)
        ):
            pattern = "🐉 Dragonfly Doji"
            type_tag = "Bullish"

    # 🔴 বেয়ারিশ প্যাটার্ন ফিল্টার (রেজিস্ট্যান্সে)
    if is_at_resistance and type_tag == "None":
        if (
            is_green3
            and (abs(close2 - open2) <= 0.3 * (high2 - low2))
            and is_red1
            and (close1 < (open3 + close3) / 2)
        ):
            pattern = "🌩️ Evening Star"
            type_tag = "Bearish"
        elif (
            is_green2 and is_red1 and (close1 <= open2) and (open1 >= close2)
        ):
            pattern = "❄️ Bearish Engulfing"
            type_tag = "Bearish"
        elif (
            is_green2
            and is_red1
            and (open1 > close2)
            and (close1 < (open2 + close2) / 2)
            and (close1 > open2)
        ):
            pattern = "🌧️ Dark Cloud Cover"
            type_tag = "Bearish"
        elif (
            is_red1
            and (upper_shadow1 >= 2 * body1)
            and (lower_shadow1 <= 0.2 * body1)
            and (body1 > 0)
        ):
            pattern = "🌠 Shooting Star"
            type_tag = "Bearish"
        elif (
            is_red1
            and (lower_shadow1 >= 2 * body1)
            and (upper_shadow1 <= 0.2 * body1)
            and (body1 > 0)
        ):
            pattern = "🪢 Hanging Man"
            type_tag = "Bearish"
        elif (
            (body1 <= 0.1 * range1)
            and (upper_shadow1 >= 0.6 * range1)
            and (lower_shadow1 <= 0.1 * range1)
        ):
            pattern = "🪦 Gravestone Doji"
            type_tag = "Bearish"

    buyer_power = round(((close1 - low1) / range1) * 100, 1)
    seller_power = round(((high1 - close1) / range1) * 100, 1)

    return {
        "Price": round(close1, 2),
        "Price_Status": price_status,
        "Pattern": pattern,
        "Type": type_tag,
        "Buyer Power %": buyer_power,
        "Seller Power %": seller_power,
    }


def render_cards(items):
    for item in items:
        with st.container():
            c1, c2, c3, c4 = st.columns([2.5, 2, 3, 2])
            stock_name = item["Stock"]
            groww_url = f"https://groww.in/search?q={stock_name}"
            tv_url = (
                f"https://in.tradingview.com/chart/?symbol=NSE:{stock_name}"
            )

            with c1:
                st.markdown(f"### **{stock_name}**")
                st.caption(
                    f"LTP: **₹{item['Price']}** | {item['Price_Status']}"
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
        f"**{selected_category}** সেকশনে সমস্ত স্টকের ক্যান্ডেলস্টিক প্যাটার্ন"
        " স্ক্যান করা হচ্ছে..."
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
                # সিলেক্ট করা প্রাইস ট্যাগ অনুসারে ফিল্টার
                if res["Price_Status"] in selected_price_status:
                    clean_name = ticker.replace(".NS", "")
                    card_data = {
                        "Stock": clean_name,
                        "Price": res["Price"],
                        "Price_Status": res["Price_Status"],
                        "Pattern": res["Pattern"],
                        "Buyer Power (%)": res["Buyer Power %"],
                        "Seller Power (%)": res["Seller Power %"],
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
            st.subheader("🟢 সাপোর্টে তৈরি হওয়া বুলিশ সেটআপ:")
            render_cards(bullish_results)
        else:
            st.info(
                "⚠️ নির্বাচিত ফিল্টার অনুযায়ী এই মুহূর্তে কোনো স্টকে বুলিশ"
                " রিভার্সাল পাওয়া যায়নি।"
            )

    with tab_bearish:
        if bearish_results:
            st.subheader("🔴 রেজিস্ট্যান্সে তৈরি হওয়া বেয়ারিশ সেটআপ:")
            render_cards(bearish_results)
        else:
            st.info(
                "⚠️ নির্বাচিত ফিল্টার অনুযায়ী এই মুহূর্তে কোনো স্টকে বেয়ারিশ"
                " রিভার্সাল পাওয়া যায়নি।"
            )
