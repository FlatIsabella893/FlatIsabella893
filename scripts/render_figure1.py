"""
Render Figure 1: Timeline of major technological advances in chicken genetics.

Style brief (from figure_prompts/Figure1_BioRender_Kiro_prompt.md):
- Publication style (Nature Reviews Genetics / Trends in Genetics / Poultry Science).
- White background, low-saturation lane bands, no cartoon icons.
- Five horizontal swimlanes; x-axis 1990-2030; phase dividers at 2010 and 2020.
- Capsule nodes with year + technique + superscript reference numbers.
- Bilingual EN / ZH labels; bottom "research-question upgrade chain" arrow.

Outputs:
- figures/Figure1_chicken_genetics_timeline.svg
- figures/Figure1_chicken_genetics_timeline.pdf
- figures/Figure1_chicken_genetics_timeline.png   (300 dpi)
"""

from __future__ import annotations

import os
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties, fontManager
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle

# ---------------------------------------------------------------------------
# Font setup (CJK + Latin)
# ---------------------------------------------------------------------------
CJK_FONT_PATH = "/root/.fonts/NotoSansCJKsc-Regular.otf"
if os.path.exists(CJK_FONT_PATH):
    fontManager.addfont(CJK_FONT_PATH)
    cjk_name = FontProperties(fname=CJK_FONT_PATH).get_name()
else:
    cjk_name = "Noto Sans"

mpl.rcParams["font.sans-serif"] = ["Noto Sans", cjk_name, "DejaVu Sans"]
mpl.rcParams["font.family"] = "sans-serif"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams["pdf.fonttype"] = 42
mpl.rcParams["svg.fonttype"] = "none"

# ---------------------------------------------------------------------------
# Figure geometry
# ---------------------------------------------------------------------------
X_MIN, X_MAX = 1989.0, 2030.5
PHASE_BOUNDARIES = (2010, 2020)

# Swimlane order top -> bottom on the canvas (we draw with y increasing upward,
# so lane index 0 is the top lane.)
LANES = [
    {
        "key": "markers",
        "title_en": "Molecular markers",
        "title_zh": "分子标记",
        "band": "#EEF3F8",
        "accent": "#3F6FAA",
    },
    {
        "key": "genome",
        "title_en": "Reference genome and variant resources",
        "title_zh": "参考基因组与变异资源",
        "band": "#EDEEF6",
        "accent": "#5C5CA6",
    },
    {
        "key": "popgen",
        "title_en": "Population and quantitative genetics",
        "title_zh": "群体与数量遗传研究",
        "band": "#ECF1EA",
        "accent": "#4F8A4F",
    },
    {
        "key": "omics",
        "title_en": "Functional annotation and multi-omics",
        "title_zh": "功能注释与多组学",
        "band": "#F4EFE4",
        "accent": "#A77A2E",
    },
    {
        "key": "editing",
        "title_en": "Genome editing and breeding design",
        "title_zh": "基因编辑与育种设计",
        "band": "#F5EAEA",
        "accent": "#A8474A",
    },
]

# y geometry (data units)
LANE_HEIGHT = 1.0
LANE_GAP = 0.15
N_LANES = len(LANES)

# Bottom area reserved for the "research question upgrade chain" arrow.
BOTTOM_PAD = 1.55
TOP_PAD = 1.45  # phase headers + main title

# Compute lane y centers (top lane drawn highest).
lane_centers = []
for i in range(N_LANES):
    # i=0 -> top
    y_center = BOTTOM_PAD + (N_LANES - 1 - i) * (LANE_HEIGHT + LANE_GAP) + LANE_HEIGHT / 2
    lane_centers.append(y_center)

Y_MAX = BOTTOM_PAD + N_LANES * LANE_HEIGHT + (N_LANES - 1) * LANE_GAP + TOP_PAD
Y_MIN = 0.0


# ---------------------------------------------------------------------------
# Node data
# ---------------------------------------------------------------------------
# Each node: (x, label_top, label_bottom, refs, big?)
# big nodes are drawn slightly larger / bolder per brief.

# helper to get unicode superscript references like "34", "43-45"
SUP_MAP = str.maketrans(
    {"0": "\u2070", "1": "\u00b9", "2": "\u00b2", "3": "\u00b3", "4": "\u2074",
     "5": "\u2075", "6": "\u2076", "7": "\u2077", "8": "\u2078", "9": "\u2079",
     "-": "\u207b"}
)


def sup(s: str) -> str:
    return s.translate(SUP_MAP)


nodes = {
    "markers": [
        (1993, "1990s",   "RFLP / RAPD",                 "34",     False),
        (1998, "1998",    "Microsatellite map",          "35",     False),
        (2001, "2000",    "Consensus linkage map",       "36",     False),
        (2011, "2011",    "60K SNP chip",                "38",     False),
        (2014, "2013",    "600K SNP array",              "39",     False),
    ],
    "genome": [
        (2004, "2004",    "Chicken draft genome",        "46",     True),
        (2007, "2004",    "2.8M SNP map",                "47",     False),
        (2017, "2017",    "Improved assembly",           "7",      False),
        (2021, "2021",    "Chicken pangenome",           "8",      True),
        (2024, "2023",    "Graph pangenome",             "49",     False),
        (2028.5, "Future","T2T / long-read",             "",       False),
    ],
    "popgen": [
        (2003, "2000s",   "QTL mapping",                 "6",      False),
        (2010.5, "2010",  "Selection signals",           "48",     False),
        (2014, "2010s",   "GWAS production traits",      "43-45",  False),
        (2020, "2020",    "863-genome domestication",    "13",     True),
        (2024, "2020s",   "Genomic selection / ssGBLUP", "65-68",  False),
        (2027.5, "2020s", "Host-microbiome",             "69-70",  False),
    ],
    "omics": [
        (2021, "2021",    "FAANG annotation",            "9",      False),
        (2022.5, "2022",  "ATAC-seq atlas",              "50",     False),
        (2023.7, "2023",  "Regulatory element atlas",    "10",     False),
        (2024.6, "2020s", "Single-cell omics",           "51-53",  False),
        (2025.7, "2025",  "ChickenGTEx",                 "11",     True),
        (2027.2, "2025",  "Egg-laying mol. QTL",         "81-83",  False),
    ],
    "editing": [
        (2014, "2010s",   "PGC germline platform",       "57-58",  True),
        (2021, "2020s",   "CRISPR/Cas9 editing",         "12",     True),
        (2023.5, "2023",  "ANP32A flu resistance",       "111",    False),
        (2027, "Future",  "Base / prime / multiplex",    "12,59",  False),
        (2029.5, "Future","GS + editing system",         "",       False),
    ],
}


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------
def draw_lane_band(ax, y_center, color):
    rect = Rectangle(
        (X_MIN + 0.4, y_center - LANE_HEIGHT / 2),
        (X_MAX - X_MIN) - 0.8,
        LANE_HEIGHT,
        facecolor=color,
        edgecolor="none",
        zorder=1,
    )
    ax.add_patch(rect)


def draw_lane_title(ax, y_center, title_en, title_zh, accent):
    # Left-side title block, sitting slightly inside the band.
    ax.text(
        X_MIN + 0.7, y_center + 0.16,
        title_en,
        fontsize=8.4, fontweight="bold", color=accent,
        va="center", ha="left", zorder=4,
    )
    ax.text(
        X_MIN + 0.7, y_center - 0.18,
        title_zh,
        fontsize=7.6, color="#444444",
        va="center", ha="left", zorder=4,
    )


def draw_axis_line(ax, y_center, accent):
    ax.plot(
        [X_MIN + 4.6, X_MAX - 0.6], [y_center, y_center],
        color=accent, alpha=0.55, linewidth=0.9, zorder=2,
    )


def draw_node(ax, x, y_center, label_top, label_bottom, refs, accent, big=False):
    # Tick on lane axis
    ax.plot([x, x], [y_center - 0.06, y_center + 0.06],
            color=accent, alpha=0.7, linewidth=0.9, zorder=3)

    # Capsule
    body_fontsize = 7.4 if not big else 8.2
    year_fontsize = 6.6 if not big else 7.2

    text = label_bottom
    if refs:
        text = f"{label_bottom}{sup(refs)}"

    # Two-line label inside capsule: year (small) on top, technique below.
    # Estimate width from text length.
    base_w = max(2.0, 0.18 * len(label_bottom) + 0.6)
    if big:
        base_w += 0.4
    w = base_w
    h = 0.46 if not big else 0.54

    # Place capsule above the line for odd index, below for even, to reduce
    # overlap. We'll alternate based on x position parity within lane.
    # Simpler: always above the line, with a leader line to the tick.
    cy = y_center + 0.34 if not big else y_center + 0.40

    box = FancyBboxPatch(
        (x - w / 2, cy - h / 2), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.18",
        linewidth=0.9 if not big else 1.3,
        edgecolor=accent,
        facecolor="white",
        zorder=5,
    )
    ax.add_patch(box)

    # Leader line
    ax.plot([x, x], [y_center + 0.06, cy - h / 2],
            color=accent, alpha=0.7, linewidth=0.7, zorder=4)

    # Year (tiny, top of capsule)
    ax.text(x, cy + 0.10, label_top,
            fontsize=year_fontsize, color=accent,
            ha="center", va="center", zorder=6,
            fontweight="bold" if big else "normal")

    # Technique + refs
    ax.text(x, cy - 0.09, text,
            fontsize=body_fontsize, color="#1f1f1f",
            ha="center", va="center", zorder=6,
            fontweight="bold" if big else "normal")


def draw_phase_dividers(ax):
    for x in PHASE_BOUNDARIES:
        ax.plot([x, x], [BOTTOM_PAD - 0.05, Y_MAX - TOP_PAD + 0.7],
                color="#999999", linewidth=0.8, linestyle=(0, (4, 3)),
                zorder=2, alpha=0.7)


def draw_phase_headers(ax):
    top_y = Y_MAX - TOP_PAD + 0.80
    sub_y = Y_MAX - TOP_PAD + 0.45

    phases = [
        (
            (X_MIN + 4.6 + 1990) / 2 if False else (1990 + 2010) / 2,
            "Phase I  1990-2010",
            "Low-density marker and linkage era",
            "低密度标记与连锁定位阶段",
        ),
        (
            (2010 + 2020) / 2,
            "Phase II  2010-2020",
            "Genome-wide association & population genomics era",
            "全基因组关联与群体基因组阶段",
        ),
        (
            (2020 + 2030) / 2,
            "Phase III  2020-2030",
            "Multi-omics, pangenome & genome editing era",
            "多组学、泛基因组与基因编辑阶段",
        ),
    ]
    for cx, head, sub_en, sub_zh in phases:
        ax.text(cx, top_y, head,
                fontsize=9.2, fontweight="bold", color="#222222",
                ha="center", va="center", zorder=4)
        ax.text(cx, sub_y, sub_en,
                fontsize=7.6, color="#444444",
                ha="center", va="center", zorder=4)
        ax.text(cx, sub_y - 0.27, sub_zh,
                fontsize=7.2, color="#666666",
                ha="center", va="center", zorder=4)


def draw_year_axis(ax):
    y = BOTTOM_PAD - 0.15
    ax.plot([X_MIN + 4.6, X_MAX - 0.4], [y, y],
            color="#444444", linewidth=0.8, zorder=3)
    for yr in (1990, 1995, 2000, 2005, 2010, 2015, 2020, 2025, 2030):
        ax.plot([yr, yr], [y, y - 0.08], color="#444444",
                linewidth=0.8, zorder=3)
        ax.text(yr, y - 0.22, str(yr), fontsize=7.4, color="#333333",
                ha="center", va="top", zorder=3)


def draw_bottom_chain(ax):
    # Research question upgrade chain
    y_arrow = 0.55
    x0 = X_MIN + 4.6
    x1 = X_MAX - 0.6

    arrow = FancyArrowPatch(
        (x0, y_arrow), (x1, y_arrow),
        arrowstyle="-|>", mutation_scale=14,
        linewidth=1.6, color="#2f4858", zorder=5,
    )
    ax.add_patch(arrow)

    stages_en = ["Locus discovery", "Causal variant",
                 "Cell / tissue mechanism", "Breeding translation"]
    stages_zh = ["位点发现", "因果变异", "组织 / 细胞机制", "育种转化"]

    n = len(stages_en)
    for i, (en, zh) in enumerate(zip(stages_en, stages_zh)):
        cx = x0 + (x1 - x0) * (i + 0.5) / n
        # small marker
        ax.plot([cx], [y_arrow], marker="o", markersize=5,
                color="#2f4858", zorder=6)
        ax.text(cx, y_arrow + 0.20, en,
                fontsize=8.4, fontweight="bold", color="#2f4858",
                ha="center", va="bottom", zorder=6)
        ax.text(cx, y_arrow - 0.22, zh,
                fontsize=7.8, color="#2f4858",
                ha="center", va="top", zorder=6)


def draw_titles(ax):
    ax.text(X_MIN + 0.4, Y_MAX - 0.32,
            "Figure 1  Timeline of major technological advances in chicken genetics",
            fontsize=12.5, fontweight="bold", color="#111111",
            ha="left", va="center", zorder=10)
    ax.text(X_MIN + 0.4, Y_MAX - 0.66,
            "图 1  家鸡遗传学主要技术进展时间线",
            fontsize=10.5, color="#333333",
            ha="left", va="center", zorder=10)


# ---------------------------------------------------------------------------
# Main render
# ---------------------------------------------------------------------------
def render():
    fig_w_in, fig_h_in = 16.0, 9.0
    fig, ax = plt.subplots(figsize=(fig_w_in, fig_h_in))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    ax.set_xlim(X_MIN, X_MAX)
    ax.set_ylim(Y_MIN, Y_MAX)
    ax.set_aspect("auto")
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])

    # Lane bands
    for lane, y_center in zip(LANES, lane_centers):
        draw_lane_band(ax, y_center, lane["band"])

    # Phase dividers + headers
    draw_phase_dividers(ax)
    draw_phase_headers(ax)

    # Lane titles + per-lane axes
    for lane, y_center in zip(LANES, lane_centers):
        draw_lane_title(ax, y_center, lane["title_en"], lane["title_zh"],
                        lane["accent"])
        draw_axis_line(ax, y_center, lane["accent"])

    # Nodes
    for lane, y_center in zip(LANES, lane_centers):
        for x, top, bottom, refs, big in nodes[lane["key"]]:
            draw_node(ax, x, y_center, top, bottom, refs, lane["accent"], big)

    # Year axis
    draw_year_axis(ax)

    # Research question upgrade chain
    draw_bottom_chain(ax)

    # Titles
    draw_titles(ax)

    out_dir = Path(__file__).resolve().parent.parent / "figures"
    out_dir.mkdir(exist_ok=True)

    svg_path = out_dir / "Figure1_chicken_genetics_timeline.svg"
    pdf_path = out_dir / "Figure1_chicken_genetics_timeline.pdf"
    png_path = out_dir / "Figure1_chicken_genetics_timeline.png"

    fig.savefig(svg_path, bbox_inches="tight", pad_inches=0.15)
    fig.savefig(pdf_path, bbox_inches="tight", pad_inches=0.15)
    fig.savefig(png_path, bbox_inches="tight", pad_inches=0.15, dpi=300)
    plt.close(fig)

    print(f"wrote: {svg_path}")
    print(f"wrote: {pdf_path}")
    print(f"wrote: {png_path}")


if __name__ == "__main__":
    render()
