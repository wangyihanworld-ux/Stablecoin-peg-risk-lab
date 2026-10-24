"""Optional static evidence chart; pip install matplotlib==3.10.8."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from analyze import load_prices

root=Path(__file__).resolve().parent
fig,axes=plt.subplots(2,1,figsize=(10,7),constrained_layout=True)
for asset,color in [('usdc','#215b8f'),('dai','#bb6520')]:
    rows=load_prices(root/'data'/f'{asset}.csv')
    axes[0].plot([d for d,_ in rows],[float(p) for _,p in rows],label=asset.upper(),color=color,lw=1.4)
    march=[(d,p) for d,p in rows if d.month==3]
    axes[1].plot([d for d,_ in march],[float((p-1)*10000) for _,p in march],label=asset.upper(),color=color,marker='.',lw=1)
axes[0].axhline(1,color='gray',ls='--',lw=.8)
axes[0].set(title='Observed daily stablecoin prices | January–June 2023',ylabel='USD per token')
axes[1].axhspan(-100,100,color='#dddddd',alpha=.5,label='Illustrative ±100 bps band')
axes[1].set(title='Selected stress month | March 2023',ylabel='Deviation from USD 1 (bps)')
for ax in axes:
    locator=mdates.AutoDateLocator(minticks=4,maxticks=7)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
    ax.legend(loc='lower right',fontsize=8)
    ax.grid(alpha=.15)
fig.supxlabel('Coin Metrics PriceUSD • Daily observations, not intraday lows • CC BY-NC 4.0',fontsize=9)
(root/'results').mkdir(exist_ok=True)
fig.savefig(root/'results'/'peg_deviation.png',dpi=160)
plt.close(fig)
