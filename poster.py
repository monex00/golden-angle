"""
poster.py: still renders of the tree, in an ink-on-paper style.

Four plates:

    tree    one tree, dense enough that the tone is pure branch density
    grid    nine trees, one parameter swept
    angle   137.5 degrees against 137.0, as a sunflower head
    cone    a single step of the recurrence, drawn out

The visual rules, all four plates:

  - two palettes, both strictly MONOCHROME:
      paper  bg #f4f0e8  ink #383b3e
      night  bg #1d252b  ink #fbfcfc
  - tone comes from DENSITY, not from a colormap: hundreds of thousands of thin
    strokes at partial opacity, overlapping into greys. No grey is ever named
  - axes and spines fully off, equal aspect, artwork bleeding to the edge
  - the generating formula typeset underneath

`build_tree` is NOT duplicated here: it is imported from the notebook, which
stays the single source of truth. A marimo notebook is an ordinary Python
module, and `app.run()` hands back every definition in it.

    uv run python poster.py
"""

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

import fractal_tree

_OUT, _DEFS = fractal_tree.app.run()
build_tree = _DEFS["build_tree"]
PSI = _DEFS["PSI"]

# --- palettes --------------------------------------------------------------
# alpha and line width are part of the palette, not separate knobs: on paper
# the ink accumulates toward the dark and tolerates high alpha; on a dark
# ground white saturates almost immediately, so it needs far less opacity for
# density to stay readable as tone.
PAPER = dict(bg="#f4f0e8", ink="#383b3e", alpha=0.80, lw=2.6)
NIGHT = dict(bg="#1d252b", ink="#fbfcfc", alpha=0.22, lw=1.7)

FORMULA = r"$\mathbf{v}_{n+1}=\mathrm{norm}\left(\cos\theta\,\mathbf{v}_n+\sin\theta\,\mathbf{u}(\psi)\right)$"
ANGLE = r"$\psi=\pi(3-\sqrt{5})\approx 137.5^\circ$"

DPI = 200       # full-size plates
DOCS_DPI = 113  # same drawing, ~610px wide, for the README previews
ELEV = 0.18     # camera elevation


# --- geometry --------------------------------------------------------------
def project(P, azim, elev):
    """Orthographic 3D -> 2D. Orthographic rather than perspective keeps the
    image graphic and flat, which is the right register for this style."""
    ca, sa = np.cos(azim), np.sin(azim)
    ce, se = np.cos(elev), np.sin(elev)
    right = np.array([-sa, ca, 0.0])
    up = np.array([-ca * se, -sa * se, ce])
    return np.stack([P @ right, P @ up], axis=-1)


def tree_segments(tree, azim, elev, lw0, leonardo, branches):
    """Project the tree; return (segments, widths, bbox).

    Matplotlib accepts a width PER SEGMENT, which Plotly does not, so
    Leonardo's rule (r_parent^2 = sum of r_child^2, i.e.
    r_child = r_parent * b^(-1/2)) can be applied for real here.
    """
    segs, widths = [], []
    for lv, (A, B) in enumerate(tree["levels"]):
        a, b = project(A, azim, elev), project(B, azim, elev)
        segs.append(np.stack([a, b], axis=1))
        w = lw0 * (branches ** (-lv / 2.0)) if leonardo else lw0 * 0.74**lv
        widths.append(np.full(len(a), max(w, 0.12)))
    S = np.concatenate(segs)
    pts = S.reshape(-1, 2)
    return S, np.concatenate(widths), (pts.min(axis=0), pts.max(axis=0))


def frame_bbox(ax, lo, hi, pad=0.04):
    """Limits hugging the drawing: no letterboxing, no dead space."""
    d = (hi - lo).max() * pad
    ax.set_xlim(lo[0] - d, hi[0] + d)
    ax.set_ylim(lo[1] - d, hi[1] + d)
    ax.set_aspect("equal", "box")
    ax.set_axis_off()


def place_axes(fig, band, aspect):
    """Place an axes of ratio `aspect` (w/h) centred inside `band`
    (x0, y0, w, h in figure coordinates). This is what makes the drawing fill
    the frame: with a mismatched axes shape, equal aspect leaves empty bands."""
    fw, fh = fig.get_size_inches()
    x0, y0, w, h = band
    bw, bh = w * fw, h * fh
    if bw / bh > aspect:           # band too wide -> shrink in x
        nw, nh = bh * aspect, bh
    else:                          # band too tall -> shrink in y
        nw, nh = bw, bw / aspect
    return fig.add_axes([
        x0 + (bw - nw) / 2 / fw, y0 + (bh - nh) / 2 / fh, nw / fw, nh / fh
    ])


def draw_tree(ax, tree, ink, azim=0.9, elev=ELEV, lw0=2.6, alpha=0.9,
              leonardo=True, branches=2):
    """Draw the tree as a single LineCollection."""
    S, W, (lo, hi) = tree_segments(tree, azim, elev, lw0, leonardo, branches)
    ax.add_collection(LineCollection(
        S, linewidths=W, colors=ink, alpha=alpha,
        capstyle="round", antialiased=True,
    ))
    frame_bbox(ax, lo, hi)


def blank(figsize, pal, dpi=DPI):
    fig = plt.figure(figsize=figsize, dpi=dpi)
    fig.set_facecolor(pal["bg"])
    return fig


# --- plate: one tree -------------------------------------------------------
def poster_tree(path, pal=PAPER, depth=10, branches=3, theta=0.62,
                ratio=0.74, gravity=0.05, jitter=0.035, seed=7, azim=0.9,
                dpi=DPI):
    tree = build_tree(depth=depth, branches=branches, theta=theta, ratio=ratio,
                      gravity=gravity, jitter=jitter, seed=seed)
    fig = blank((5.4, 6.75), pal, dpi)
    S, W, (lo, hi) = tree_segments(tree, azim, ELEV, pal["lw"], True, branches)
    ax = place_axes(fig, (0.03, 0.13, 0.94, 0.84),
                    (hi[0] - lo[0]) / (hi[1] - lo[1]))
    ax.set_facecolor(pal["bg"])
    ax.add_collection(LineCollection(S, linewidths=W, colors=pal["ink"],
                                     alpha=pal["alpha"], capstyle="round"))
    frame_bbox(ax, lo, hi)

    fig.text(0.5, 0.088, FORMULA, ha="center", va="center",
             color=pal["ink"], fontsize=11.5)
    fig.text(0.5, 0.045, ANGLE + r"$\qquad \theta=%.2f$" % theta,
             ha="center", va="center", color=pal["ink"], fontsize=10, alpha=0.75)
    fig.savefig(path, facecolor=pal["bg"], dpi=dpi)
    plt.close(fig)
    return tree["segments"]


# --- plate: nine trees, one parameter --------------------------------------
def poster_grid(path, pal=PAPER, thetas=None, depth=11, branches=2, dpi=DPI):
    if thetas is None:
        thetas = np.linspace(0.22, 1.15, 9)
    fig = blank((5.4, 6.75), pal, dpi)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.955, bottom=0.09,
                        wspace=0.0, hspace=0.10)
    for i, th in enumerate(thetas):
        ax = fig.add_subplot(3, 3, i + 1)
        ax.set_facecolor(pal["bg"])
        tree = build_tree(depth=depth, branches=branches, theta=float(th),
                          ratio=0.79, gravity=0.05, jitter=0.03, seed=7)
        draw_tree(ax, tree, pal["ink"], azim=0.9, lw0=1.0, alpha=pal["alpha"],
                  branches=branches)
        ax.set_title(r"$\theta=%.2f$" % th, color=pal["ink"], fontsize=8.5,
                     pad=2, alpha=0.8)

    fig.text(0.5, 0.055, r"one parameter: $\theta$",
             ha="center", color=pal["ink"], fontsize=13)
    fig.text(0.5, 0.026, "the opening of the child cone",
             ha="center", color=pal["ink"], fontsize=9, alpha=0.65)
    fig.savefig(path, facecolor=pal["bg"], dpi=dpi)
    plt.close(fig)


# --- plate: 137.5 against 137.0 --------------------------------------------
def poster_angle(path, pal=PAPER, n=1400, dpi=DPI):
    fig = blank((5.4, 6.75), pal, dpi)
    fig.subplots_adjust(left=0.03, right=0.97, top=0.86, bottom=0.18,
                        hspace=0.16)
    k = np.arange(n)
    for i, (deg, label) in enumerate(
        [(137.5077, r"$\psi=\pi(3-\sqrt{5})$"), (137.0, r"$137.0^\circ$")]
    ):
        ax = fig.add_subplot(2, 1, i + 1)
        ax.set_facecolor(pal["bg"])
        a = np.radians(deg) * k
        r = np.sqrt(k)
        ax.scatter(r * np.cos(a), r * np.sin(a), s=2.4, c=pal["ink"],
                   linewidths=0.0, alpha=0.9)
        ax.set_aspect("equal", "box")
        ax.set_axis_off()
        ax.set_title(label, color=pal["ink"], fontsize=12, pad=4)

    fig.text(0.5, 0.925, "half a degree apart",
             ha="center", color=pal["ink"], fontsize=15)
    for j, line in enumerate([
        r"$1/\varphi=[0;1,1,1,\dots]$ : the worst-approximable",
        "irrational. No rational shortcut,",
        "so no empty lane.",
    ]):
        fig.text(0.5, 0.118 - j * 0.037, line, ha="center",
                 color=pal["ink"], fontsize=10.5)
    fig.savefig(path, facecolor=pal["bg"], dpi=dpi)
    plt.close(fig)


# --- plate: the cone, a single step ----------------------------------------
def poster_cone(path, pal=PAPER, theta=0.62, n_children=6, dpi=DPI):
    fig = blank((5.4, 6.75), pal, dpi)
    ax = fig.add_axes([0.06, 0.30, 0.88, 0.62])
    ax.set_facecolor(pal["bg"])
    az, el = 1.15, 0.30

    v = np.array([0.0, 0.0, 1.0])
    e1 = np.array([1.0, 0.0, 0.0])
    e2 = np.cross(v, e1)
    apex = np.cos(theta) * v          # centre of the circle of children

    t = np.linspace(0, 2 * np.pi, 400)
    ring = apex + np.sin(theta) * (
        np.cos(t)[:, None] * e1 + np.sin(t)[:, None] * e2
    )
    R = project(ring, az, el)
    ax.plot(R[:, 0], R[:, 1], color=pal["ink"], lw=0.9, alpha=0.4)

    V = project(np.stack([np.zeros(3), v * 1.18]), az, el)
    ax.plot(V[:, 0], V[:, 1], color=pal["ink"], lw=2.4)
    ax.annotate(r"$\mathbf{v}_n$", V[1], color=pal["ink"], fontsize=14,
                xytext=(7, -2), textcoords="offset points")

    C = project(apex[None], az, el)[0]
    for i in range(n_children):
        psi = (i + 1) * PSI
        u = np.cos(psi) * e1 + np.sin(psi) * e2
        d = np.cos(theta) * v + np.sin(theta) * u
        D = project(np.stack([np.zeros(3), d]), az, el)
        # the circle's radius IS sin(theta)*u(psi): draw it where it actually
        # lives, from the axis out to the rim, not as a vector at the origin
        ax.plot([C[0], D[1, 0]], [C[1], D[1, 1]],
                color=pal["ink"], lw=0.7, alpha=0.35, ls=(0, (1, 2)))
        ax.plot(D[:, 0], D[:, 1], color=pal["ink"], lw=1.6, alpha=0.9)
        ax.annotate(r"$%d\psi$" % (i + 1), D[1], color=pal["ink"], fontsize=8.5,
                    alpha=0.75, xytext=(5, 3), textcoords="offset points")

    ax.plot([C[0]], [C[1]], marker="o", ms=2.5, color=pal["ink"], alpha=0.6)

    # theta arc between the axis and one child, placed in the clear sector
    d1 = np.cos(theta) * v + np.sin(theta) * (np.cos(PSI) * e1 + np.sin(PSI) * e2)
    s = np.linspace(0, 1, 60)[:, None]
    arc = (1 - s) * v + s * d1
    arc = 0.42 * arc / np.linalg.norm(arc, axis=1, keepdims=True)
    Aq = project(arc, az, el)
    ax.plot(Aq[:, 0], Aq[:, 1], color=pal["ink"], lw=1.0, alpha=0.55)
    ax.annotate(r"$\theta$", Aq[len(Aq) // 2], color=pal["ink"], fontsize=13,
                xytext=(7, -6), textcoords="offset points")

    pts = np.vstack([R, V, project(np.stack([np.zeros(3), v]), az, el)])
    frame_bbox(ax, pts.min(axis=0), pts.max(axis=0), pad=0.10)

    fig.text(0.5, 0.225, FORMULA, ha="center", color=pal["ink"], fontsize=11.5)
    for j, line in enumerate([
        r"$\theta$ says how wide to open the cone.",
        r"$\psi$ says where to sit on the cone.",
        "Two degrees of freedom, independent.",
    ]):
        fig.text(0.5, 0.155 - j * 0.038, line, ha="center",
                 color=pal["ink"], fontsize=10.5, alpha=0.8)
    fig.savefig(path, facecolor=pal["bg"], dpi=dpi)
    plt.close(fig)


if __name__ == "__main__":
    import argparse
    import pathlib

    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--docs", action="store_true",
                    help="regenerate the README previews in docs/ instead")
    args = ap.parse_args()

    # The previews are the same drawing at a lower DPI, not a resized copy:
    # every length is in points, so the whole plate scales exactly. Rendering
    # small beats downscaling here: no resampling, and the type stays crisp.
    out = pathlib.Path("docs" if args.docs else "out")
    dpi = DOCS_DPI if args.docs else DPI
    out.mkdir(exist_ok=True)

    n = poster_tree(out / "tree.png", PAPER, depth=13, dpi=dpi)
    poster_grid(out / "grid.png", PAPER, dpi=dpi)
    poster_angle(out / "angle.png", PAPER, dpi=dpi)
    poster_cone(out / "cone.png", PAPER, dpi=dpi)
    if not args.docs:
        poster_tree(out / "tree_night.png", NIGHT, depth=13, azim=2.3, dpi=dpi)

    print(f"tree: {n:,} segments")
    for p in sorted(out.glob("*.png")):
        print(f"  {p}  {p.stat().st_size // 1024} KB")
