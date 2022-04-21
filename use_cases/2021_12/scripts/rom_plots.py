#!/usr/bin/env python
"""
  Plot ARMA Results for EPRI Cases.

  This script requires cryptography module to be installed.
  You can install this via:
      conda install cryptography scikit-learn
  or
      pip install cryptography scikit-learn
"""
# Internal Libraries
import argparse
import time
import hashlib
import collections
import datetime as dt
import xml.etree.cElementTree as ET
from pathlib import Path
from typing import Iterator, Dict, List, Tuple, Union, Callable
from typing_extensions import TypedDict

# External Libraries
import pandas as pd
import numpy as np
import matplotlib as mpl
mpl.use('Agg') # Prevents the script from blocking while plotting
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors # type: ignore
import sklearn.linear_model
import statsmodels.api as sm
from matplotlib.font_manager import FontProperties
from matplotlib.ticker import StrMethodFormatter # type:ignore
from cryptography.fernet import Fernet


# Global Constants
YEARS = np.arange(2025, 2055, 5)
DAYS = ['Sun.', 'Mon.', 'Tues.', 'Wed.', 'Thurs.', 'Fri.', 'Sat.']
MONTHS = [
    'Jan.', 'Feb.', 'Mar.', 'Apr.', 'May', 'June',
    'July', 'Aug.', 'Sept.', 'Oct.', 'Nov.', 'Dec.'
]
CRYPTO = b"_1sbrS8rGU1kSSCLIuN6e2Z_Gs4UhJX8uCVPETuJkOs="
BASE_DIR = Path(__file__).resolve().parent.parent
TRAIN_DIR = BASE_DIR.joinpath('train')

# Initialize Color-Map
set1 = np.unique(plt.cm.Dark2(np.linspace(0, 1, 256)), axis=0)  # type: ignore
set2 = [plt.cm.viridis(i) for i in [0.0, 0.25, 0.5, 0.75, 1.0]] # type: ignore
set3 = np.unique(plt.cm.tab20(np.linspace(0, 1, 256)), axis=0)  # type: ignore
allc = np.vstack((set1, set2, set3))
COLORS = mcolors.LinearSegmentedColormap.from_list('rom_colormap', allc)
NORM = mcolors.BoundaryNorm(np.arange(0, 32, 1), COLORS.N, clip=True)

# Matplotlib Global Settings
plt.rc("figure", figsize=(25, 10))
plt.rc(
    "axes",
    titlesize=25,
    titleweight="bold",
    labelsize=25,
    axisbelow=True,
    grid=True
)
plt.rc("savefig", bbox="tight")
plt.rc("legend", fontsize=20)
plt.rc(["xtick", "ytick"], labelsize=20)


class Info(TypedDict):
    """Heterogenously typed dictionary for stricter type checking."""
    info: Dict[str, str]
    xmlhash: str
    args: argparse.Namespace
    fetch: Callable


class PlotOpts(TypedDict):
    """Heterogenously typed dictionary for stricter type checking."""
    density: bool
    bins: int
    edgecolor: str


## Functions
def search_node(root: ET.Element, node: str, child_element_names: List[str]) -> Dict[str, Union[str, None]]:
    """
    Return dictionary containing information requested from node children.

    @In: root, ET.Element, root node of xml tree.
    @In: node, str, xpath to parent node of interest.
    @In: children, List[str], expected children nodes.
    @Out: values, Dict[str, str], retrieved information for subnode.
    """
    values = {
        # This information will be placed in LaTeX table;
        # Therefore, we need to preemptively escape underscores.
        child.replace("_", r"\_"): root.findtext(f"{node}/{child}")
        for child in child_element_names
        if root.findtext(f"{node}/{child}") is not None
    }
    return values


def parse_xml(xml_file: Path) -> Dict[str, str]:
    """
    Parse model information from xml file.

    @In: xml_file, Path, path to current specified xml_file.
    @Out: info_dict, Dict[str, str], information parsed from xml.
    """
    root = ET.parse(xml_file).getroot()
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Information parsed from xml file.
    case_info = {
        "state": xml_file.name.split("_")[0].upper(),
        "strategy": xml_file.resolve().parent.name,
    }
    model_info = search_node(root, "Models/ROM", ["P", "Q", "Fourier"])

    if root.find("Models/ROM/Segment/subspace") is not None:
        subspace_info = root.find("Models/ROM/Segment/subspace").attrib
    else:
        subspace_info: Dict[str, str] = {}

    model_info = {**model_info, **subspace_info}
    pp_info = search_node(
        root,
        "Models/PostProcessor/KDD",
        ["SKLtype", "n_clusters", "tol", "random_state"],
    )
    samp_info = search_node(root, "Samplers/MonteCarlo/samplerInit", ["limit"])
    misc_info = {"created": now}
    working_dir_info = search_node(root, "RunInfo", ['WorkingDir'])

    # Merge all dictionaries
    # This should allow us to not fail on missing nodes
    info_dict = {
        **case_info, **model_info, **pp_info,
        **samp_info, **misc_info, **working_dir_info
    }
    return info_dict


def parse_meta(xml_file: Path) -> Callable[[int, int], int]:
    """
    Return callable that returns cluster info for each ROM for each year.

    @In: xml_file, Path, path to romMeta.xml
    @Out: get_cluster, Callable, a function that takes a segment and
          returns a cluster.
    """
    root = ET.parse(xml_file).getroot()
    meta = {}

    for year_rom in root.findall("arma/MacroStepROM"):
        meta[int(year_rom.get('YEAR', '0'))] = {}
        for cluster in year_rom.findall("ClusterROM"):
            cluster_num = int(cluster.get('cluster', '999'))
            segments = tuple([int(i) for i in cluster.findtext('segments_represented').split(", ")])
            # Assign tuple of segments as key and Cluster Number as value
            meta[int(year_rom.get('YEAR', '0'))][segments] = cluster_num

    def get_cluster(year: int, segment: int) -> int:
        """
        Return cluster number for a given segment.

        @In: year, int, year given from the ROM.
        @In: segment, int, segment from predicted values of ROM.
        @Out: int, a number representing cluster number.
        """
        id_segments = next(filter(lambda x: segment in x, meta[year].keys()))
        return meta[year][id_segments]

    return get_cluster


def hash_xml(xml_file: Path) -> str:
    """
    Return a truncated sha1 hash of xml.

    @In: xml_file, Path, current specified xml_file.
    @Out: sha_signature, str, sha1 hash of xml_file.
    """
    hash_str = open(xml_file, "rb").read()
    sha_signature = hashlib.sha1(hash_str).hexdigest()[:8]
    return sha_signature


def encrypt_xml(xml_file: Path) -> bytes:
    """
    Encrypt XML document that created the plots.

    @In: xml_file, Path, current specified xml_file.
    @Out: xml_hash, bytes, hash of xml file to embedd in PNG.
    """
    cipher = Fernet(CRYPTO)
    with open(xml_file, "rb") as out:
        xml_hash = cipher.encrypt(out.read())
    return xml_hash


def decrypt_xml(png_file: Path) -> str:
    """
    Decrypt XML file that is hidden in png file.

    @In: png_file, Path, PNG file with embedded xml.
    @Out: xml_text, str, original xml file.
    """
    cipher = Fernet(CRYPTO)
    with open(png_file, "rb") as f:
        xml_hash = f.read().split(b"IEND\xaeB`\x82")[1]
        xml_text = cipher.decrypt(xml_hash).decode("utf-8")
    return xml_text


def embed_xml(xml_file: Path, old_image: Path, new_image: Path) -> None:
    """
    Embed XML file into an image.

    @In: xml_file, Path, path to xml you want to embedd.
    @In: old_image, Path, path to the original png file without xml.
    @In: new_image, Path, path to the new image containing xml.
    @Out: None
    """
    with open(new_image, "wb") as out:
        out.write(open(old_image, "rb").read())
        out.write(encrypt_xml(xml_file))


def ecdf(sample) -> Tuple[float, float]:
    """
    Return empirical cdf of sample data.

    @In: sample, pd.Series, a vector of observed data.
    @Out: Tuple[float, float], quantile and cumulative probability vectors.
    """
    sample = np.atleast_1d(sample).astype(np.double)  # type: ignore
    quantiles, counts = np.unique(sample, return_counts=True)
    cumprob = np.cumsum(counts).astype(np.double) / sample.size  # type: ignore
    return quantiles, cumprob  # type: ignore


def detrend(pivots, values, periods: List[float]) -> pd.Series:
    """
    Return a time-series signal detrending using Fourier analysis.

    @In: df, pd.DataFrame, a dataframe containing signal information.
    @Out: pd.Series, a detrended time-series vector
    """
    # TODO: scrape fourier bases from current xml file.
    fourier = np.zeros((pivots.size, 2*len(periods)))
    for p, period in enumerate(periods):
        hist = 2.0 * (np.pi / period) * pivots
        fourier[:, 2 * p] = np.sin(hist)
        fourier[:, 2 * p + 1] = np.cos(hist)

    masks = np.ones(len(values), dtype=bool)  # type: ignore
    fe = sklearn.linear_model.LinearRegression(normalize=False)
    fs = fourier[masks, :]
    values = values[masks]
    fe.fit(fs, values)
    intercept = fe.intercept_
    coeffs = fe.coef_
    wave_coef_map: Dict = collections.defaultdict(dict)
    for c, coef in enumerate(coeffs):
      period = periods[c//2]
      waveform = 'sin' if c % 2 == 0 else 'cos'
      wave_coef_map[period][waveform] = coef
    coef_map = {}
    signal = np.ones(len(pivots)) * intercept
    for period, coefs in wave_coef_map.items():
      A = coefs['sin']
      B = coefs['cos']
      s, C = ((np.arctan2(B, A)), A / np.cos(np.arctan2(B, A)))  # type: ignore
      coef_map[period] = {'amplitude': C, 'phase': s}
      signal += C * np.sin(2.0 * np.pi * pivots / period + s)
    return signal  # type: ignore


def add_plot_table(fig: plt.Figure, axes: List[plt.Axes], info: Dict[str, str]) -> None:
    """
    Add table of ROM Parameters to graphic.

    @In: fig, plt.Figure, current figure to contain plots
    @In: axes, list, a list of current axes in figure
    @In: info, dict, a dictionary of model information.
    @Out: None
    """
    gs = fig.add_gridspec(nrows=2, ncols=(len(YEARS) // 2 + 1))
    nested_axes = [axes[i:i+3] for i in range(0, 6, 3)]
    for i, row in enumerate(nested_axes):
        for j, ax in enumerate(row):
            ax.set_position(gs[i, j].get_position(fig))
            ax.set_subplotspec(gs[i, j])
    fig.tight_layout()
    axtab = fig.add_subplot(gs[0:, -1])
    table_vals = [[val] for _, val in info.items()]
    tab = axtab.table(
        table_vals,
        colLabels=[r"$\bf{ROM \ Parameters}$"],
        rowLabels=[fr"$\bf{k}$" for k in info.keys()],
        bbox=[0.3, 0.2, 0.72, 0.7],
    )
    axtab.set_axis_off()
    tab.auto_set_font_size(False)
    tab.set_fontsize(15)
    tab.scale(.7, 4)
    # Prevent a long fourier vector from overlapping on table.
    if 22 < len(info['Fourier']) < 27:
        tab.get_celld()[(5, 0)].set_text_props(fontproperties=FontProperties(size=10))
    elif len(info['Fourier']) >= 27:
        fourier_ele = info['Fourier'].split(', ')
        fourier_len = np.array([len(ele) for ele in fourier_ele])
        which_max = np.argmin(fourier_len.cumsum() < 26)
        fourier_new = ', '.join(fourier_ele[:which_max]) + '...'
        tab.get_celld()[(5, 0)].set_text_props(
            fontproperties=FontProperties(size=10),
            text=fourier_new
        )


def plot_time(ax: plt.Axes,
              year_rom: pd.DataFrame,
              epri_dat: pd.DataFrame,
              **kwargs) -> None:
    """
    Plot time series comparison of original and sampled ROM.

    @In: ax, plt.Axes, current axes to plot data with.
    @In: year_rom, pd.DataFrame, ARMA output for the specified year
    @In: epri_dat, pd.DataFrame, Original EPRI data for specified year
    @Out: None
    """
    for _, dat in year_rom.groupby("RAVEN_sample_ID"):
        ax.plot(
            dat.HOUR.to_numpy(), dat.TOTALLOAD.to_numpy(),
            alpha=0.1, color="blue", label="Synthetic"
        )
    ax.plot(
        epri_dat.HOUR.to_numpy(), epri_dat.TOTALLOAD.to_numpy(),
        color="darkred", label="US-REGEN"
    )
    h, l = ax.get_legend_handles_labels()
    by_label = dict(zip(l, h))
    leg = ax.legend(by_label.values(), by_label.keys())
    for lh in leg.legendHandles:
        lh.set_alpha(1)
    ax.yaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
    # ax.set_xlabel("Period (Hour)")
    # ax.set_ylabel("Total Load (GW)")


def plot_hist(ax: plt.Axes,
              year_rom: pd.DataFrame,
              epri_dat: pd.DataFrame,
              **kwargs) -> None:
    """
    Plot histrogram comprarison of original and sampled ROM.

    @In: ax, plt.Axes, current axes to plot data with.
    @In: year_rom, pd.DataFrame, ARMA output for the specified year
    @In: epri_dat, pd.DataFrame, Original EPRI data for specified year
    @Out: None
    """
    plot_opts: PlotOpts = {"density": True, "bins": 50, "edgecolor": "black",}
    ax.hist(
        year_rom.TOTALLOAD.to_numpy(),
        color="blue", label="Synthetic", **plot_opts,
    )
    ax.hist(
        epri_dat.TOTALLOAD.to_numpy(),
        color="darkred", alpha=0.7, label="US-REGEN", **plot_opts,
    )
    ax.legend()


def plot_ecdf(ax: plt.Axes,
              year_rom: pd.DataFrame,
              epri_dat: pd.DataFrame,
              **kwargs) -> None:
    """
    Plot Load Duration Curves.

    @In: ax, plt.Axes, current axes to plot data with.
    @In: year_rom, pd.DataFrame, ARMA output for the specified year
    @In: epri_dat, pd.DataFrame, Original EPRI data for specified year
    @Out: None
    """
    epri_q, epri_p = ecdf(epri_dat.TOTALLOAD.to_numpy())
    custom_lines = [
        mpl.lines.Line2D([0], [0], color='blue', lw=4),    # type: ignore
        mpl.lines.Line2D([0], [0], color='darkred', lw=4)  # type: ignore
    ]

    for _, dat in year_rom.groupby("RAVEN_sample_ID"):
        sim_q, sim_p = ecdf(dat.TOTALLOAD.to_numpy())
        ax.plot(sim_p, sim_q, linestyle='-', color="blue", alpha=0.3, lw=1.5)  # type: ignore

    ax.plot(epri_p, epri_q, linestyle='-', color='darkred', lw=1.5)  # type: ignore
    ax.legend(custom_lines, ['Synthetic', 'US-REGEN'])


def plot_orig(ax: plt.Axes, _: pd.DataFrame, epri_dat: pd.DataFrame, **kwargs) -> None:
    """
    Plot Fourier decomposition on top of original data.

    @In: ax, plt.Axes, current axes to plot data with
    @In: _, pd.DataFrame, ARMA output unneeded for this plot
    @In: epri_dat, pd.DataFrame, Original EPRI data for specified year
    @Out: None
    """
    bases = [float(i) for i in kwargs['Fourier'].split(', ')]
    pivots = epri_dat.HOUR.to_numpy()
    values = epri_dat.TOTALLOAD.to_numpy()
    fourier = detrend(pivots, values, bases)
    ax.plot(pivots, values, color="darkred", label='US-REGEN')
    ax.plot(pivots, fourier, color="darkblue", label='Fourier Series')  # type: ignore
    ax.legend()

def plot_clust(ax: plt.Axes,
               year_rom: pd.DataFrame,
               _: pd.DataFrame,
               **kwargs) -> None:
    """
    Plot time series comparison of original and sampled ROM with
    highlighted cluster information.

    @In: ax, plt.Axes, current axes to plot data with.
    @In: year_rom, pd.DataFrame, ARMA output for the specified year
    @In: epri_dat, pd.DataFrame, Original EPRI data for specified year
    @Out: None
    """
    # Let's only plot the clusters of one sample.
    year_rom = year_rom.query("RAVEN_sample_ID == 0").iloc[:-1, :]
    for _, d, in year_rom.groupby("SEGMENT"):
        clust = np.unique(d.CLUSTER)[0]
        ax.plot(d.HOUR.to_numpy(), d.TOTALLOAD.to_numpy(), color=allc[clust])  # type: ignore
    ax.yaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))

def date_heatmap(series, ax, **kwargs):
    """
    Create calendar plot
    @In:
    @In:
    @Out:
    """
    # Combine values occurring on the same day.
    dates = series.index.floor('D')
    group = series.groupby(dates)
    series = group.mean()

    # Parse start/end, defaulting to the min/max of the index.
    start = pd.to_datetime(series.index.min())  # type: ignore
    end = pd.to_datetime(series.index.max())  # type: ignore

    # We use [start, end) as a half-open interval below.
    end += np.timedelta64(1, 'D')  # type: ignore

    # Get the previous/following Sunday to start/end.
    # Pandas and numpy day-of-week conventions are Monday=0 and Sunday=6.
    start_sun = start - np.timedelta64((start.dayofweek + 1) % 7, 'D')  # type: ignore
    end_sun = end + np.timedelta64(7 - end.dayofweek - 1, 'D')  # type: ignore

    # Create the heatmap and track ticks.
    num_weeks = (end_sun - start_sun).days // 7
    heatmap = np.nan * np.zeros((7, num_weeks))
    ticks = {}  # week number -> month name
    for week in range(num_weeks):
        for day in range(7):
            date = start_sun + np.timedelta64(7 * week + day, 'D')  # type: ignore
            if date.day == 1:
                ticks[week] = MONTHS[date.month - 1]
            if date.dayofyear == 1:
                ticks[week] += f'\n{date.year}'
            if start <= date < end:
                heatmap[day, week] = series.get(date, np.nan)

    # Get the coordinates, offset by 0.5 to align the ticks.
    y = np.arange(8) - 0.5
    x = np.arange(num_weeks + 1) - 0.5

    mesh = ax.pcolormesh(x, y, heatmap, cmap=COLORS, norm=NORM, rasterized=True, **kwargs)
    ax.invert_yaxis()

    ax.set_xticks(list(ticks.keys()))
    ax.set_xticklabels(list(ticks.values()))
    ax.set_yticks(np.arange(7))
    ax.set_yticklabels(DAYS)

    plt.sca(ax)
    plt.sci(mesh)

    return ax


def plot_cal(ax: plt.Axes,
             year_rom: pd.DataFrame,
             _: pd.DataFrame,
             **kwargs) -> None:
    """

    @In: ax, plt.Axes, current axes to plot data with.
    @In: year_rom, pd.DataFrame, ARMA output for the specified year
    @In: epri_dat, pd.DataFrame, Original EPRI data for specified year
    @In: kwargs, dict, extra options
    @Out: None
    """
    series = (
        year_rom.query("RAVEN_sample_ID == 0")[["TIMESTAMP", "CLUSTER"]]
        .set_index("TIMESTAMP")
        .squeeze()
    )
    ax = date_heatmap(series, ax=ax, edgecolor='black')
    # colorbar = plt.colorbar(
    #     orientation='horizontal', drawedges=True, pad=0.25,
    #     fraction=0.9
    # )
    # colorbar.set_ticks(np.arange(0, 31, 1) + 0.5)
    # colorbar.set_ticklabels(np.arange(0, 31, 1))
    # colorbar.outline.set_linewidth(2)  # type: ignore
    # colorbar.dividers.set_linewidth(2) # type: ignore
    # ax.set_aspect('equal')


def plot_ac(ax, _, epri_dat, **kwargs):
    sm.graphics.tsa.plot_acf(epri_dat.TOTALLOAD.squeeze(), lags=40, ax=ax)
    ax.set_xlabel('Lag')


def transform_data(file_path: Union[Path, pd.DataFrame], **kwargs) -> pd.DataFrame:
    """
    Add datetime column to a dataframe.

    @In: file_path, Path or pd.DataFrame, either read-in data or modify exisiting.
    @Out: pd.DataFrame, transformed dataframe.
    """
    # TODO: probably not good practice to anticipate a file_path or dataframe.
    if isinstance(file_path, pd.DataFrame):
        df = file_path
    else:
        df = pd.read_csv(file_path, engine='c', memory_map=True)

    year = pd.unique(df.YEAR)[0]
    df = df.assign(
        TIMESTAMP = pd.Timestamp(f'{year}-01-01') + pd.to_timedelta(df.HOUR, unit="H"), # type: ignore
        # Have to handle years where there are 366 days...
        SEGMENT = lambda x: x.TIMESTAMP.apply(lambda y: min(364, int(y.timetuple().tm_yday) - 1))
    )
    # Add cluster numbers as a column -- only to ROM data
    if kwargs:
        get_cluster = kwargs['clust']
        df = df.assign(CLUSTER = lambda x: x.SEGMENT.apply(lambda y: get_cluster(year, y)))
    return df


def load_data(args: argparse.Namespace, info) -> Callable[[], Iterator[Tuple[int, pd.DataFrame, pd.DataFrame]]]:
    """
    Return generator function to puke data for plot creation.

    @In: args, Namespace, arguments passed to the script
    @Out: function, a generator yielding dataframes in YEAR order
    """
    time_start = time.time()
    doi_path = args.parent_xml/info['WorkingDir']
    meta_path = doi_path/"romMeta.xml"
    sim_path = args.parent_xml/info['WorkingDir']/"tload_synth.csv"
    sim_dat = pd.read_csv(sim_path, engine='c', memory_map=True)


    # Load all needed data once instead of reading it in everytime.
    epri_dict = {
        # Add a few columns to the data on read-in.
        # Add 3 to i to start at Data_3.csv (year 2025; not 2015)
        year: transform_data(doi_path.joinpath(f"Data_{i+3}.csv"))
        for i, year in enumerate(YEARS)
    }

    sim_dict = {
        # Add cluster infomation to ROM output data
        year: transform_data(sim_dat.query("YEAR == @year"), clust=parse_meta(meta_path))
        for year in YEARS
    }

    def fetch_data() -> Iterator[Tuple[int, pd.DataFrame, pd.DataFrame]]:
        """Generator that yields the dataframe for a given YEAR."""
        for year in YEARS:
            year_rom = sim_dict[year]
            epri_dat = epri_dict[year]
            yield year, year_rom, epri_dat

    time_spent = round(time.time()-time_start, 3)
    print(f"Data Loaded! -- {time_spent} seconds")
    return fetch_data


def generate_plots(func: Callable[[plt.Axes, pd.DataFrame, pd.DataFrame], None],
                   info: Dict[str, str],
                   xmlhash: str,
                   args: argparse.Namespace,
                   fetch: Callable[[], Iterator[Tuple[int, pd.DataFrame, pd.DataFrame]]]) -> None:
    """
    Generate plots specified by higher-order-function.

    @In: func, function, a higher-order function plots specific details
    @In: info, dict, a dictionary containing model information
    @In: xmlhash, str, an sha1 hash of current xml file
    @In: fetch, function, a dataframe yielding function
    @Out: None
    """
    fig = plt.figure()
    start_time = time.time()
    grid_spec = (2, len(YEARS) // 2)
    if func.__name__ == 'plot_cal':
        # Reverse gridspec to be tall not wide
        grid_spec = grid_spec[::-1]
        fig.set_size_inches(22, 18)

    # Loop through all the dataframes seperated by YEARS
    for i, (year, year_rom, epri_dat) in enumerate(fetch()):
        # Assume we are plotting with no table added
        ax = fig.add_subplot(*grid_spec, i + 1)
        func(ax, year_rom, epri_dat, **info)
        ax.set_title(f"{year} Total Load")

    # We only want axis labels on specific subplots for specific plots.
    if func.__name__ in ['plot_orig', 'plot_time', 'plot_clust']:
        all_axes = fig.get_axes()
        all_axes[0].set_ylabel('Total Load (GW)')
        all_axes[3].set_ylabel('Total Load (GW)')
        for ax in all_axes[-3:]:
            ax.set_xlabel('Period (Hour)')

    if func.__name__ in ['plot_ecdf']:
        all_axes = fig.get_axes()
        all_axes[0].set_ylabel('Quantile')
        all_axes[3].set_ylabel('Quantile')
        for ax in all_axes[-3:]:
            ax.set_xlabel('Cumulative Probability')


    # If info is blank we can't add a table
    if args.add_tables and info:
        add_plot_table(fig, fig.get_axes(), info)

    if func.__name__ == 'plot_cal':
        fig.set_size_inches(35, 18)
        cbar_ax = fig.add_axes([0.93, 0.15, 0.05, 0.7])
        colorbar = plt.colorbar(
            cax=cbar_ax, orientation='vertical', drawedges=True
        )
        colorbar.set_ticks(np.arange(0, 31, 1) + 0.5)
        colorbar.set_ticklabels(np.arange(0, 31, 1))
        colorbar.outline.set_linewidth(2)  # type: ignore
        colorbar.dividers.set_linewidth(2) # type: ignore

    write_image(fig, args, xmlhash=xmlhash, func=func, start_time=start_time)


def write_image(fig: plt.Figure, args: argparse.Namespace, **kwargs) -> None:
    """
    Save plots to disk.

    @In: fig, Figure, figure to be saved
    @In: args, Namespace, program arguments
    @In: **kwargs, additional arguments
    @Out: None
    """
    xmlhash = kwargs.get('xmlhash')
    xmlfile = args.parent_xml/args.xml
    func = kwargs.get('func', False)
    func_name = func.__name__.split("_")[1] if func else ''
    fig_name = f"{func_name}_{xmlhash}.png"

    if args.subparser == 'single-plot':
        fig_name = f"{args.function}si_{xmlhash}.png"

    fig_path = args.parent_xml/fig_name

    # fig.tight_layout()
    fig.savefig(fig_path)
    fig.clf()

    time_spent = round(time.time()-kwargs['start_time'], 3)
    print(f"{fig_name} has been saved -- {time_spent} seconds")

    fig_dir = args.parent_xml/"figures"
    if args.embed_xml:
        embed_xml(
            xmlfile,
            fig_path,
            # Hacky way to split the name to add an 'em' before first '_'.
            fig_dir/"_".join([(fig_name.split("_"))[0] + "em"] + fig_name.split("_")[1:])
        )


def burn_plots(xml_file: Path) -> None:
    """
    Delete plots from working directory.

    If an embedded plot containing an xml file cannot be found in the
    ./figures directory, it will skip deleting the plot. This is to
    prevent plots from being accidently deleted.

    The plots that are output in the working directory are put there
    for convience and should not be versioned. Plots that need
    versioning should be embedded with an xml file and place in the
    working directory's ./figure folder.

    @In: xml_file, Path, path to current xml file.
    @Out: None
    """
    stage_dir = xml_file.parent
    save_dir = stage_dir.joinpath("figures")
    images = stage_dir.glob("*.png")

    for image in images:
        sep_name = image.name.split('_')
        new_name = sep_name[0] + "em_" + "_".join(sep_name[1:])
        if not save_dir.joinpath(new_name).exists():
            # print(f"Warning: Embedded png of {image.name} does not exist! Skipping...")
            continue
        print(f"Removing {image.name}")
        image.unlink()


def initialize(args):
    """
    @In: args, Namespace, program arguments
    @Out: xml_file, info, xmlhash, fetch
    """
    xml_file = args.xml.resolve()
    info = parse_xml(xml_file)
    xmlhash = hash_xml(xml_file)
    # Load up plotting data once to save time
    fetch = load_data(args, info)
    burn_plots(xml_file)
    return xml_file, info, xmlhash, fetch


def create_single_plot(args: argparse.Namespace) -> None:
    """
    Just create a single plot of one of the plotting functions.

    @In: args, Namespace, arguments given to script
    @Out: None
    """
    _, info, xmlhash, fetch = initialize(args)

    # If args specify specific year get that data from generator.
    year, year_rom, epri_dat = next(fetch())
    if args.year != 2025:
        which_year = np.argmax(np.array(YEARS) == args.year) + 1
        year_data = fetch()
        for _ in range(which_year):
            year, year_rom, epri_dat = next(year_data)

    start_time = time.time()
    fig = plt.figure()
    ax = fig.add_subplot(111)

    if args.function == 'og':
        plot_orig(ax, year_rom, epri_dat, **info)
        ax.set_xlabel("Period (Hour)")
        ax.set_ylabel("Total Load (GW)")
    elif args.function == 'ts':
        plot_time(ax, year_rom, epri_dat)
    elif args.function == 'hist':
        plot_hist(ax, year_rom, epri_dat)
    elif args.function == 'clust':
        plot_clust(ax, year_rom, epri_dat)
    elif args.function == 'ecdf':
        plot_ecdf(ax, year_rom, epri_dat)
    elif args.function == 'cal':
        plot_cal(ax, year_rom, epri_dat)
    elif args.function == 'ac':
        plot_ac(ax, year_rom, epri_dat)
    else:
        raise ValueError(f"{args.function} is not an available plotting method.")

    ax.set_title(f"{year} Total Load")
    write_image(fig, args, xmlhash=xmlhash, start_time=start_time)


def create_multiyear_plots(args: argparse.Namespace) -> None:
    """
    Create and possibly embed xml in plots.

    This is the main function for a script given with no flags or
    subarguments.

    @In: args, Namespace, arguments given to script
    @Out: None
    """
    _, info, xmlhash, fetch = initialize(args)

    # Pump-out all the plots
    plot_info: Info = {"info": info, "xmlhash": xmlhash, "args": args, "fetch": fetch}
    funcs = [plot_time, plot_hist, plot_ecdf, plot_clust, plot_orig, plot_cal]
    for plot_func in funcs:
        generate_plots(plot_func, **plot_info)


def extract_xml(png_file: Path) -> None:
    """
    Extract XML from png file.

    This is the main function for a script given with the extract-xml
    subcommand. This will extract the xml from a desired image and
    output in the working directory with the name: "train_<xml_hash>".
    Where <xml_hash> is the identifying hash of the original xml file
    that created the plot.

    @In: png_file, Path, path to png file containing xml
    @Out: None
    """
    if "em" not in png_file.name:
        raise ValueError(f"Specified file: {png_file} does not contain embedded xml.")
    png_hash = png_file.stem.split("_")[2]
    embedded_xml = decrypt_xml(png_file)
    with open(f"train_{png_hash}.xml", "w") as out:
        out.write(embedded_xml)
    # Check to make sure the new hash is the same as old hash
    if png_hash != hash_xml(Path(f"train_{png_hash}.xml")):
        print(
            "Warning: hash values are not equivalent!",
            "The extracted xml may not be what you expect",
        )


def main():
    """Driver Function."""
    parser = argparse.ArgumentParser(
        description="ARMA Plotting Script for EPRI Data"
    )
    parser.add_argument(
        "-t",
        "--add-tables",
        action="store_true",
        help="Add descriptive tables to plot margin.",
    )
    parser.add_argument(
        "-e",
        "--embed-xml",
        action="store_true",
        help="Embed current xml file into image output."
    )
    parser.add_argument(
        'xml',
        type=Path,
        help="Path to RAVEN input file"
    )

    # Add subcommands to this tool
    subparsers = parser.add_subparsers(dest="subparser")
    single_plot_parser = subparsers.add_parser("single-plot")
    single_plot_parser.add_argument("function", type=str)
    single_plot_parser.add_argument("--year", required=False, default=2025, type=int)
    extract_xml_parser = subparsers.add_parser("extract-xml")
    extract_xml_parser.add_argument("png", type=Path)

    args = parser.parse_args()
    # Add parent directory so we can use it throughout the script.
    args.parent_xml = args.xml.resolve().parent

    if args.subparser == "extract-xml":
        extract_xml(args.png)
    elif args.subparser == "single-plot":
        create_single_plot(args)
    else:
        create_multiyear_plots(args)


if __name__ == "__main__":
    main()
