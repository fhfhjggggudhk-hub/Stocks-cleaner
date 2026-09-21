import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="AI Stock Screener Pro", layout="wide")

st.title("⚡ AI Stock Screener Pro (Support & Resistance Precision)")
st.caption("প্রপার সাপোর্ট ও রেজিস্ট্যান্স লেভেলে তৈরি হওয়া বুলিশ এবং বেয়ারিশ রিভার্সাল প্যাটার্ন।")

# ১০টি সাব-সেক্টরে ১০০০টি শীর্ষ স্টক
SUB_SECTORS = {
    "🏦 1. Banking, Finance & NBFC (100 Stocks)": [
        "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS", 
        "MUTHOOTFIN.NS", "INDUSINDBK.NS", "BANKBARODA.NS", "PNB.NS", "FEDERALBNK.NS", "IDFCFIRSTB.NS", "AUBANK.NS", 
        "CANBK.NS", "UNIONBANK.NS", "BANDHANBNK.NS", "CHOLAFIN.NS", "SHRIRAMFIN.NS", "M&MFIN.NS", "LICHSGFIN.NS", 
        "RECLTD.NS", "PFC.NS", "MANAPPURAM.NS", "J&KBANK.NS", "KARURVYSYA.NS", "SOUTHBANK.NS", "CUB.NS", 
        "EQUITASBNK.NS", "UJJIVANSFB.NS", "MAHABANK.NS", "CENTRALBK.NS", "IOB.NS", "BANKINDIA.NS", "UCOBANK.NS", 
        "CREDACC.NS", "POONAWALLA.NS", "IIFL.NS", "PEL.NS", "CANFINHOME.NS", "HOMEFIRST.NS", "HUDCO.NS", 
        "MAXFIN.NS", "ABCAPITAL.NS", "ICICIPRULI.NS", "HDFCLIFE.NS", "SBILIFE.NS", "LICI.NS", "PAYTM.NS", "POLICYBZR.NS",
        "PSB.NS", "INDIABULLS.NS", "DCBBANK.NS", "FINPIPE.NS", "JMFINANCIL.NS", "IBULHSGFIN.NS", "EDELWEISS.NS", 
        "MOTILALOFS.NS", "ANGELONE.NS", "5PAISA.NS", "ISEC.NS", "BSE.NS", "MCX.NS", "UTIAMC.NS", "NAM-INDIA.NS", 
        "HDFCAMC.NS", "NIVAPUPA.NS", "STARHEALTH.NS", "ICICIGI.NS", "GICRE.NS", "NIACL.NS", "PNBHOUSING.NS", 
        "AAVAS.NS", "REPCOHOME.NS", "MASFIN.NS", "ARMANFIN.NS", "SURYODAY.NS", "ESAFSFB.NS", "JSFB.NS", 
        "UTKARSHBNK.NS", "FINOPB.NS", "KOTAKGOLD.NS", "KALYANKJIL.NS", "GEOJITFSL.NS", "SMIFS.NS", "MONARCH.NS", 
        "DBREALTY.NS", "CHAMBLFERT.NS", "GSFC.NS", "FACT.NS", "RCF.NS", "NFL.NS", "GNFC.NS", "SPIC.NS", 
        "MANGCHEFER.NS", "MADRASFERT.NS", "ZUARI.NS", "DEEPAKFERT.NS"
    ],
    "💻 2. IT, Software & Tech Services (100 Stocks)": [
        "TCS.NS", "INFY.NS", "WIPRO.NS", "TECHM.NS", "HCLTECH.NS", "PERSISTENT.NS", "COFORGE.NS", "LTIM.NS", 
        "MPHASIS.NS", "LTTS.NS", "TATAELXSI.NS", "KPITTECH.NS", "CYIENT.NS", "OFSS.NS", "ZENSARTECH.NS", 
        "BSOFT.NS", "HAPPSTMNDS.NS", "INTELLECT.NS", "TATACOMM.NS", "MASTEK.NS", "SONATSOFTW.NS", "ECLERX.NS", 
        "DATAPATTNS.NS", "NETWEB.NS", "TATATECH.NS", "NEWGEN.NS", "TANLA.NS", "RATEGAIN.NS", "FSL.NS", 
        "CSOFT.NS", "LATENTVIEW.NS", "KAYNES.NS", "ROUTE.NS", "CEINFO.NS", "BLS.NS", "AFFLE.NS", "JUSTDIAL.NS", 
        "NAUKRI.NS", "ZOMATO.NS", "CAMS.NS", "CDSL.NS", "INDIAMART.NS", "RSYSTEMS.NS", "NUCLEUS.NS", 
        "REDINGTON.NS", "SAKSOFT.NS", "SUBEXLTD.NS", "INFOBEAN.NS", "GENESYS.NS", "BHARTIARTL.NS", "IDEA.NS", 
        "MTNL.NS", "TEJASNET.NS", "HFCL.NS", "RAILTEL.NS", "OPTIEMUS.NS", "ITI.NS", "STERTOOLS.NS", "NELCO.NS", 
        "EXPLEOSOL.NS", "BIRLASOFT.NS", "CIGNITI.NS", "RAMCOSYS.NS", "QUESS.NS", "TEAMLEASE.NS", "SIS.NS", 
        "FIRSTSOURCE.NS", "HINDUJAVENT.NS", "ALLSEC.NS", "HOVS.NS", "MPSLTD.NS", "INTEGRA.NS", "INFOMEDIA.NS", 
        "TREJHARA.NS", "PROZONER.NS", "DATAMATICS.NS", "SILLYMONKS.NS", "CREATIVE.NS", "VIRTUALG.NS", "SIGNPOST.NS", 
        "GTLINFRA.NS", "SURANAIND.NS", "SOFTTECH.NS", "INNOVANA.NS", "AXISCADES.NS", "ALANKIT.NS", "VAKRANGEE.NS", 
        "GIRESI.NS", "KALYANI.NS", "BSE.NS", "SADBHAV.NS", "ONWARDTEC.NS", "TRIGYN.NS", "SILLYMONK.NS", "DREAMFOLKS.NS"
    ],
    "⛽ 3. Oil, Gas, Energy & Chemicals (100 Stocks)": [
        "RELIANCE.NS", "ONGC.NS", "IOC.NS", "BPCL.NS", "HPCL.NS", "GAIL.NS", "OIL.NS", "ATGL.NS", "PETRONET.NS", 
        "MGL.NS", "IGL.NS", "GUJGASLTD.NS", "COALINDIA.NS", "NTPC.NS", "POWERGRID.NS", "TATAPOWER.NS", "IREDA.NS", 
        "SUZLON.NS", "ADANIGREEN.NS", "ADANIPOWER.NS", "SJWN.NS", "NHPC.NS", "INOXWIND.NS", "KPIGREEN.NS", 
        "TORNTPOWER.NS", "CESC.NS", "JSWENERGY.NS", "ADANIENT.NS", "BHEL.NS", "DEEPAKNTR.NS", "GSPL.NS", 
        "CHAMBLFERT.NS", "UPL.NS", "GNFC.NS", "NFL.NS", "RCF.NS", "FACT.NS", "COROMANDEL.NS", "PIIND.NS", 
        "SRF.NS", "AARTIIND.NS", "ATUL.NS", "SUMICHEM.NS", "LINDEINDIA.NS", "SOLARINDS.NS", "CASTROLIND.NS", 
        "AEGISCHEM.NS", "FINEORG.NS", "ALKYLAMINE.NS", "BALAMINES.NS", "TATACHEM.NS", "GHCL.NS", "DCMSRIRAM.NS", 
        "FLUOROCHEM.NS", "VINATIORGA.NS", "NAVINFLUOR.NS", "CLEAN.NS", "ROSSARI.NS", "GRAVITA.NS", "EXIDEIND.NS", 
        "EPL.NS", "SUPRIYA.NS", "CHEMCON.NS", "HERANBA.NS", "INDIAGLYCO.NS", "JAYAGRO.NS", "BALRAMCHIN.NS", 
        "TRIVENI.NS", "RENUKA.NS", "EIDPARRY.NS", "BAJAJHIND.NS", "DHARAMSI.NS", "PRAJIND.NS", "GOCLCORP.NS", 
        "EXCELINDUS.NS", "SURYAROSH.NS", "JINDALSAW.NS", "WELCORP.NS", "MAHSEAMLES.NS", "APLAPOLLO.NS", 
        "RATNAMANI.NS", "MOIL.NS", "HINDZINC.NS", "HINDCOPPER.NS", "NMDC.NS", "GMDC.NS", "KIOCL.NS", 
        "SAIL.NS", "TATASTEEL.NS", "JSWSTEEL.NS", "JINDALSTEL.NS", "ELECTCAST.NS", "GODREJAGRO.NS", "SURYALAXMI.NS"
    ],
    "🚗 4. Auto, EV & Auto Components (100 Stocks)": [
        "TATAMOTORS.NS", "MARUTI.NS", "M&M.NS", "HEROMOTOCO.NS", "BAJAJ-AUTO.NS", "EICHERMOT.NS", "SONACOMS.NS", 
        "MOTHERSON.NS", "BOSCHLTD.NS", "EXIDEIND.NS", "OLECTRA.NS", "TUBEINVEST.NS", "BALKRISIND.NS", "BHARATFORG.NS", 
        "ASHOKLEY.NS", "TVSMOTOR.NS", "TIINDIA.NS", "AMARAJA.NS", "FORCEPOL.NS", "CRAFTSMAN.NS", "SUPRAJIT.NS", 
        "LUMAXIND.NS", "ENDURANCE.NS", "UNOMINDA.NS", "ESCORTS.NS", "SCHAEFFLER.NS", "TIMKEN.NS", "SKFINDIA.NS", 
        "SUBROS.NS", "SWARAJENG.NS", "SUNDRMFAST.NS", "JBMA.NS", "GREAVESCOTT.NS", "SJS.NS", "PRICOLLTD.NS", 
        "SANSERA.NS", "APOLLOTYRE.NS", "CEATLTD.NS", "MRF.NS", "JKTYRE.NS", "RAMKRASN.NS", "VARROC.NS", 
        "BANCOINDIA.NS", "MHRIL.NS", "GABRIEL.NS", "FIEMIND.NS", "AUTOAXLES.NS", "JAMNAAUTO.NS", "WHEELS.NS", 
        "TALBROSAUTO.NS", "RANEHOLDIN.NS", "LUMAXTECH.NS", "MUNJALSHOW.NS", "SMLISUZU.NS", "ATULAUTO.NS", 
        "MAHSCOOTER.NS", "VSTTILLERS.NS", "GNA.NS", "MENONBE.NS", "RICOAUTO.NS", "PRECISION.NS", "ASAL.NS", 
        "INDNIPPON.NS", "RANEENGINE.NS", "LGBALAKR.NS", "JAYBARMARU.NS", "SINTERCOM.NS", "SANDHAR.NS", "SSWL.NS", 
        "MINDACORP.NS", "SETCO.NS", "SALZERELEC.NS", "SHARDAMOTR.NS", "AUTOMOTIVE.NS", "PITTIENG.NS", "NELCAST.NS", 
        "INDOBORAX.NS", "MMFL.NS", "HLEGLAS.NS", "DIVGIITTS.NS", "LANDMARK.NS", "EUREKAFORB.NS", "HINDALCO.NS", 
        "VEDL.NS", "JSL.NS", "NATIONALUM.NS", "BEL.NS", "HAL.NS", "MAZDOCK.NS", "GRSE.NS", "COCHINSHIP.NS"
    ],
    "🏥 5. Pharma, Healthcare & Biotech (100 Stocks)": [
        "SUNPHARMA.NS", "CIPLA.NS", "DRREDDY.NS", "DIVISLAB.NS", "APOLLOHOSP.NS", "FORTIS.NS", "MAXHEALTH.NS", 
        "NH.NS", "LALPATHLAB.NS", "MANKIND.NS", "TORNTPHARM.NS", "LUPIN.NS", "ZYDUSLIFE.NS", "AUROPHARMA.NS", 
        "GLENMARK.NS", "ALKEM.NS", "IPCALAB.NS", "BIOCON.NS", "SYNGENE.NS", "METROPOLIS.NS", "LAURUSLABS.NS", 
        "GRANULES.NS", "JBCHEPHY.NS", "NATCOPHARM.NS", "CAPLIPOINT.NS", "ERIS.NS", "GLAXO.NS", "PFIZER.NS", 
        "ABBOTINDIA.NS", "SANOFI.NS", "AJANTPHARM.NS", "MARKSANS.NS", "HIKAL.NS", "ASTRAZEN.NS", "AARTIDRUGS.NS", 
        "GLAND.NS", "KIMS.NS", "ASTERDM.NS", "RAINBOW.NS", "MEDANTA.NS", "VIJAYA.NS", "SUVENPHAR.NS", 
        "NEULANDLAB.NS", "SOLARA.NS", "SHILPAMED.NS", "FDC.NS", "DISHMAN.NS", "THYROCARE.NS", "PGHL.NS", 
        "ALEMBICLTD.NS", "APLLTD.NS", "BLUEJET.NS", "CONCORD.NS", "KOPRAN.NS", "LINCOLN.NS", "MOREPENLAB.NS", 
        "PANACEABIO.NS", "RPGLIFE.NS", "SEQUENT.NS", "SMSPHARMA.NS", "SYNCOM.NS", "TTKHLTCARE.NS", "UNICHEMLAB.NS", 
        "VENUSREM.NS", "WOCKPHARMA.NS", "ZEEL.NS", "YATHARTH.NS", "ARTEMISMED.NS", "INDOCO.NS", "HESTERBIO.NS", 
        "JAGSNPHARM.NS", "BLISSGVS.NS", "SHALBY.NS", "SIGACHI.NS", "TARSONS.NS", "MEDICO.NS", "NOVARTIND.NS", 
        "BAYERCROP.NS", "DHANUKA.NS", "BASF.NS", "RALLIS.NS", "INSECTICID.NS", "ASTEC.NS", "SHARDACROP.NS", 
        "BHAGCHEM.NS", "BESTAGRO.NS", "AARTIIND.NS", "DEEPAKNTR.NS", "TATACHEM.NS", "SUMICHEM.NS", "FINEORG.NS"
    ],
    "🏗️ 6. Metals, Mining & Cement (100 Stocks)": [
        "TATASTEEL.NS", "JSWSTEEL.NS", "HINDALCO.NS", "JINDALSTEL.NS", "VEDL.NS", "SAIL.NS", "NMDC.NS", 
        "NATIONALUM.NS", "HINDZINC.NS", "HINDCOPPER.NS", "ULTRACEMCO.NS", "GRASIM.NS", "AMBUJACEM.NS", 
        "ACC.NS", "DALBHARAT.NS", "SHREECEM.NS", "JKCEMENT.NS", "RAMCOCEM.NS", "BIRLACORPN.NS", "HEidelberg.NS", 
        "APLAPOLLO.NS", "RATNAMANI.NS", "JSL.NS", "JINDALSAW.NS", "WELCORP.NS", "MAHSEAMLES.NS", "MOIL.NS", 
        "GMDC.NS", "KIOCL.NS", "ELECTCAST.NS", "MIDHANI.NS", "MISHTI.NS", "GALLANTT.NS", "ISMTLTD.NS", 
        "GODAWARI.NS", "SardaENERGY.NS", "SURYAROSH.NS", "KAJARIRCER.NS", "SOMANYCERA.NS", "CERA.NS", "ORIENTBELL.NS", 
        "PRINCEPIPE.NS", "ASTRAL.NS", "SUPREMEIND.NS", "FINPIPE.NS", "KESORAMIND.NS", "SAGARDEEP.NS", "UBL.NS", 
        "MCDOWELL-N.NS", "VBL.NS", "SANGHIIND.NS", "STARCEMENT.NS", "ORIENTCEM.NS", "DECCANCE.NS", "NCLIND.NS", 
        "MANAKSTEEL.NS", "BHARATWIRE.NS", "SHANKARA.NS", "PENIND.NS", "GOODLUCK.NS", "HI-TECH.NS", "BOMDYEING.NS", 
        "CENTURYTEX.NS", "RAYMOND.NS", "SWANENERGY.NS", "ALOKINDS.NS", "KPRMILL.NS", "LUXIND.NS", "PAGEIND.NS", 
        "RUPA.NS", "DOLLAR.NS", "GOKEX.NS", "TRIDENT.NS", "WELSPUNLIV.NS", "SPENTEX.NS", "HIMATSEIDE.NS", 
        "NITIIN.NS", "INDOCOUNT.NS", "FILATEX.NS", "RSWM.NS", "BANSWR.NS", "SUTLEJTEX.NS", "VARDHACRLC.NS", 
        "GARFIBRES.NS", "JIKIND.NS", "TCNSBRANDS.NS", "GOCOLORS.NS", "VEDANTFASH.NS", "ETHOSLTD.NS", "TITAN.NS"
    ],
    "🛒 7. FMCG, Retail & Consumer Durables (100 Stocks)": [
        "HUNVR.NS", "ITC.NS", "NESTLEIND.NS", "BRITANNIA.NS", "TATACONSUM.NS", "DABUR.NS", "GODREJCP.NS", 
        "MARICO.NS", "COLPAL.NS", "VARUNBEV.NS", "VBL.NS", "AWL.NS", "EMAMILTD.NS", "RADICO.NS", "UBL.NS", 
        "MCDOWELL-N.NS", "TITAN.NS", "KALYANKJIL.NS", "SENCO.NS", "TRENT.NS", "DMART.NS", "ABFRL.NS", 
        "MANYAVAR.NS", "BATAINDIA.NS", "RELAXO.NS", "CAMPUS.NS", "METROBRAND.NS", "HAVELLS.NS", "POLYCAB.NS", 
        "CROMPTON.NS", "VOLTAS.NS", "BLUESTARCO.NS", "WHIRLPOOL.NS", "DIXON.NS", "AMBER.NS", "SYRMA.NS", 
        "KEI.NS", "RRKABEL.NS", "FINCABLES.NS", "BAJAJELEC.NS", "ORIENTELEC.NS", "SYMPHONY.NS", "VGUARD.NS", 
        "TTKPRESTIG.NS", "HAWKINS.NS", "PGHH.NS", "GILLETTE.NS", "JYOTHYLAB.NS", "BAJAJCON.NS", "GODREJAGRO.NS", 
        "ZOMATO.NS", "JUBLFOOD.NS", "DEVYANI.NS", "WESTLIFE.NS", "SAPPHIRE.NS", "RESTAURANT.NS", "BARBEQUE.NS", 
        "HONASA.NS", "PATANJALI.NS", "HERITGFOOD.NS", "DODLA.NS", "HATSON.NS", "PARAGMILK.NS", "KRBL.NS", 
        "LTFOODS.NS", "VENKEYS.NS", "SKMMEAT.NS", "AVANTIFEED.NS", "APEX.NS", "CCL.NS", "TCPLPACK.NS", 
        "UFO.NS", "PVRINOX.NS", "TIPSMUSIC.NS", "SAREGAMA.NS", "SUNTV.NS", "ZEEL.NS", "NAZARA.NS", 
        "DELTACORP.NS", "EASEMYTRIP.NS", "THOMASCOOK.NS", "YATRA.NS", "LEMONTREE.NS", "INDIANHOTE.NS", "EIHOTEL.NS", 
        "CHALET.NS", "SAMHI.NS", "PARKSTREET.NS", "WONDERLA.NS", "KOTARISUG.NS", "BALRAMCHIN.NS", "RENUKA.NS"
    ],
    "🛡️ 8. Defense, Aerospace & Engineering (100 Stocks)": [
        "HAL.NS", "BEL.NS", "MAZDOCK.NS", "COCHINSHIP.NS", "GRSE.NS", "BDL.NS", "DATAPATTNS.NS", "PARAS.NS", 
        "ASTRAENC.NS", "MTARTECH.NS", "IDEAFORGE.NS", "ZENITH.NS", "L&T.NS", "SIEMENS.NS", "ABB.NS", 
        "CGPOWER.NS", "SUZLON.NS", "INOXWIND.NS", "HITACHI.NS", "BHEL.NS", "CUMMINSIND.NS", "THERMAX.NS", 
        "TRIVENI.NS", "TDPOWERSYS.NS", "KIRLOSENG.NS", "AIAENG.NS", "ELECTCAST.NS", "KEC.NS", "KALPATPOWR.NS", 
        "ENGINERSIN.NS", "VATECH.NS", "IONEXCHANG.NS", "PRAJIND.NS", "ACTIONIND.NS", "TEXRAIL.NS", "TITAGARH.NS", 
        "RAILTEL.NS", "RITES.NS", "RVNL.NS", "IRCON.NS", "IRFC.NS", "BEML.NS", "CONCOR.NS", "GPPL.NS", 
        "JISLJALEQS.NS", "SCHNEIDER.NS", "VGUARD.NS", "HONAUT.NS", "GENUSPOWER.NS", "HPL.NS", "ELGIEQUIP.NS", 
        "DISHTV.NS", "KIRLOSBROS.NS", "KSB.NS", "SHAKTIPUMP.NS", "ROTO.NS", "SKIPPER.NS", "SURYAROSH.NS", 
        "JINDALSAW.NS", "WELCORP.NS", "MAHSEAMLES.NS", "APLAPOLLO.NS", "RATNAMANI.NS", "PITTIENG.NS", "NELCAST.NS", 
        "CRAFTSMAN.NS", "BHARATFORG.NS", "RAMKRASN.NS", "GNA.NS", "RICOAUTO.NS", "PRECISION.NS", "SANSERA.NS", 
        "SUNDRMFAST.NS", "TIMKEN.NS", "SKFINDIA.NS", "SCHAEFFLER.NS", "AARTISURF.NS", "SHARDAMOTR.NS", "SALZERELEC.NS", 
        "KAYNES.NS", "SYRMA.NS", "CYIENTDLM.NS", "DCXINDIA.NS", "E2E.NS", "TENT.NS", "DYNAMATECH.NS", "GABRIEL.NS"
    ],
    "⚡ 9. Renewable Energy, Power & Utilities (100 Stocks)": [
        "NTPC.NS", "POWERGRID.NS", "TATAPOWER.NS", "IREDA.NS", "SUZLON.NS", "ADANIGREEN.NS", "ADANIPOWER.NS", 
        "SJWN.NS", "NHPC.NS", "INOXWIND.NS", "KPIGREEN.NS", "TORNTPOWER.NS", "CESC.NS", "JSWENERGY.NS", 
        "ADANIENT.NS", "BHEL.NS", "BORORENEW.NS", "WEBELSOLAR.NS", "STERENERGY.NS", "SOLEX.NS", "GENUSPOWER.NS", 
        "HPL.NS", "SCHNEIDER.NS", "CGPOWER.NS", "SIEMENS.NS", "ABB.NS", "HITACHI.NS", "CUMMINSIND.NS", 
        "KEC.NS", "KALPATPOWR.NS", "RITES.NS", "ENGINERSIN.NS", "VATECH.NS", "IONEXCHANG.NS", "AIAENG.NS", 
        "THERMAX.NS", "TDPOWERSYS.NS", "KIRLOSENG.NS", "TRIVENI.NS", "PRAJIND.NS", "GAIL.NS", "PETRONET.NS", 
        "MGL.NS", "IGL.NS", "GUJGASLTD.NS", "ATGL.NS", "GSPL.NS", "RELIANCE.NS", "ONGC.NS", "OIL.NS", 
        "COALINDIA.NS", "NLCINDIA.NS", "DEEPAKNTR.NS", "GIPCL.NS", "OPG.NS", "INDIANENERGY.NS", "IEX.NS", 
        "MCX.NS", "BSE.NS", "CDSL.NS", "CAMS.NS", "NSDL.NS", "HUDCO.NS", "PFC.NS", "RECLTD.NS", "IREDA.NS", 
        "SUZLON.NS", "KPIT.NS", "TATACOMM.NS", "STERLITE.NS", "HFCL.NS", "TEJASNET.NS", "NELCO.NS", "RAILTEL.NS", 
        "ITI.NS", "BEML.NS", "BEL.NS", "HAL.NS", "MIDHANI.NS", "MTARTECH.NS", "DATAPATTNS.NS", "PARAS.NS"
    ],
    "🚂 10. Railways, Logistics & Infrastructure (100 Stocks)": [
        "IRFC.NS", "RVNL.NS", "IRCON.NS", "RAILTEL.NS", "RITES.NS", "TEXRAIL.NS", "TITAGARH.NS", "BEML.NS", 
        "CONCOR.NS", "GPPL.NS", "MAZDOCK.NS", "COCHINSHIP.NS", "GRSE.NS", "DELHIVERY.NS", "BLUEDART.NS", 
        "TCIEXP.NS", "MAHLOG.NS", "VRLLOG.NS", "GATEWAY.NS", "ALLCARGO.NS", "AEGISCHEM.NS", "GMRINFRA.NS", 
        "ADANIPORTS.NS", "JSWINFRA.NS", "IRB.NS", "PNCINFRA.NS", "KNRCON.NS", "HGINFRA.NS", "GRINFRA.NS", 
        "DILIPBUILD.NS", "J KUMAR.NS", "ITD.NS", "NCC.NS", "ASHOKA.NS", "NSPIL.NS", "SADBHAV.NS", "SIMPLEX.NS", 
        "ENGINERSIN.NS", "NBCC.NS", "PSPPROJECT.NS", "CAPACITE.NS", "AHLUCONT.NS", "MANINFRA.NS", "TEXINFRA.NS", 
        "WELENT.NS", "DLF.NS", "LODHA.NS", "GODREJPROP.NS", "OBERREALTY.NS", "PHOENIXLTD.NS", "PRESTAGE.NS", 
        "BRIGADE.NS", "SOBHA.NS", "SIGNATURE.NS", "MAHLIFE.NS", "SUNTECK.NS", "IBREALEST.NS", "KOLTEPATIL.NS", 
        "GANESHIN.NS", "ASHIANA.NS", "PURVA.NS", "AJMERA.NS", "MARATHON.NS", "DBREALTY.NS", "PENINLAND.NS", 
        "RAMKY.NS", "GPTINFRA.NS", "RPPINFRA.NS", "VPRPL.NS", "OMAXE.NS", "PARSVNATH.NS", "HUBTOWN.NS"
    ]
}

col_sec, col_tf = st.columns(2)
with col_sec:
    selected_category = st.selectbox("একটি সাব-সেক্টর বেছে নিন:", list(SUB_SECTORS.keys()))
with col_tf:
    timeframe_option = st.selectbox("ক্যান্ডেল টাইমফ্রেম (Timeframe):", ["1 Day (Daily)", "4 Hours (4h)", "1 Hour (1h)", "15 Minutes (15m)"])

def fetch_stock_data(ticker, tf_choice):
    stock = yf.Ticker(ticker)
    if tf_choice == "1 Day (Daily)":
        return stock.history(period="3mo", interval="1d")
    elif tf_choice == "4 Hours (4h)":
        df = stock.history(period="1mo", interval="1h")
        if not df.empty:
            df = df.resample('4h').agg({
                'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'
            }).dropna()
        return df
    elif tf_choice == "1 Hour (1h)":
        return stock.history(period="1mo", interval="1h")
    elif tf_choice == "15 Minutes (15m)":
        return stock.history(period="5d", interval="15m")
    return pd.DataFrame()

def analyze_stock(df):
    if len(df) < 21:
        return None
    
    # বর্তমান ও পেছনের ক্যান্ডেলসমূহ
    c1 = df.iloc[-1]
    c2 = df.iloc[-2]
    c3 = df.iloc[-3]
    
    open1, close1, high1, low1 = c1['Open'], c1['Close'], c1['High'], c1['Low']
    open2, close2, high2, low2 = c2['Open'], c2['Close'], c2['High'], c2['Low']
    open3, close3, high3, low3 = c3['Open'], c3['Close'], c3['High'], c3['Low']
    
    body1 = abs(close1 - open1)
    range1 = high1 - low1
    if range1 == 0:
        return None
        
    lower_shadow1 = min(open1, close1) - low1
    upper_shadow1 = high1 - max(open1, close1)
    
    # প্রপার সাপোর্ট ও রেজিস্ট্যান্স ফিল্টার (পূর্ববর্তী ২০ ক্যান্ডেলের লো ও হাই)
    prev_df = df.iloc[-21:-1]
    recent_low = prev_df['Low'].min()
    recent_high = prev_df['High'].max()
    
    # সূক্ষ্ম সাপোর্ট ও রেজিস্ট্যান্স টলারেন্স (Strict 0.8% Range)
    is_at_support = (low1 <= recent_low * 1.008)
    is_at_resistance = (high1 >= recent_high * 0.992)
    
    is_green1 = close1 > open1
    is_red1 = close1 < open1
    is_red2 = close2 < open2
    is_green2 = close2 > open2
    is_red3 = close3 < open3
    is_green3 = close3 > open3
    
    pattern = "⚪ No Pattern"
    type_tag = "None"
    
    # 🟢 বুলিশ প্যাটার্ন ফিল্টার (শুধুমাত্র প্রপার সাপোর্টে)
    if is_at_support:
        if is_red3 and (abs(close2 - open2) <= 0.3 * (high2 - low2)) and is_green1 and (close1 > (open3 + close3) / 2):
            pattern = "🌟 Morning Star"
            type_tag = "Bullish"
        elif is_red2 and is_green1 and (close1 >= open2) and (open1 <= close2):
            pattern = "🔥 Bullish Engulfing"
            type_tag = "Bullish"
        elif is_red2 and is_green1 and (open1 < close2) and (close1 > (open2 + close2) / 2) and (close1 < open2):
            pattern = "⚡ Piercing Line"
            type_tag = "Bullish"
        elif is_green1 and (lower_shadow1 >= 2 * body1) and (upper_shadow1 <= 0.2 * body1) and (body1 > 0):
            pattern = "🔨 Green Bullish Hammer"
            type_tag = "Bullish"
        elif is_green1 and (upper_shadow1 >= 2 * body1) and (lower_shadow1 <= 0.2 * body1) and (body1 > 0):
            pattern = "🙃 Inverted Hammer"
            type_tag = "Bullish"
        elif (body1 <= 0.1 * range1) and (lower_shadow1 >= 0.6 * range1) and (upper_shadow1 <= 0.1 * range1):
            pattern = "🐉 Dragonfly Doji"
            type_tag = "Bullish"

    # 🔴 বেয়ারিশ প্যাটার্ন ফিল্টার (শুধুমাত্র প্রপার রেজিস্ট্যান্সে)
    if is_at_resistance and type_tag == "None":
        if is_green3 and (abs(close2 - open2) <= 0.3 * (high2 - low2)) and is_red1 and (close1 < (open3 + close3) / 2):
            pattern = "🌩️ Evening Star"
            type_tag = "Bearish"
        elif is_green2 and is_red1 and (close1 <= open2) and (open1 >= close2):
            pattern = "❄️ Bearish Engulfing"
            type_tag = "Bearish"
        elif is_green2 and is_red1 and (open1 > close2) and (close1 < (open2 + close2) / 2) and (close1 > open2):
            pattern = "🌧️ Dark Cloud Cover"
            type_tag = "Bearish"
        elif is_red1 and (upper_shadow1 >= 2 * body1) and (lower_shadow1 <= 0.2 * body1) and (body1 > 0):
            pattern = "🌠 Shooting Star"
            type_tag = "Bearish"
        elif is_red1 and (lower_shadow1 >= 2 * body1) and (upper_shadow1 <= 0.2 * body1) and (body1 > 0):
            pattern = "🪢 Hanging Man"
            type_tag = "Bearish"
        elif (body1 <= 0.1 * range1) and (upper_shadow1 >= 0.6 * range1) and (lower_shadow1 <= 0.1 * range1):
            pattern = "🪦 Gravestone Doji"
            type_tag = "Bearish"
            
    buyer_power = round(((close1 - low1) / range1) * 100, 1)
    seller_power = round(((high1 - close1) / range1) * 100, 1)
    
    return {
        "Price": round(close1, 2),
        "Pattern": pattern,
        "Type": type_tag,
        "Buyer Power %": buyer_power,
        "Seller Power %": seller_power
    }

def render_cards(items):
    for item in items:
        with st.container():
            c1, c2, c3, c4 = st.columns([2, 2, 3, 2])
            stock_name = item["Stock"]
            groww_url = f"https://groww.in/search?q={stock_name}"
            tv_url = f"https://in.tradingview.com/char
