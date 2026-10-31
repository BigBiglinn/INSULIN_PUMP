"""Cycle-by-cycle start-up model of the LM51551 flyback with hiccup logic. Bench-only prototype.

NOT a vendor model. Purpose: test whether a soft-start capacitor charges the 48 V output without
tripping the 64-cycle hiccup timer. Datasheet values (TI SNVSB75E): ISS 9-11 uA, VREF 1 V, VCLTH
93-107 mV, Gm 2 mA/V, GCOMP 0.142, COMP clamp 2.5-2.8 V, hiccup 64 limit cycles, reset after 8 clean
cycles, off time 32768 cycles, DMAX1 80-90 %. Assumed: lossless switching, COMP offset 0.2 V, and the
fixed slope compensation neglected (optimistic for regulation, conservative for current limit: the
limit is applied directly to the sensed current).
"""
import itertools

FSW = 298e3
L = 7.29e-6
N = 5.0
VF = 0.9
RS = 0.022
R_COMP, C_COMP, C_HF = 3.01e3, 180e-9, 3.3e-9
R_TOP, R_BOT = 470e3, 10e3
GM = 2e-3
GCOMP = 0.142


def run(vin, c_out, css, vclth, iss, dmax, iload_fn, r_bleed, tmax=0.6):
    t, il, vo = 0.0, 0.0, 0.0
    vss, vcomp, vrc = 0.0, 0.0, 0.0
    T = 1 / FSW
    limit = vclth / RS
    fault, clean, hiccups = 0, 0, 0
    ipk_max = 0.0
    off_left = 0
    while t < tmax:
        if off_left > 0:
            off_left -= 1
            vss = 0.0
            vcomp = 0.0
            vrc = 0.0
            il = max(0.0, il - (vo + VF) / (N * L) * T)
            vo = max(0.0, vo - (iload_fn(vo) + vo / r_bleed) * T / c_out)
            t += T
            continue
        vss = min(1.0, vss + iss * T / css)
        vfb = vo * R_BOT / (R_TOP + R_BOT)
        ieq = GM * (min(vss, 1.0) - vfb)
        ieq = max(-180e-6, min(180e-6, ieq))
        i_r = (vcomp - vrc) / R_COMP
        vrc += i_r * T / C_COMP
        vcomp = max(0.0, min(2.5, vcomp + (ieq - i_r) * T / C_HF))
        ipk_cmd = max(0.0, (vcomp - 0.2) * GCOMP / RS)
        # on-time: ramp until command, limit or DMAX
        ton_max = dmax * T
        ipk_try = il + vin / L * ton_max
        hit_limit = False
        if ipk_cmd <= il:
            ton, ip = 0.0, il
        else:
            ip = min(ipk_try, ipk_cmd)
            if ip >= limit:
                ip, hit_limit = limit, True
            ton = (ip - il) / (vin / L)
        ipk_max = max(ipk_max, ip)
        toff = T - ton
        slope = (vo + VF) / (N * L)   # primary-referred demagnetisation
        tdem = min(toff, ip / slope if slope > 0 else toff)
        il_end = ip - slope * tdem
        q_sec = (ip + il_end) / 2 / N * tdem
        vo += (q_sec - (iload_fn(vo) + vo / r_bleed) * T) / c_out
        vo = max(vo, 0.0)
        il = max(0.0, il_end)
        t += T
        if hit_limit:
            fault += 1
            clean = 0
        else:
            clean += 1
            if clean >= 8:
                fault = 0
        if fault >= 64:
            hiccups += 1
            fault, clean = 0, 0
            off_left = 32768
        if vo >= 47.5 and off_left == 0 and vss >= 1.0:
            return dict(ok=True, t=t, hiccups=hiccups, ipk=ipk_max)
    return dict(ok=False, t=t, hiccups=hiccups, vo=vo, ipk=ipk_max)


idle = lambda v: 0.006 if v > 20 else 0.0     # PMD401 "roughly 6 mA" at 48 V (manual 150025-01)
nominal_c = 47e-6 + 100e-6 + 2 * 1.3e-6
hi_c = 1.2 * (47e-6 + 100e-6) + 4.4e-6

print("vin  Cout_uF  Css     VCLTH  ISS   result")
for css in (47e-9, 220e-9, 470e-9, 1e-6):
    for vin, c, vcl, iss in itertools.product((3.0, 4.2), (nominal_c, hi_c), (0.093, 0.107), (9e-6, 11e-6)):
        if vcl == 0.107 and vin == 3.0 and iss == 9e-6:
            continue
        if vcl == 0.093 or vin == 4.2:
            r = run(vin, c, css, vcl, iss, 0.85, idle, 10e3)
            if r["ok"]:
                msg = "OK    t=%6.1f ms  hiccups=%d  Ipk=%.2f A" % (r["t"] * 1e3, r["hiccups"], r["ipk"])
            else:
                msg = "FAIL  Vo=%5.1f V after %.0f ms hiccups=%d" % (r["vo"], r["t"] * 1e3, r["hiccups"])
            print("%.1f  %6.1f  %4.0f nF  %.0f mV  %2.0f uA  %s" % (vin, c * 1e6, css * 1e9, vcl * 1e3, iss * 1e6, msg))
print("\nWorst case with PMD401 drawing full 100 mA during start (should be avoided by firmware; AEN parked):")
full = lambda v: 0.1 if v > 20 else 0.0
for vin, css in ((3.0, 1e-6), (3.4, 1e-6), (4.2, 1e-6)):
    r = run(vin, hi_c, css, 0.093, 9e-6, 0.85, full, 10e3)
    print(vin, css, r)
