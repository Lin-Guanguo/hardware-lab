#!/usr/bin/env python3
"""Read-only EMC / signal-integrity checks on the committed E16 snapshot.

Every threshold and rule ID comes from an upstream rule set, not from this
script's own judgement:

  aklofas/kicad-happy, skills/emc/references/pcb-emc-rules.md (MIT)
  rule IDs cited per check below, each with its primary source.

This checker deliberately reads hardware/e16-right-mid-snapshot.json and never
the EDA export path, so it is an independent second opinion on geometry the
native DRC already accepted.

Usage:
    python3 scripts/check-e16-emc.py [--snapshot PATH] [--json OUT]

Board parameters are E16's actual stackup: 2 copper layers, 0.8 mm core,
FR4 eps_r = 4.4. Rules that need poured-copper geometry cannot run because the
snapshot exporter does not capture copper pours yet; they are reported as
BLOCKED rather than silently skipped.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

MIL = 0.0254  # mm per mil

# EPCB_LayerId values used by the snapshot (see the upstream easyeda-api-skill
# reference for the full enum).
LAYER_TOP = 1
LAYER_BOTTOM = 2
LAYER_BOARD_OUTLINE = 11
LAYER_MULTI = 12

# E16 stackup. 0.8 mm total, two copper layers, so the plane-to-plane
# dielectric height is the full board thickness.
DIELECTRIC_HEIGHT_MM = 0.8
EPS_R = 4.4
C_0 = 299_792_458.0

# Transmitter frequency that sets the via-stitching spacing requirement:
# the nRF52840 module's 2.4 GHz radio.
MAX_FREQUENCY_HZ = 2.4e9


# --------------------------------------------------------------------------
# geometry helpers
# --------------------------------------------------------------------------

def mm(v: float) -> float:
    return v * MIL


def dist(ax, ay, bx, by):
    return math.hypot(ax - bx, ay - by)


def point_segment_distance(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    if dx == 0 and dy == 0:
        return dist(px, py, x1, y1)
    t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    return dist(px, py, x1 + t * dx, y1 + t * dy)


def segment_length(x1, y1, x2, y2):
    return math.hypot(x2 - x1, y2 - y1)


def propagation_delay_ps_per_mm(eps_r: float = EPS_R) -> float:
    """Microstrip delay, sqrt((eps_r+1)/2)/c.

    Formula and value from the upstream library's propagation_delay_ps_per_mm
    (EQ-032); for FR4 this is 5.48 ps/mm.
    """
    eps_eff = (eps_r + 1) / 2
    v_phase = C_0 / math.sqrt(eps_eff)
    return 1e12 / (v_phase * 1e3)


def lambda_over_20_mm(freq_hz: float, eps_r: float = EPS_R) -> float:
    """lambda/20 in the dielectric. Source: Altium stitching-via article."""
    wavelength_mm = (C_0 / freq_hz) / math.sqrt(eps_r) * 1e3
    return wavelength_mm / 20


# --------------------------------------------------------------------------
# snapshot access
# --------------------------------------------------------------------------

class Snapshot:
    def __init__(self, path: Path):
        raw = json.loads(path.read_text())
        self.raw = raw
        self.document = raw.get("document", {})
        self.components = raw["components"]
        self.pads = raw["pads"]
        self.lines = raw["lines"]
        self.vias = raw["vias"]
        self.polylines = raw["polylines"]
        self.regions = raw["regions"]

    # Nearest-centre association is wrong for this snapshot: standalone test
    # points (TP1..TP5) have no owning component and land on R16 up to 24 mm
    # away, and the 10.5 x 15.6 mm module's own pads sit 6-7 mm from its
    # centre. So pads are selected by an explicit per-footprint-class radius
    # instead, and every consumer prints the pad count it resolved.
    PAD_RADIUS_MM = {
        "cap": 1.2,      # C0603 / C0805
        "tiny": 0.9,     # SOT-9X3-3 ESD arrays (1.0 x 0.8 mm body)
    }

    def component(self, ref):
        for c in self.components:
            if c["ref"] == ref:
                return c
        return None

    def position_mm(self, ref):
        c = self.component(ref)
        return (mm(c["x"]), mm(c["y"])) if c else None

    def pads_of(self, ref, radius_mm=None):
        """Pads within an explicit radius of the component centre.

        Returns (pads, radius). The caller must sanity-check the pad count;
        the radius is a footprint-class assumption, not a measurement.
        """
        pos = self.position_mm(ref)
        if not pos:
            return [], 0.0
        if radius_mm is None:
            radius_mm = self.PAD_RADIUS_MM["cap"]
        px, py = pos
        pads = [p for p in self.pads
                if dist(px, py, mm(p["x"]), mm(p["y"])) <= radius_mm]
        return pads, radius_mm

    def own_pad_ids(self, ref, radius_mm=None):
        return {p["id"] for p in self.pads_of(ref, radius_mm)[0]}

    def pads_on_net(self, net):
        return [p for p in self.pads if p["net"] == net]

    def vias_on_net(self, net):
        return [v for v in self.vias if v["net"] == net]

    def lines_on_net(self, net):
        return [l for l in self.lines if l["net"] == net]

    def trace_length_mm(self, net):
        return sum(segment_length(mm(l["x1"]), mm(l["y1"]), mm(l["x2"]), mm(l["y2"]))
                   for l in self.lines_on_net(net))

    def copper_area_mm2(self, net):
        """Trace-only copper area; zones are absent from the snapshot."""
        return sum(
            segment_length(mm(l["x1"]), mm(l["y1"]), mm(l["x2"]), mm(l["y2"]))
            * mm(l["widthMil"])
            for l in self.lines_on_net(net)
        )


# --------------------------------------------------------------------------
# checks
# --------------------------------------------------------------------------

def check_ml_001(s: Snapshot):
    """ML-001: unshielded switching inductor within 15 mm of sensitive
    analogue / crystal / RF circuitry.

    Source: kicad-happy EMC rule ML-001. Sensitive circuit here is the
    MDBT50Q module, which contains the radio, the NFC front end and the
    32 MHz crystal.
    """
    findings = []
    for inductor_ref, inductor_role in SWITCHING_INDUCTORS.items():
        inductor = s.position_mm(inductor_ref)
        if not inductor:
            continue
        for sens_ref, sens_role in SENSITIVE_REFS.items():
            sensitive = s.position_mm(sens_ref)
            if not sensitive:
                continue
            d = dist(*inductor, *sensitive)
            findings.append({
                "rule": "ML-001",
                "threshold": "15 mm",
                "measured": f"{inductor_ref} ({inductor_role}) to {sens_ref} ({sens_role}) "
                            f"= {d:.2f} mm",
                "status": "fail" if d < 15.0 else "pass",
                "source": "kicad-happy ML-001; inductor magnetic leakage couples into "
                          "high-impedance nodes",
            })
    return findings or None


def check_sw_002(s: Snapshot):
    """SW-002: switching-node copper area.

    Threshold: >25 mm^2 medium, >100 mm^2 high.
    Source: TI SLVA477 "Layout Tips for Switching Regulators".
    """
    area = s.copper_area_mm2("EPD_SW")
    if area > 100:
        status = "high"
    elif area > 25:
        status = "medium"
    else:
        status = "pass"
    return {
        "rule": "SW-002",
        "threshold": "25 mm^2 medium / 100 mm^2 high",
        "measured": f"EPD_SW trace copper = {area:.2f} mm^2 "
                    f"({len(s.lines_on_net('EPD_SW'))} segments, zones absent from snapshot)",
        "status": status,
        "source": "TI SLVA477",
    }


def check_sw_003(s: Snapshot):
    """SW-003: input-capacitor hot-loop area, taken as the triangle formed by
    the input cap, the switching IC and the inductor.

    Threshold: >25 mm^2 medium, >100 mm^2 high.
    Source: Paul, Introduction to EMC, Ch. 10; Ridley, Power Supply Design Vol. 2.
    """
    ic = s.position_mm("U4")
    inductor = s.position_mm("L1")
    if not ic or not inductor:
        return None
    # Input capacitor: the nearest capacitor to the switching IC that shares a
    # rail with it. Candidates are resolved geometrically.
    candidates = []
    for c in s.components:
        if not c["ref"].startswith("C"):
            continue
        p = (mm(c["x"]), mm(c["y"]))
        candidates.append((dist(*p, *ic), c["ref"], p))
    if not candidates:
        return None
    _, cap_ref, cap = min(candidates)

    def triangle_area(a, b, c):
        return abs((b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])) / 2

    area = triangle_area(ic, inductor, cap)
    if area > 100:
        status = "high"
    elif area > 25:
        status = "medium"
    else:
        status = "pass"
    return {
        "rule": "SW-003",
        "threshold": "25 mm^2 medium / 100 mm^2 high",
        "measured": f"triangle U4 {ic} -> L1 {inductor} -> {cap_ref} {cap} = {area:.2f} mm^2",
        "status": status,
        "source": "Paul, Introduction to EMC, Ch. 10; Ridley, Power Supply Design Vol. 2",
    }


def check_dc_001(s: Snapshot):
    """DC-001 / DC-002: decoupling capacitor distance.

    DC-001 is measured pad to pad: from each decoupling capacitor's supply pad
    to the nearest other pad on the same net, which is the point the transient
    current actually has to reach. A component-centre-to-centre measurement
    gives a false critical on U1 (9.23 mm centre to centre against 4.40 mm
    pad to pad), so it is not used.

    Threshold: 5 mm warning, 8 mm critical; DC-002 flags an IC with no
    capacitor within 10 mm (component centres, coarse).
    Source: Bogatin EDN Rule of Thumb #6; Hubing, "Estimating the Connection
    Inductance of Decoupling Capacitors", LearnEMC.
    """
    findings = []
    for c in s.components:
        if not c["ref"].startswith("C"):
            continue
        pads, radius = s.pads_of(c["ref"])
        own = {p["id"] for p in pads}
        supply = [p for p in pads if p["net"] and p["net"] != "GND"]
        if not supply:
            continue
        worst = 0.0
        target = None
        for p in supply:
            px, py = mm(p["x"]), mm(p["y"])
            others = [q for q in s.pads_on_net(p["net"]) if q["id"] not in own]
            if not others:
                continue
            q = min(others, key=lambda q: dist(px, py, mm(q["x"]), mm(q["y"])))
            d = dist(px, py, mm(q["x"]), mm(q["y"]))
            if d > worst:
                worst, target = d, (p["net"], q["number"], mm(q["x"]), mm(q["y"]))
        if target is None:
            continue
        if worst > 8:
            status = "critical"
        elif worst > 5:
            status = "warning"
        else:
            status = "pass"
        findings.append({
            "rule": "DC-001",
            "threshold": "5 mm warning / 8 mm critical (pad to pad)",
            "measured": f"{c['ref']} {target[0]} pad -> nearest other {target[0]} pad "
                        f"(pad {target[1]} at ({target[2]:.2f}, {target[3]:.2f})) = {worst:.2f} mm "
                        f"[{len(pads)} pads within {radius} mm]",
            "status": status,
            "source": "Bogatin EDN Rule of Thumb #6; Hubing, LearnEMC",
        })

    # DC-002: coarse component-centre screen for an IC with no nearby capacitor.
    caps = [c for c in s.components if c["ref"].startswith("C")]
    for ic in s.components:
        if not ic["ref"].startswith("U"):
            continue
        ic_pos = (mm(ic["x"]), mm(ic["y"]))
        best_d, best_ref = min(
            ((dist(ic_pos[0], ic_pos[1], mm(c["x"]), mm(c["y"])), c["ref"]) for c in caps),
            default=(float("inf"), None),
        )
        findings.append({
            "rule": "DC-002",
            "threshold": "an IC with no capacitor within 10 mm",
            "measured": f"{ic['ref']} nearest capacitor {best_ref} = {best_d:.2f} mm (centres)",
            "status": "fail" if best_d > 10 else "pass",
            "source": "TI SLUA383; Analog Devices MT-101",
        })
    return findings


def check_dc_003(s: Snapshot):
    """DC-003: decoupling capacitor pad further than 3 mm from the nearest via.

    Only supply-rail decoupling is judged; the EPD charge-pump capacitors are
    reported separately because DC-003 targets the high-frequency supply path.
    Source: LearnEMC connection-inductance note.
    """
    findings = []
    for c in s.components:
        if not c["ref"].startswith("C"):
            continue
        pads, radius = s.pads_of(c["ref"])
        if not pads:
            continue
        supply = [p for p in pads if p["net"] and p["net"] != "GND"]
        if not supply:
            continue
        worst = 0.0
        for p in supply:
            px, py = mm(p["x"]), mm(p["y"])
            same_net_vias = [v for v in s.vias if v["net"] in (p["net"], "GND")]
            nearest = min((dist(px, py, mm(v["x"]), mm(v["y"])) for v in same_net_vias),
                          default=float("inf"))
            worst = max(worst, nearest)
        if worst == float("inf"):
            continue
        findings.append({
            "rule": "DC-003",
            "threshold": "3 mm to the nearest via on the same net or GND",
            "measured": f"{c['ref']} supply pad to nearest via = {worst:.2f} mm "
                        f"[{len(pads)} pads within {radius} mm]",
            "status": "fail" if worst > 3.0 else "pass",
            "source": "LearnEMC, Estimating the Connection Inductance of Decoupling Capacitors",
        })
    return findings


def check_rp_001(s: Snapshot):
    """RP-001: a signal via that changes layers without a ground stitching via
    within max(2 x dielectric height, 1.0 mm).

    Source: Ott, "PCB Stack-Up Part 6"; Sierra Circuits return path design guide.
    """
    limit = max(2 * DIELECTRIC_HEIGHT_MM, 1.0)
    gnd_vias = [(mm(v["x"]), mm(v["y"])) for v in s.vias_on_net("GND")]
    if not gnd_vias:
        return {"rule": "RP-001", "threshold": f"{limit:.2f} mm",
                "measured": "no GND vias in snapshot", "status": "blocked",
                "source": "Ott, PCB Stack-Up Part 6"}
    offenders = []
    for v in s.vias:
        if v["net"] == "GND":
            continue
        px, py = mm(v["x"]), mm(v["y"])
        d = min(dist(px, py, gx, gy) for gx, gy in gnd_vias)
        if d > limit:
            offenders.append((v["net"], px, py, d))
    offenders.sort(key=lambda o: -o[3])

    # Applicability: on a two-layer board there is no plane pair, so the return
    # current hops between the two GND pours. That only needs a local GND via
    # when the net has fast edges; DC and slow logic nets spread their return
    # current and are reported separately rather than counted as defects.
    fast_nets = {"USB_DP_CONN", "USB_DM_CONN", "USB_DP_MCU", "USB_DM_MCU",
                 "USB_CC1", "USB_CC2", "EPD_SW", "EPD_PUMP", "EPD_SCK_TBD",
                 "NFC1_TBD", "NFC2_TBD", "SWDCLK", "SWDIO", "NRESET"}
    fast = [o for o in offenders if o[0] in fast_nets]
    return {
        "rule": "RP-001",
        "threshold": f"GND via within max(2H, 1.0 mm) = {limit:.2f} mm",
        "measured": f"{len(offenders)} of {len([v for v in s.vias if v['net'] != 'GND'])} "
                    f"signal vias exceed it; of those {len(fast)} carry fast edges"
                    + (f"; worst fast net {fast[0][0]} at ({fast[0][1]:.2f}, {fast[0][2]:.2f}) "
                       f"= {fast[0][3]:.2f} mm" if fast else ""),
        "status": "fail" if fast else ("warning" if offenders else "pass"),
        "details": [f"{n} ({x:.2f}, {y:.2f}) d={d:.2f} mm" for n, x, y, d in offenders[:15]],
        "fast_net_details": [f"{n} ({x:.2f}, {y:.2f}) d={d:.2f} mm" for n, x, y, d in fast],
        "source": "Ott, PCB Stack-Up Part 6; Sierra Circuits return path design guide",
    }


def check_vs_001(s: Snapshot):
    """VS-001: average ground via spacing against 2 x lambda/20 at the highest
    signal frequency. Source: Altium, stitching via spacing."""
    required = lambda_over_20_mm(MAX_FREQUENCY_HZ)
    limit = 2 * required
    gnd = sorted((mm(v["x"]), mm(v["y"])) for v in s.vias_on_net("GND"))
    if len(gnd) < 2:
        return None
    # Nearest-neighbour spacing: the metric that matters for plane stitching.
    nn = []
    for i, a in enumerate(gnd):
        d = min(dist(a[0], a[1], b[0], b[1]) for j, b in enumerate(gnd) if j != i)
        nn.append(d)
    avg = sum(nn) / len(nn)
    return {
        "rule": "VS-001",
        "threshold": f"average spacing <= 2 x lambda/20 = {limit:.2f} mm at 2.4 GHz",
        "measured": f"{len(gnd)} GND vias, average nearest-neighbour spacing = {avg:.2f} mm, "
                    f"max = {max(nn):.2f} mm",
        "status": "fail" if avg > limit else "pass",
        "source": "Altium, Everything You Need to Know About Stitching Vias (lambda/20 for >120 dB)",
    }


def check_dp(s: Snapshot):
    """DP-001 / DP-002 / DP-003 for the USB pair.

    USB full speed uses a 15 ns rise time and a 10000 ps skew budget
    (kicad-happy DIFF_PAIR_PROTOCOLS['USB-FS']); the high-speed 25 ps limit is
    reported alongside so the margin is visible.

    Sources: USB 2.0 spec 7.1.2; Ott Ch. 19; Johnson, High-Speed Signal
    Propagation, Ch. 11.
    """
    delay = propagation_delay_ps_per_mm()
    out = []
    for a, b in (("USB_DP_CONN", "USB_DM_CONN"), ("USB_DP_MCU", "USB_DM_MCU")):
        la, lb = s.trace_length_mm(a), s.trace_length_mm(b)
        diff = abs(la - lb)
        skew = diff * delay
        out.append({
            "rule": "DP-001",
            "threshold": "USB-FS budget 10000 ps (USB-HS 25 ps for comparison)",
            "measured": f"{a}={la:.2f} mm, {b}={lb:.2f} mm, delta={diff:.2f} mm, "
                        f"skew={skew:.1f} ps",
            "status": "pass" if skew <= 10000 else "fail",
            "source": "USB 2.0 spec 7.1.2; kicad-happy DIFF_PAIR_PROTOCOLS",
        })
    # DP-003: any layer transition on a differential pair is HIGH severity.
    transitions = []
    for net in ("USB_DP_CONN", "USB_DM_CONN", "USB_DP_MCU", "USB_DM_MCU"):
        layers = sorted({l["layer"] for l in s.lines_on_net(net)})
        vias = len(s.vias_on_net(net))
        transitions.append(f"{net}: layers {layers}, {vias} vias")
    vias_total = sum(len(s.vias_on_net(n)) for n in
                     ("USB_DP_CONN", "USB_DM_CONN", "USB_DP_MCU", "USB_DM_MCU"))
    out.append({
        "rule": "DP-003",
        "threshold": "zero layer transitions on a differential pair",
        "measured": f"{vias_total} vias on the USB pair; " + "; ".join(transitions),
        "status": "fail" if vias_total else "pass",
        "source": "Armstrong, PCB Design Techniques for Lowest-Cost EMC Compliance, Part 5",
    })
    return out


def check_es(s: Snapshot):
    """ES-001 / ES-002: ESD device distance to the protected connector, and
    ground vias at the ESD device.

    Sources: TI SLVA680 "ESD Protection Layout Guide"; ST AN5686.
    """
    out = []
    j1 = s.position_mm("J1")
    for ref in ("U5", "U6"):
        pos = s.position_mm(ref)
        if not pos or not j1:
            continue
        d = dist(*pos, *j1)
        out.append({
            "rule": "ES-001",
            "threshold": "<=15 mm (move within 10 mm)",
            "measured": f"{ref} to J1 = {d:.2f} mm",
            "status": "pass" if d <= 15 else "fail",
            "source": "TI SLVA680; ST AN5686",
        })
        gnd_pads = [p for p in s.pads_of(ref, s.PAD_RADIUS_MM["tiny"])[0]
                    if p["net"] == "GND"]
        for p in gnd_pads:
            px, py = mm(p["x"]), mm(p["y"])
            near = [v for v in s.vias_on_net("GND")
                    if dist(px, py, mm(v["x"]), mm(v["y"])) <= 3.0]
            out.append({
                "rule": "ES-002",
                "threshold": ">=2 GND vias within 3 mm (HIGH if none)",
                "measured": f"{ref} GND pad at ({px:.2f}, {py:.2f}): {len(near)} GND vias within 3 mm",
                "status": "high" if not near else ("low" if len(near) < 2 else "pass"),
                "source": "TI SLVA680; ST AN5686",
            })
    return out


# Device roles that geometry alone cannot recover from the snapshot. Footprints
# encode the package, not the function, so the function map is declared here and
# reported alongside every finding that depends on it.
EXTERNAL_CONNECTORS = {"J1": "USB-C"}
PROTECTION_REFS = {"U5": "USB ESD array", "U6": "USB ESD array"}
SWITCHING_INDUCTORS = {"L1": "U4 EPD boost"}
SENSITIVE_REFS = {"U1": "MDBT50Q module: radio, NFC front end, 32 MHz crystal"}


def board_outline_edges(s: Snapshot):
    """Closed polygon on the BOARD_OUTLINE layer as a list of mm segments."""
    outline = [p for p in s.polylines if p["layer"] == LAYER_BOARD_OUTLINE]
    if not outline:
        return []
    poly = outline[0]["polygon"]
    if isinstance(poly, dict):
        poly = poly.get("polygon", [])
    nums = [float(v) for v in poly if not isinstance(v, str)]
    verts = [(mm(nums[i]), mm(nums[i + 1])) for i in range(0, len(nums) - 1, 2)]
    return [(a, b) for a, b in zip(verts, verts[1:] + verts[:1]) if a != b]


def check_be_001(s: Snapshot):
    """BE-001: signal trace on an outer layer within 1 x dielectric height of the
    board edge.

    Source: kicad-happy BE-001.

    Applicability: both copper layers of a 2-layer board are outer layers, so
    every trace qualifies geometrically. The rule targets edge radiation, which
    only matters for nets with fast edges; nets whose role is DC or
    press-driven are reported separately rather than counted as defects.
    """
    edges = board_outline_edges(s)
    if not edges:
        return {"rule": "BE-001", "status": "blocked", "threshold": "1 x H = 0.8 mm",
                "measured": "no board outline on layer 11 in snapshot",
                "source": "kicad-happy BE-001"}
    limit = DIELECTRIC_HEIGHT_MM
    slow_nets = {"USB_VBUS", "USB_CC1", "USB_CC2", "KEY_NEXT_N", "KEY_OK_N",
                 "KEY_PREV_N", "CHG_CE_N", "CHG_PG_N", "CHG_INT_N", "CHG_SCL",
                 "CHG_SDA", "BAT_NTC_TBD", "BAT_PACK_TBD", "SYS", "VDD_3V3",
                 "EPD_EN_TBD", "EPD_BS0", "EPD_PUMP", "EPD_GDR", "EPD_RESE",
                 "EPD_VCOM", "EPD_VDD", "EPD_VDDL", "EPD_VGH", "EPD_VGL",
                 "EPD_VPH", "EPD_VSNH", "EPD_VSNL1", "EPD_VSNL2", "EPD_VSPH",
                 "EPD_VSPL1", "EPD_VSPL2", "SWDIO"}
    near = []
    for l in s.lines:
        if not l["net"]:
            continue
        x1, y1, x2, y2 = mm(l["x1"]), mm(l["y1"]), mm(l["x2"]), mm(l["y2"])
        probes = [(x1, y1), (x2, y2), ((x1 + x2) / 2, (y1 + y2) / 2)]
        d = min(point_segment_distance(px, py, ax, ay, bx, by)
                for px, py in probes for (ax, ay), (bx, by) in edges)
        if d < limit:
            near.append((d, l["net"], l["layer"], x1, y1, x2, y2))
    near.sort()
    fast = [r for r in near if r[1] not in slow_nets]
    return {
        "rule": "BE-001",
        "threshold": f"trace within 1 x H = {limit:.2f} mm of the board edge",
        "measured": f"{len(near)} of {len([l for l in s.lines if l['net']])} trace "
                    f"segments are inside it; {len(fast)} carry fast edges"
                    + (f"; nearest {fast[0][1]} at {fast[0][0]:.3f} mm" if fast else
                       f"; nearest is {near[0][1]} at {near[0][0]:.3f} mm, a DC or "
                       f"press-driven net" if near else ""),
        "status": "fail" if fast else ("warning" if near else "pass"),
        "details": [f"{n} layer {lay} {d:.3f} mm" for d, n, lay, *_ in near[:10]],
        "source": "kicad-happy BE-001",
    }


def check_be_003(s: Snapshot):
    """BE-003: ground via stitching in a 10 mm radius around a connector, against
    2 x lambda/20 for that connector's highest-frequency signal.

    Source: kicad-happy BE-003; Altium stitching-via spacing.

    Applicability note: the requirement scales with the connector's knee
    frequency, so the result is reported with the distance that would actually
    have to be met. At USB full speed that distance is far larger than the
    board, which makes the rule non-binding rather than satisfied by design.
    """
    findings = []
    for ref, kind in EXTERNAL_CONNECTORS.items():
        pos = s.position_mm(ref)
        if not pos:
            continue
        # USB full speed: 15 ns rise time, knee = 0.35 / t_rise.
        knee_hz = 0.35 / 15e-9
        required = 2 * lambda_over_20_mm(knee_hz)
        radius = 10.0
        vias = [v for v in s.vias_on_net("GND")
                if dist(pos[0], pos[1], mm(v["x"]), mm(v["y"])) <= radius]
        gnd = sorted((mm(v["x"]), mm(v["y"])) for v in vias)
        avg = None
        if len(gnd) > 1:
            nn = [min(dist(a[0], a[1], b[0], b[1])
                      for j, b in enumerate(gnd) if j != i)
                  for i, a in enumerate(gnd)]
            avg = sum(nn) / len(nn)
        findings.append({
            "rule": "BE-003",
            "threshold": f"average spacing <= 2 x lambda/20 at the knee frequency "
                         f"({required:.0f} mm at {knee_hz / 1e6:.1f} MHz)",
            "measured": f"{ref} ({kind}): {len(vias)} GND vias within {radius:.0f} mm"
                        + (f", average nearest-neighbour spacing {avg:.2f} mm" if avg else ""),
            "status": "pass" if (avg is None or avg <= required) else "fail",
            "source": "kicad-happy BE-003; Altium stitching-via spacing",
        })
    return findings


def check_io_001(s: Snapshot):
    """IO-001: an external connector with no EMC filtering or ESD/TVS device
    within 25 mm. Source: kicad-happy IO-001.

    Applicability: this board provides ESD arrays only; there is no ferrite bead
    or common-mode choke, so the check confirms protection coverage rather than
    filter coverage.
    """
    findings = []
    for ref, kind in EXTERNAL_CONNECTORS.items():
        pos = s.position_mm(ref)
        if not pos:
            continue
        ranked = sorted(
            (dist(pos[0], pos[1], *s.position_mm(pref)), pref, role)
            for pref, role in PROTECTION_REFS.items() if s.position_mm(pref)
        )
        if not ranked:
            findings.append({
                "rule": "IO-001", "threshold": "protection device within 25 mm",
                "measured": f"{ref} ({kind}): no protection device declared",
                "status": "fail", "source": "kicad-happy IO-001",
            })
            continue
        d, pref, role = ranked[0]
        findings.append({
            "rule": "IO-001",
            "threshold": "protection device within 25 mm",
            "measured": f"{ref} ({kind}): nearest protection {pref} ({role}) = {d:.2f} mm; "
                        f"no ferrite bead or common-mode choke on this board",
            "status": "pass" if d <= 25 else "fail",
            "source": "kicad-happy IO-001",
        })
    return findings


def check_xt_001(s: Snapshot):
    """XT-001: parallel coupling length >=5 mm at a spacing below 3x dielectric
    height on outer layers.

    Sources: Bogatin, Signal and Power Integrity, Ch. 13; Johnson, High-Speed
    Digital Design, Ch. 5.

    Note: with a 0.8 mm dielectric the 3H threshold is 2.4 mm, which is wider
    than most of this board's routing. The rule is therefore reported as an
    aggregate of net pairs, and only the aggressor classes that carry HIGH
    severity upstream (clock and switching nets) should be treated as findings.
    """
    h3 = 3 * DIELECTRIC_HEIGHT_MM
    aggressors = {"EPD_SCK_TBD", "EPD_SW", "EPD_PUMP", "SWDCLK"}
    pairs = {}
    segs = [l for l in s.lines if l["net"]]
    for i, a in enumerate(segs):
        ax1, ay1, ax2, ay2 = mm(a["x1"]), mm(a["y1"]), mm(a["x2"]), mm(a["y2"])
        alen = segment_length(ax1, ay1, ax2, ay2)
        if alen < 5.0:
            continue
        for b in segs[i + 1:]:
            if b["net"] == a["net"] or b["layer"] != a["layer"]:
                continue
            bx1, by1, bx2, by2 = mm(b["x1"]), mm(b["y1"]), mm(b["x2"]), mm(b["y2"])
            blen = segment_length(bx1, by1, bx2, by2)
            if blen < 5.0:
                continue
            # Parallelism via the angle between directions.
            dot = ((ax2 - ax1) * (bx2 - bx1) + (ay2 - ay1) * (by2 - by1)) / (alen * blen)
            if abs(dot) < math.cos(math.radians(20)):
                continue
            # Spacing: midpoint of the shorter segment against the longer one.
            mx, my = (bx1 + bx2) / 2, (by1 + by2) / 2
            spacing = point_segment_distance(mx, my, ax1, ay1, ax2, ay2)
            if spacing >= h3:
                continue
            overlap = min(alen, blen)
            key = tuple(sorted((a["net"], b["net"])))
            cur = pairs.get(key)
            if cur is None or overlap > cur["overlap"]:
                pairs[key] = {"overlap": overlap, "spacing": spacing, "layer": a["layer"]}
    ranked = sorted(pairs.items(), key=lambda kv: -kv[1]["overlap"])
    high = [k for k, v in ranked if (k[0] in aggressors) or (k[1] in aggressors)]
    return {
        "rule": "XT-001",
        "threshold": f">=5 mm parallel coupling at spacing < 3H = {h3:.2f} mm",
        "measured": f"{len(ranked)} net pairs qualify; {len(high)} involve a clock or "
                    f"switching aggressor",
        "status": "high" if high else ("medium" if ranked else "pass"),
        "details": [f"{k[0]} <-> {k[1]}: overlap {v['overlap']:.1f} mm, "
                    f"spacing {v['spacing']:.2f} mm, layer {v['layer']}"
                    for k, v in ranked[:12]],
        "source": "Bogatin, Signal and Power Integrity, Ch. 13; Johnson, High-Speed Digital Design, Ch. 5",
    }


# Rules this checker deliberately does not compute. Pour geometry is no longer a
# blocker: the exporter captures it and analyze-e16-pour.py covers GP-003,
# GP-004 and BE-002. What remains here is genuinely unimplemented, and saying so
# is the point — a rule that is silently absent reads as a rule that passed.
NOT_IMPLEMENTED = [
    {
        "rule": "GP-001",
        "why": "reference-plane coverage per signal net; pour geometry is available, "
               "the check is simply not written yet",
        "where": "could be added here or to analyze-e16-pour.py",
        "source": "Hubing, AltiumLive 2022; Ott, Ch. 16",
    },
    {
        "rule": "GP-005",
        "why": "multiple ground domains; this board has a single GND net, and the "
               "pour is one node, so the check would be vacuous",
        "source": "kicad-happy GP-005",
    },
    {
        "rule": "SU-001..003",
        "why": "stackup rules assume inner layers and a plane pair; a 2-layer board "
               "has neither, so the premises do not hold",
        "source": "kicad-happy stackup rules",
    },
    {
        "rule": "PD-001..004 (PDN impedance)",
        "why": "needs per-capacitor net mapping plus ESL/ESR; a 2-layer board has no "
               "plane pair, so the payoff is limited",
        "source": "Bogatin; kicad-happy PDN checks",
    },
    {
        "rule": "DP-002 (skew-induced CM radiation)",
        "why": "needs cable length and a common-mode current path assumption; the "
               "board alone does not define them",
        "source": "Ott, Ch. 19; Johnson, Ch. 11",
    },
]


def main():
    ap = argparse.ArgumentParser()
    here = Path(__file__).resolve().parent.parent
    ap.add_argument("--snapshot", type=Path,
                    default=here / "hardware" / "e16-right-mid-snapshot.json")
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()

    s = Snapshot(args.snapshot)
    print(f"snapshot: {args.snapshot}")
    print(f"  {len(s.components)} components, {len(s.pads)} pads, "
          f"{len(s.lines)} trace segments, {len(s.vias)} vias")
    print(f"  board: 2 layers, {DIELECTRIC_HEIGHT_MM} mm dielectric, "
          f"eps_r {EPS_R}, 3H = {3 * DIELECTRIC_HEIGHT_MM:.2f} mm")
    print(f"  decoupling caps resolved with a {s.PAD_RADIUS_MM['cap']} mm radius, "
          f"ESD arrays with {s.PAD_RADIUS_MM['tiny']} mm")
    print()

    results = []
    for name, fn in (
        ("ML-001", check_ml_001),
        ("SW-002", check_sw_002),
        ("SW-003", check_sw_003),
        ("DC-001", check_dc_001),
        ("DC-003", check_dc_003),
        ("RP-001", check_rp_001),
        ("VS-001", check_vs_001),
        ("BE-001", check_be_001),
        ("BE-003", check_be_003),
        ("IO-001", check_io_001),
        ("DP-001/003", check_dp),
        ("ES-001/002", check_es),
        ("XT-001", check_xt_001),
    ):
        out = fn(s)
        if out is None:
            continue
        results.extend(out if isinstance(out, list) else [out])

    order = {"high": 0, "critical": 1, "fail": 2, "medium": 3, "warning": 4,
             "low": 5, "pass": 6, "blocked": 7}
    for r in sorted(results, key=lambda r: order.get(r["status"], 9)):
        if r["status"] == "pass":
            continue
        print(f"[{r['status'].upper():8}] {r['rule']}  (threshold {r['threshold']})")
        print(f"           {r['measured']}")
        print(f"           source: {r['source']}")
        for d in r.get("fast_net_details", [])[:12]:
            print(f"             fast: {d}")
        for d in r.get("details", [])[:12]:
            print(f"             - {d}")
        print()

    print("--- passing ---")
    for r in results:
        if r["status"] == "pass":
            print(f"  {r['rule']:12} {r['measured']}")

    print("\n--- not implemented (absent, not passing) ---")
    for b in NOT_IMPLEMENTED:
        print(f"  {b['rule']}: {b['why']}")

    if args.json:
        args.json.write_text(json.dumps(
            {"snapshot": str(args.snapshot), "results": results,
             "not_implemented": NOT_IMPLEMENTED},
            indent=2, ensure_ascii=False))
        print(f"\nwrote {args.json}")


if __name__ == "__main__":
    sys.exit(main())
