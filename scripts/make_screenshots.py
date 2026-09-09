"""Generate screenshot-style UI images from an ACTUAL run of the demo.

The embedded plots are exactly what the Streamlit app renders; the surrounding
frame reproduces the app layout so the README can show what the UI looks like
without needing a live browser. Regenerate with:
    python -m smartmeter_sca.scripts.make_screenshots
"""
import os, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from smartmeter_sca.src.meter import SmartMeter
from smartmeter_sca.src import leakage, cpa, metrics
from smartmeter_sca.src.countermeasure import INFO

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "docs", "screenshots")
os.makedirs(OUT, exist_ok=True)
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})

BG="#ffffff"; SIDE="#f0f2f6"; TXT="#31333F"; SUB="#6b6f76"
BLUE="#e8f0fe"; GREEN="#eafaf0"; GREENB="#1a7f4b"; RED="#fdecec"; REDB="#c0392b"; PRIMARY="#ff4b4b"

def rrect(fig,x,y,w,h,fc):
    fig.patches.append(FancyBboxPatch((x,y),w,h,
        boxstyle="round,pad=0.002,rounding_size=0.012",
        transform=fig.transFigure,fc=fc,ec="none"))

def compute(protection,n=1500,noise=2.0):
    m=SmartMeter(); key=m.key_array(); pts=m.capture(n)
    tr=leakage.simulate_traces(pts,key,noise_sigma=noise,protection=protection,seed=1)
    rec,best,table=cpa.recover_key(tr,pts)
    cps=np.unique(np.linspace(20,n,20).astype(int))
    ge=metrics.guessing_entropy_curve(tr,pts,key,cps)
    ttd,_=metrics.traces_to_disclosure(tr,pts,key,0,cps)
    return dict(key=key,rec=rec,best=best,table=table,traces=tr,cps=cps,ge=ge,ttd=ttd,
                n=n,noise=noise,protection=protection,ok=int((rec==key).sum()))

def sidebar(fig,protection,n,noise):
    x0=0.015
    fig.text(x0,0.945,"Attack settings",weight="bold",fontsize=12,color=TXT)
    def slider(y,label,val,frac):
        fig.text(x0,y+0.028,label,fontsize=8.5,color=TXT)
        ax=fig.add_axes([x0,y,0.20,0.006]); ax.axis("off")
        ax.axhline(0.5,color="#c9ccd4",lw=3); ax.plot([frac],[0.5],marker="o",ms=9,color=PRIMARY)
        ax.set_xlim(0,1); ax.set_ylim(0,1)
        fig.text(x0+0.205,y+0.026,str(val),fontsize=8.5,color=SUB)
    slider(0.885,"Number of power traces",n,(n-100)/4900)
    slider(0.815,"Measurement noise (sigma)",noise,noise/6)
    fig.text(x0,0.775,"Meter protection",fontsize=8.5,color=TXT)
    for i,p in enumerate(leakage.PROTECTIONS):
        yy=0.748-i*0.026; sel=p==protection
        fig.text(x0+0.006,yy,("◉ " if sel else "○ ")+INFO[p]["label"],
                 fontsize=8.5,color=(PRIMARY if sel else SUB),weight=("bold" if sel else "normal"))
    import textwrap
    rrect(fig,x0,0.585,0.205,0.075,BLUE)
    wrapped="\n".join(textwrap.wrap(INFO[protection]["desc"],width=42))
    fig.text(x0+0.008,0.648,wrapped,fontsize=7.3,color=TXT,va="top")
    rrect(fig,x0,0.545,0.205,0.028,PRIMARY)
    fig.text(x0+0.1025,0.559,"Run attack",color="white",ha="center",va="center",weight="bold",fontsize=9)

def header(fig):
    fig.text(0.30,0.955,"Side-Channel Attack on a Smart Meter (CPS)",weight="bold",fontsize=16,color=TXT)
    fig.text(0.30,0.928,"SE6012 CA1 demo. Real AES-128, real CPA, laptop-only, CPU. The attacker never sees the key.",
             fontsize=9,color=SUB)

def metric(fig,x,label,value):
    fig.text(x,0.845,label,fontsize=8.5,color=SUB)
    fig.text(x,0.815,value,fontsize=17,color=TXT,weight="bold")

def keyblock(fig,y,key,rec):
    hx=lambda a:" ".join(f"{b:02x}" for b in a)
    fig.text(0.30,y+0.028,"Recovered key vs true key",weight="bold",fontsize=10,color=TXT)
    rrect(fig,0.30,y-0.052,0.66,0.072,"#f6f6f6")
    fig.text(0.312,y+0.006,f"true      : {hx(key)}",family="monospace",fontsize=8.2,color=TXT)
    fig.text(0.312,y-0.012,f"recovered : {hx(rec)}",family="monospace",fontsize=8.2,color=TXT)
    marks="".join(("OK " if rec[i]==key[i] else "XX ") for i in range(16))
    fig.text(0.312,y-0.030,f"match     : {marks}",family="monospace",fontsize=8.2,
             color=(GREENB if (rec==key).all() else REDB))

def banner(fig,ok):
    if ok==16:
        rrect(fig,0.30,0.878,0.66,0.03,GREEN)
        fig.text(0.312,0.893,"OK   FULL AES-128 KEY RECOVERED. The meter's secret is broken.",
                 color=GREENB,fontsize=9.5,va="center",weight="bold")
    else:
        rrect(fig,0.30,0.878,0.66,0.03,RED)
        fig.text(0.312,0.893,"XX   Attack defeated. The countermeasure stopped key recovery.",
                 color=REDB,fontsize=9.5,va="center",weight="bold")

def plots(fig,r):
    ax1=fig.add_axes([0.325,0.30,0.28,0.24])
    ax1.plot(r["table"][0],lw=0.8); ax1.axvline(r["key"][0],color="r",ls="--",lw=1)
    ax1.set_title("Correlation vs key guess (byte 0)",fontsize=9)
    ax1.set_xlabel("guess (0-255)",fontsize=8); ax1.set_ylabel("max |corr|",fontsize=8); ax1.tick_params(labelsize=7)
    ax2=fig.add_axes([0.68,0.30,0.28,0.24])
    ax2.plot(r["cps"],r["ge"],"-o",ms=3,color="#1f77b4"); ax2.axhline(0,color="gray",ls=":",lw=.8)
    ax2.set_title("Guessing entropy vs traces",fontsize=9)
    ax2.set_xlabel("number of traces",fontsize=8); ax2.set_ylabel("mean log2 rank",fontsize=8); ax2.tick_params(labelsize=7)
    ax3=fig.add_axes([0.325,0.05,0.635,0.16])
    for i in range(6): ax3.plot(r["traces"][i],lw=0.6)
    ax3.set_title("Example simulated power traces",fontsize=9)
    ax3.set_xlabel("time sample",fontsize=8); ax3.set_ylabel("power (a.u.)",fontsize=8); ax3.tick_params(labelsize=7)

def frame(protection,fname,landing=False):
    r=compute(protection)
    fig=plt.figure(figsize=(13,9),dpi=110); fig.patch.set_facecolor(BG)
    rrect(fig,0.0,0.0,0.24,1.0,SIDE)
    sidebar(fig,protection,r["n"],r["noise"]); header(fig)
    if landing:
        fig.text(0.30,0.80,"Set the parameters on the left and press  Run attack.",fontsize=11,color=TXT)
        fig.text(0.30,0.76,"- Unprotected meter: the AES key is recovered from power alone.",fontsize=9.5,color=SUB)
        fig.text(0.30,0.735,"- Masking / shuffling: the identical attack fails.",fontsize=9.5,color=SUB)
        fig.text(0.30,0.71,"- Everything runs on CPU in a few seconds. No GPU, no hardware.",fontsize=9.5,color=SUB)
    else:
        banner(fig,r["ok"])
        metric(fig,0.325,"Key bytes recovered",f"{r['ok']} / 16")
        metric(fig,0.55,"Mean best correlation",f"{r['best'].mean():.3f}")
        metric(fig,0.78,"Traces to disclosure (byte 0)","n/a" if r["ttd"]<0 else str(r["ttd"]))
        keyblock(fig,0.615,r["key"],r["rec"]); plots(fig,r)
    fig.savefig(os.path.join(OUT,fname),dpi=110,facecolor=BG); plt.close(fig)
    print("wrote",fname,"ok=",r["ok"])

if __name__=="__main__":
    frame("none","01_landing.png",landing=True)
    frame("none","02_unprotected_result.png")
    frame("masking","03_masking_result.png")
    frame("shuffling","04_shuffling_result.png")
