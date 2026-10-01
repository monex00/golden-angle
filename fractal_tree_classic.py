# /// script
# requires-python = ">=3.12"
# dependencies = ["marimo", "numpy", "plotly"]
# ///

import marimo

__generated_with = "0.24.0"
app = marimo.App(width="full", app_title="3d Fractal Tree")


@app.cell
def _():
    import marimo as mo
    import numpy as np
    import plotly.graph_objects as go

    PHI = (1.0 + np.sqrt(5.0)) / 2.0  # golden ratio
    PSI = np.pi * (3.0 - np.sqrt(5.0))  # golden angle (rad)
    return PHI, PSI, go, mo, np


@app.cell
def _(mo):
    mo.md(r"""
    # 🌲 3d Fractal Tree: golden-angle phyllotaxis

    Two formulas do all the work:

    $$\psi = \pi\,(3-\sqrt5) \approx 137.5^\circ
    \qquad
    \mathbf v_{n+1} = \operatorname{norm}\!\big(\cos\theta\,\mathbf v_n + \sin\theta\,\mathbf u(\psi)\big)$$

    Below: **what they mean**, **why they work**, and the tree itself with every
    parameter on a slider.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---
    ## 1. The golden angle $\psi$

    $\varphi = \frac{1+\sqrt5}{2}$. The golden angle is the full turn divided by $\varphi^2$:

    $$\psi = \frac{2\pi}{\varphi^{2}} = 2\pi\,(2-\varphi) = \pi\,(3-\sqrt5) \approx 2.39996\ \text{rad} = 137.5077^\circ$$

    **Why this angle.** If every new branch rotates by a fixed angle $\alpha$ around its
    parent, branches land on top of each other whenever $\alpha/2\pi$ is (or is
    close to) a rational $p/q$: after $q$ steps you are back where you started, and you get $q$
    crowded lanes with empty space between them.

    $1/\varphi$ has continued fraction $[0;1,1,1,\dots]$: it is the **worst-approximable**
    irrational number. So $\psi$ is the angle that avoids repeating itself for as long as
    possible → maximally uniform angular coverage. Same reason sunflower seeds use 137.5°.
    """)
    return


@app.cell
def _(PHI, PSI, mo, np):
    _rows = [
        ("phi = (1+sqrt5)/2", PHI),
        ("psi = pi(3-sqrt5)  [rad]", PSI),
        ("2pi/phi^2          [rad]", 2 * np.pi / PHI**2),
        ("psi                [deg]", np.degrees(PSI)),
        ("360 - psi          [deg]", 360 - np.degrees(PSI)),
    ]
    mo.md(
        "```\n" + "\n".join(f"{k:<28} = {v:.9f}" for k, v in _rows) + "\n```\n"
        "*Rows 2 and 3 agree: the two spellings are the same number.*"
    )
    return


@app.cell
def _(mo):
    phyllo_angle = mo.ui.slider(
        start=110.0,
        stop=160.0,
        step=0.05,
        value=137.51,
        label="divergence angle (degrees)",
        show_value=True,
        full_width=True,
    )
    phyllo_n = mo.ui.slider(
        start=50,
        stop=1500,
        step=50,
        value=600,
        label="number of seeds",
        show_value=True,
        full_width=True,
    )
    mo.vstack(
        [
            mo.md("### Try it: why 137.5 and not 137.0"),
            phyllo_angle,
            phyllo_n,
            mo.md(
                "Move it by **half a degree**: spiral arms and empty wedges appear "
                "immediately. Only the golden angle spreads the points evenly."
            ),
        ]
    )
    return phyllo_angle, phyllo_n


@app.cell
def _(go, np, phyllo_angle, phyllo_n):
    _k = np.arange(phyllo_n.value)
    _a = np.radians(phyllo_angle.value) * _k
    _r = np.sqrt(_k)
    phyllo_fig = go.Figure(
        go.Scatter(
            x=_r * np.cos(_a),
            y=_r * np.sin(_a),
            mode="markers",
            marker=dict(
                size=6,
                color=_k,
                colorscale=[[0, "#ff2bd1"], [1, "#2bd4ff"]],
                line=dict(width=0),
            ),
            hoverinfo="skip",
        )
    )
    phyllo_fig.update_layout(
        height=440,
        showlegend=False,
        margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="#05010a",
        plot_bgcolor="#05010a",
        xaxis=dict(visible=False, scaleanchor="y", scaleratio=1),
        yaxis=dict(visible=False),
    )
    phyllo_fig
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---
    ## 2. The branch recurrence

    $$\mathbf v_{n+1} = \operatorname{norm}\!\big(\cos\theta\,\mathbf v_n + \sin\theta\,\mathbf u(\psi)\big)$$

    In words: **take the parent's direction and tilt it by $\theta$ toward some
    perpendicular direction $\mathbf u$; $\psi$ picks which perpendicular.**

    | symbol | meaning |
    |---|---|
    | $\mathbf v_n$ | unit direction of the parent branch |
    | $\theta$ | parent-child opening angle (the `θ = 0.62` slider, ~35.5°) |
    | $\mathbf u(\psi)$ | unit vector **orthogonal** to $\mathbf v_n$, at azimuth $\psi$ in the normal plane |
    | $\operatorname{norm}$ | normalization |

    **The part the formula does not write down**, but that you need in order to
    implement it: $\mathbf u$ lives in the plane perpendicular to $\mathbf v_n$, so you
    need a **local orthonormal frame** $(\mathbf v_n, \mathbf e_1, \mathbf e_2)$ carried
    along the branch:

    $$\mathbf u(\psi) = \cos\psi\,\mathbf e_1 + \sin\psi\,\mathbf e_2,
    \qquad \mathbf e_2 = \mathbf v_n \times \mathbf e_1$$

    Since $\mathbf u \perp \mathbf v_n$ and both are unit vectors,
    $\|\cos\theta\,\mathbf v_n + \sin\theta\,\mathbf u\| = 1$ already:
    $\operatorname{norm}$ only guards against floating-point drift, **and** it becomes
    genuinely necessary as soon as you add gravity or noise (we do, below).

    The phase $\psi$ **accumulates** down the tree: child $k$ of a node with phase $\phi$
    gets $\phi + k\,\psi$. That is what scatters branches in 3D instead of flattening
    them onto a plane.

    The frame propagates by **parallel transport** (projection, not recomputation):

    $$\mathbf e_1' = \operatorname{norm}\big(\mathbf e_1 - (\mathbf e_1\cdot\mathbf v_{n+1})\,\mathbf v_{n+1}\big)$$

    Without this the tree snaps whenever a branch passes near vertical.
    """)
    return


@app.cell
def _(mo):
    demo_theta = mo.ui.slider(
        start=0.0,
        stop=1.4,
        step=0.01,
        value=0.62,
        label="theta (rad)",
        show_value=True,
        full_width=True,
    )
    demo_k = mo.ui.slider(
        start=1,
        stop=8,
        step=1,
        value=3,
        label="children to show",
        show_value=True,
        full_width=True,
    )
    mo.vstack([mo.md("### One step, up close"), demo_theta, demo_k])
    return demo_k, demo_theta


@app.cell
def _(PSI, demo_k, demo_theta, go, np):
    _v = np.array([0.0, 0.0, 1.0])
    _e1 = np.array([1.0, 0.0, 0.0])
    _e2 = np.cross(_v, _e1)
    _th = demo_theta.value

    _t = np.linspace(0, 2 * np.pi, 200)
    _ring = np.cos(_th) * _v + np.sin(_th) * (
        np.cos(_t)[:, None] * _e1 + np.sin(_t)[:, None] * _e2
    )

    demo_fig = go.Figure()
    demo_fig.add_trace(
        go.Scatter3d(
            x=[0, _v[0]],
            y=[0, _v[1]],
            z=[0, _v[2]],
            mode="lines+text",
            line=dict(color="#ff2bd1", width=10),
            text=["", "v_n"],
            textposition="top center",
            textfont=dict(color="#ff2bd1", size=15),
            hoverinfo="skip",
        )
    )
    demo_fig.add_trace(
        go.Scatter3d(
            x=_ring[:, 0],
            y=_ring[:, 1],
            z=_ring[:, 2],
            mode="lines",
            line=dict(color="#5a4a7a", width=2),
            hoverinfo="skip",
        )
    )
    for _i in range(demo_k.value):
        _psi = (_i + 1) * PSI
        _u = np.cos(_psi) * _e1 + np.sin(_psi) * _e2
        _d = np.cos(_th) * _v + np.sin(_th) * _u
        _d = _d / np.linalg.norm(_d)
        demo_fig.add_trace(
            go.Scatter3d(
                x=[0, _d[0]],
                y=[0, _d[1]],
                z=[0, _d[2]],
                mode="lines",
                line=dict(color="#2bd4ff", width=6),
                hoverinfo="skip",
            )
        )
        demo_fig.add_trace(
            go.Scatter3d(
                x=[0, _u[0]],
                y=[0, _u[1]],
                z=[0, _u[2]],
                mode="lines",
                line=dict(color="#3a7f8f", width=2, dash="dot"),
                hoverinfo="skip",
            )
        )
    demo_fig.update_layout(
        height=460,
        showlegend=False,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="#05010a",
        uirevision="demo",
        scene=dict(
            bgcolor="#05010a",
            aspectmode="cube",
            xaxis=dict(visible=False, range=[-1.1, 1.1]),
            yaxis=dict(visible=False, range=[-1.1, 1.1]),
            zaxis=dict(visible=False, range=[-0.2, 1.2]),
            camera=dict(eye=dict(x=1.5, y=1.5, z=0.9)),
        ),
    )
    demo_fig
    return


@app.cell
def _(mo):
    mo.md(r"""
    Magenta = $\mathbf v_n$. Dotted = the candidate orthogonal directions $\mathbf u(\psi)$.
    Cyan = the children $\mathbf v_{n+1}$, all sitting on the **cone** of half-angle $\theta$.
    As $\theta \to 0$ the cone collapses (a stick); as $\theta \to \pi/2$ the children go
    horizontal (a flat crown).
    """)
    return


@app.cell
def _(np):
    def rotate_about(vec, axis, ang):
        """Vectorized Rodrigues: rotate `vec` about unit `axis` by `ang`."""
        c, s = np.cos(ang), np.sin(ang)
        dot = np.sum(axis * vec, axis=1, keepdims=True)
        return vec * c + np.cross(axis, vec) * s + axis * dot * (1.0 - c)

    def _hex_to_rgb(h):
        h = h.lstrip("#")
        return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))

    def palette_color(t, stops):
        """Sample a ramp of hex colors at `t` in [0,1]; returns 'rgb(r,g,b)'."""
        t = float(np.clip(t, 0.0, 1.0))
        n = len(stops) - 1
        i = min(int(t * n), n - 1)
        f = t * n - i
        a, b = _hex_to_rgb(stops[i]), _hex_to_rgb(stops[i + 1])
        r, g, bl = (round(a[j] + (b[j] - a[j]) * f) for j in range(3))
        return f"rgb({r},{g},{bl})"

    def seg_xyz(A, B):
        """Segments (A_i -> B_i) as three flat arrays, NaN as the separator.

        One Plotly trace draws a single polyline; a NaN lifts the pen. This is
        how thousands of disconnected segments fit into one trace instead of
        thousands of traces, which no browser survives.
        """
        n = len(A)
        out = []
        for i in range(3):
            arr = np.empty(3 * n)
            arr[0::3] = A[:, i]
            arr[1::3] = B[:, i]
            arr[2::3] = np.nan
            out.append(arr)
        return out

    return palette_color, rotate_about, seg_xyz


@app.cell
def _(PSI, np, rotate_about):
    def build_tree(
        depth=10,
        branches=2,
        theta=0.62,
        ratio=0.78,
        gravity=0.0,
        twist=0.0,
        jitter=0.0,
        seed=0,
        psi=PSI,
        base_len=1.0,
        max_segments=300_000,
    ):
        """Build the tree one level at a time, every branch of a level in
        parallel with numpy. Returns [(A, B), ...] per level plus stats.

        No recursion: the inner loop runs over `branches` (2-5 iterations), not
        over the number of branches. 4095 branches cost ~11 numpy passes instead
        of 4095 Python calls.
        """
        rng = np.random.default_rng(seed)

        A = np.zeros((1, 3))  # branch start point
        V = np.array([[0.0, 0.0, 1.0]])  # direction (z is up)
        E1 = np.array([[1.0, 0.0, 0.0]])  # transported local frame
        L = np.array([base_len])  # length
        PH = np.zeros(1)  # accumulated golden phase

        levels, total, truncated = [], 0, False

        for lv in range(depth + 1):
            B = A + V * L[:, None]
            levels.append((A, B))
            total += len(A)

            if lv == depth:
                break
            if total + len(A) * branches > max_segments:
                truncated = True
                break

            E2 = np.cross(V, E1)
            nA, nV, nE1, nL, nPH = [], [], [], [], []

            for k in range(branches):
                # --- the two lines that ARE the formula ------------------
                ph = PH + (k + 1) * psi
                U = np.cos(ph)[:, None] * E1 + np.sin(ph)[:, None] * E2
                D = np.cos(theta) * V + np.sin(theta) * U
                # --------------------------------------------------------
                if gravity:
                    # gravitropism. Adding a constant -z bends horizontal
                    # branches the most and leaves vertical ones untouched,
                    # which is what a real gravitational torque does.
                    D = D + np.array([0.0, 0.0, -gravity])
                if jitter:
                    D = D + jitter * rng.standard_normal(D.shape)
                D = D / np.linalg.norm(D, axis=1, keepdims=True)

                # parallel transport of the local frame. Because E1 is already
                # perpendicular to V, this projection is EXACTLY the minimal
                # rotation carrying the frame onto the new direction, the
                # discrete rotation-minimizing (Bishop) frame.
                F = E1 - np.sum(E1 * D, axis=1, keepdims=True) * D
                nrm = np.linalg.norm(F, axis=1, keepdims=True)
                bad = (nrm < 1e-8).ravel()
                if bad.any():
                    G = (
                        E2[bad]
                        - np.sum(E2[bad] * D[bad], axis=1, keepdims=True) * D[bad]
                    )
                    F[bad] = G
                    nrm[bad] = np.linalg.norm(G, axis=1, keepdims=True)
                F = F / nrm
                if twist:
                    F = rotate_about(F, D, twist)

                nA.append(B)
                nV.append(D)
                nE1.append(F)
                nL.append(L * ratio)
                nPH.append(ph)

            A = np.vstack(nA)
            V = np.vstack(nV)
            E1 = np.vstack(nE1)
            L = np.concatenate(nL)
            PH = np.concatenate(nPH)

        return {
            "levels": levels,
            "segments": total,
            "truncated": truncated,
            "depth": len(levels) - 1,
        }

    return (build_tree,)


@app.cell
def _(go, np, palette_color, seg_xyz):
    STOPS = ["#c400ff", "#ff2bd1", "#7a5cff", "#2bd4ff", "#8dfff2"]

    def tree_figure(
        tree,
        grow=None,
        glow=True,
        tips=True,
        width0=9.0,
        wshrink=0.74,
        stops=STOPS,
        height=760,
        azimuth=None,
        elevation=0.55,
        zoom=1.7,
        bg="#05010a",
        uirevision="tree",
    ):
        """One trace per depth level: Plotly only supports line width per trace,
        not per vertex, so grouping by level is what gives the trunk-to-tip
        taper. The glow is the same trace drawn wide at low opacity."""
        levels = tree["levels"]
        nd = max(len(levels) - 1, 1)
        traces, last_tip = [], None

        for lv, (A, B) in enumerate(levels):
            if grow is not None:
                f = float(np.clip(grow - lv, 0.0, 1.0))
                if f <= 0.0:
                    continue
                B = A + (B - A) * f
            X, Y, Z = seg_xyz(A, B)
            col = palette_color(lv / nd, stops)
            w = max(width0 * (wshrink**lv), 1.0)
            if glow:
                traces.append(
                    go.Scatter3d(
                        x=X,
                        y=Y,
                        z=Z,
                        mode="lines",
                        line=dict(color=col, width=w * 3.4),
                        opacity=0.06,
                        hoverinfo="skip",
                    )
                )
            traces.append(
                go.Scatter3d(
                    x=X,
                    y=Y,
                    z=Z,
                    mode="lines",
                    line=dict(color=col, width=w),
                    hoverinfo="skip",
                )
            )
            last_tip = B

        if tips and last_tip is not None and len(last_tip) <= 60_000:
            traces.append(
                go.Scatter3d(
                    x=last_tip[:, 0],
                    y=last_tip[:, 1],
                    z=last_tip[:, 2],
                    mode="markers",
                    marker=dict(
                        size=1.8, color=palette_color(1.0, stops), opacity=0.55
                    ),
                    hoverinfo="skip",
                )
            )

        fig = go.Figure(traces)
        scene = dict(
            bgcolor=bg,
            aspectmode="data",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False),
        )
        if azimuth is not None:
            scene["camera"] = dict(
                eye=dict(
                    x=zoom * float(np.cos(azimuth)),
                    y=zoom * float(np.sin(azimuth)),
                    z=elevation * zoom,
                ),
                center=dict(x=0, y=0, z=0),
                up=dict(x=0, y=0, z=1),
            )
        fig.update_layout(
            height=height,
            showlegend=False,
            margin=dict(l=0, r=0, t=0, b=0),
            # uirevision keeps the camera when a slider moves; without it the
            # view snaps back on every re-render
            paper_bgcolor=bg,
            uirevision=uirevision,
            scene=scene,
        )
        return fig

    return STOPS, tree_figure


@app.cell
def _(mo):
    mo.md(r"""
    ---
    ## 3. The tree

    `theta` and `psi` are the two parameters of the recurrence. The rest is what
    turns a mathematical fractal into something that looks alive:

    - **length ratio** $\lambda$: each child is $\lambda\times$ its parent. Above
      $\lambda \approx b^{-1/2}$ ($b$ = children per node) the crown goes dense and solid;
      below, sparse. The fractal dimension is $D = \log b / \log(1/\lambda)$.
    - **gravity**: bends every direction downward, i.e. gravitropism. Gives drooping branches.
    - **twist**: rotates the local frame at each level, so the crown spirals.
    - **noise**: breaks the exact symmetry. A little is enough to stop it reading as a fractal.
    """)
    return


@app.cell
def _(mo):
    ui_theta = mo.ui.slider(
        0.0,
        1.5,
        0.005,
        0.62,
        label="theta, opening (rad)",
        show_value=True,
        full_width=True,
    )
    ui_depth = mo.ui.slider(
        1, 14, 1, 11, label="depth", show_value=True, full_width=True
    )
    ui_branches = mo.ui.slider(
        2, 5, 1, 2, label="children per node", show_value=True, full_width=True
    )
    ui_ratio = mo.ui.slider(
        0.45, 0.95, 0.005, 0.79, label="length ratio", show_value=True, full_width=True
    )
    ui_gravity = mo.ui.slider(
        0.0, 0.6, 0.005, 0.06, label="gravity", show_value=True, full_width=True
    )
    ui_twist = mo.ui.slider(
        -1.0,
        1.0,
        0.01,
        0.0,
        label="twist (rad/level)",
        show_value=True,
        full_width=True,
    )
    ui_jitter = mo.ui.slider(
        0.0, 0.35, 0.005, 0.04, label="noise", show_value=True, full_width=True
    )
    ui_width = mo.ui.slider(
        3.0, 18.0, 0.5, 9.0, label="trunk thickness", show_value=True, full_width=True
    )
    ui_seed = mo.ui.number(0, 9999, 1, value=7, label="seed")
    ui_glow = mo.ui.checkbox(True, label="glow")
    ui_tips = mo.ui.checkbox(True, label="tips")

    controls = mo.hstack(
        [
            mo.vstack([ui_theta, ui_depth, ui_branches, ui_ratio]),
            mo.vstack([ui_gravity, ui_twist, ui_jitter, ui_width]),
            mo.vstack([ui_seed, ui_glow, ui_tips]),
        ],
        widths=[2, 2, 1],
        gap=2,
    )
    controls
    return (
        controls,
        ui_branches,
        ui_depth,
        ui_glow,
        ui_gravity,
        ui_jitter,
        ui_ratio,
        ui_seed,
        ui_theta,
        ui_tips,
        ui_twist,
        ui_width,
    )


@app.cell
def _(
    build_tree,
    ui_branches,
    ui_depth,
    ui_gravity,
    ui_jitter,
    ui_ratio,
    ui_seed,
    ui_theta,
    ui_twist,
):
    tree = build_tree(
        depth=ui_depth.value,
        branches=ui_branches.value,
        theta=ui_theta.value,
        ratio=ui_ratio.value,
        gravity=ui_gravity.value,
        twist=ui_twist.value,
        jitter=ui_jitter.value,
        seed=int(ui_seed.value),
    )
    return (tree,)


@app.cell
def _(mo, tree, tree_figure, ui_glow, ui_tips, ui_width):
    main_fig = tree_figure(
        tree,
        glow=ui_glow.value,
        tips=ui_tips.value,
        width0=ui_width.value,
        height=780,
    )
    mo.vstack(
        [
            main_fig,
            mo.md(
                f"`{tree['segments']:,} segments` · `depth {tree['depth']}`"
                + ("  **truncated** (segment cap reached)" if tree["truncated"] else "")
            ),
        ]
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---
    ## 4. Animation

    Driven by a counter that advances on every tick of `mo.ui.refresh`.
    The marimo pattern is: **one cell increments the state, another reads it**.
    Do both in one cell and you have a cycle in the dependency graph, which
    marimo refuses to run. `mo.state` is the intended escape hatch for exactly this.
    """)
    return


@app.cell
def _(mo):
    get_frame, set_frame = mo.state(0)
    return get_frame, set_frame


@app.cell
def _(mo):
    anim_play = mo.ui.checkbox(True, label="play")
    anim_mode = mo.ui.dropdown(
        options=["growth", "rotation", "pulsing theta", "growth + rotation"],
        value="growth + rotation",
        label="mode",
    )
    anim_speed = mo.ui.slider(0.02, 0.5, 0.01, 0.12, label="speed", show_value=True)
    anim_depth = mo.ui.slider(1, 12, 1, 9, label="depth (anim)", show_value=True)
    anim_tick = mo.ui.refresh(
        options=["0.1s", "0.2s", "0.5s"],
        default_interval="0.1s",
    )
    mo.hstack([anim_mode, anim_play, anim_speed, anim_depth, anim_tick], gap=1.5)
    return anim_depth, anim_mode, anim_play, anim_speed, anim_tick


@app.cell
def _(anim_play, anim_tick, set_frame):
    anim_tick  # dependency: this cell re-runs on every tick
    if anim_play.value:
        # a callable updater writes without reading, which is what keeps this
        # out of a cycle with the cell below
        set_frame(lambda f: f + 1)
    return


@app.cell
def _(
    anim_depth,
    anim_mode,
    anim_speed,
    build_tree,
    get_frame,
    np,
    tree_figure,
    ui_branches,
    ui_gravity,
    ui_jitter,
    ui_ratio,
    ui_seed,
    ui_theta,
    ui_twist,
):
    _t = get_frame() * anim_speed.value
    _mode = anim_mode.value
    _nd = anim_depth.value

    _theta = ui_theta.value
    if "theta" in _mode:
        _theta = 0.45 + 0.42 * (0.5 + 0.5 * np.sin(_t * 0.9))

    # +0.05 so the loop never lands on an empty frame; the trailing "+3" holds
    # the finished tree for a beat before restarting
    _grow = 0.05 + (_t * 0.8) % (_nd + 3.0) if "growth" in _mode else None
    _az = _t * 0.35 if "rotation" in _mode else None

    anim_tree = build_tree(
        depth=_nd,
        branches=ui_branches.value,
        theta=_theta,
        ratio=ui_ratio.value,
        gravity=ui_gravity.value,
        twist=ui_twist.value,
        jitter=ui_jitter.value,
        seed=int(ui_seed.value),
    )
    anim_fig = tree_figure(
        anim_tree,
        grow=_grow,
        azimuth=_az,
        height=680,
        uirevision=None if _az is not None else "anim",
    )
    anim_fig
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---
    ## 5. Presets

    Starting points worth trying. Copy the values into the sliders above.

    | preset | theta | children | lambda | gravity | twist | noise |
    |---|---|---|---|---|---|---|
    | **baseline** | 0.62 | 2 | 0.79 | 0.06 | 0.00 | 0.04 |
    | dense dome | 0.70 | 3 | 0.72 | 0.02 | 0.00 | 0.03 |
    | weeping willow | 0.55 | 2 | 0.84 | 0.30 | 0.00 | 0.06 |
    | cyclone | 0.75 | 3 | 0.75 | 0.05 | 0.55 | 0.02 |
    | coral | 1.05 | 4 | 0.66 | 0.00 | 0.20 | 0.10 |
    | pine | 0.35 | 3 | 0.80 | 0.12 | 0.00 | 0.02 |

    ---
    ## 6. Things to explore

    - **Leonardo's rule**: $r_{\text{parent}}^2 = \sum r_{\text{child}}^2$, i.e.
      $r_{\text{child}} = r_{\text{parent}}\,b^{-1/2}$. Here thickness scales per level
      (`wshrink`) because Plotly has no per-vertex line width. `poster.py` uses matplotlib,
      which does, and applies the real rule.
    - **Fractal dimension**: with $b$ children and ratio $\lambda$,
      $D = \log b / \log(1/\lambda)$. At $b=2, \lambda=0.79$ → $D \approx 2.94$: nearly
      solid, which is why the crown looks filled. Inverting, $\lambda = b^{-1/D}$ gives you
      the ratio for a chosen $D$. (The formula assumes non-overlapping copies; here they
      overlap heavily, so $D$ saturates at 3 in practice.)
    - **Finite crown, infinite wood**: the reach is $\sum \lambda^n = 1/(1-\lambda)$, which
      converges, but the total length is $\sum (b\lambda)^n$, which diverges when
      $b\lambda > 1$. Infinite length inside a bounded volume.
    - **Swap $\psi$**: try $2\pi/3$ (branches on three planes, very mechanical) or
      $\pi(3-\sqrt5)+0.01$ to see how fragile the spread is.
    - **Solid rendering**: `Mesh3d` with real cylinders and triangle leaves. Much more
      substantial, but costly; feasible below ~5k branches.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---
    ## 7. Exporting

    ```
    uv run marimo export html-wasm fractal_tree.py -o dist --mode run
    ```

    Produces a static page that runs **entirely in the browser** (Pyodide): working
    sliders, no server. Ready to publish.
    """)
    return


if __name__ == "__main__":
    app.run()
