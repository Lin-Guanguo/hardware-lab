# E20D screen, FPC and aperture registration

Recorded 2026-09-23. **Drawing-derived placement candidate; final flex bending and printed fit remain unqualified.**

[Registration diagram](../enclosure/renders/e20d-screen-fpc-registration.png) / [calculated evidence](records/e20d-fpc-review.json) / [current PCB and CAD](pcb-e20d-front-rear.md).

## Measurement endpoints

The user supplied an unplugged screen/FPC caliper photograph reading 51.5 mm, then a plugged photograph reading 54.8 mm, described as approximately 55 mm and difficult to measure. The second photograph spans the far screen edge to the connector rear, rather than the free FPC tip. Caliper calibration and precise jaw contact are not established.

The GDEH0154E01 [official specification entry](https://www.good-display.com/companyfile/2038.html) links the [manufacturer PDF](https://v4.cecdn.yun300.cn/100001_1909185148/GDEH0154E01.pdf). Page 5 of the locally cached official PDF gives:

- Panel: **37.32 ±0.1 × 31.8 ±0.1 mm**; thickness **0.85 ±0.15 mm**.
- FPC projection beyond glass: **14.3 ±0.3 mm**.
- Tail width: **12.5 ±0.1 mm**; contact pitch 0.5 mm; exposed contact length **3.2 ±0.2 mm**.
- Reinforcing film length: **6 ±0.3 mm**; tail thickness **0.30 ±0.03 mm**.
- FPC-side transverse offset: **9.59 ±0.3 mm**.

The [XUNPU FPC-05FB drawing](https://www.lcsc.com/datasheet/C2856831.pdf), used by the official DESPI-E01 reference board, shows 4.90 mm body depth, 5.40 mm including the rear leads, and a 2.10 mm insertion dimension in its section view.

| Endpoint | Nominal calculation | User photograph |
| --- | --- | ---: |
| Far glass edge to free tail tip | 37.32 + 14.3 = **51.62 mm** | 51.5 mm |
| Far glass edge to inserted connector body rear | 51.62 − 2.10 + 4.90 = **54.42 mm** | Approximately 54.8 mm, rear endpoint uncertain |
| Far glass edge to inserted connector lead rear | 51.62 − 2.10 + 5.40 = **54.92 mm** | Same photograph |

The first difference is −0.12 mm, inside the arithmetic 51.22–52.02 mm drawing range. The second reading is consistent with a connector rear endpoint. This agreement does not determine the final bent FPC geometry.

The official download listing was checked during this review. Re-fetching the manufacturer's PDF CDN failed; the dimensions above were visually read from the previously downloaded official PDF, SHA-256 `a3aa45389653aff47ece0f5fce8edd99f07e2889d291b54547efef4c05ba2ebd`. Its identity against the official English/Chinese downloads had been verified on 2026-09-21. The user's drawing screenshot agrees with the same dimensions.

## Registration in the card

Use the screen face toward the viewer and CAD **+Y upward**. With the FPC extending right:

1. Glass stays at **X2.00–39.32 / Y18.30–50.10 mm**.
2. The 27 × 27 mm active area stays at **X4.40–31.40 / Y20.70–47.70 mm**.
3. The case window stays at **X4.00–31.80 / Y20.30–48.10 mm**, giving **0.40 mm nominal margin on each active-area edge**.
4. The FPC-side glass border is **7.92 mm**; the other three borders are 2.40 mm. Centring the window on the entire glass would be wrong along the long axis.
5. Tail centre Y = 18.30 + 31.80 − 9.59 − 12.50/2 = **34.26 mm**.
6. J2 moves from (51.53, 34.00) to **(54.70, 34.26) mm**. The screen and window do not move to accommodate the connector.

The native model's connector mouth is approximately X51.175 mm. With 2.10 mm nominal insertion, the tail tip is X53.275 mm; the 6 mm stiffener starts at X47.275 mm. The nominal pre-stiffener length is 8.30 mm and its plan projection is approximately 7.955 mm. About **0.345 mm** of tail length remains beyond the straight plan projection. This is an allowance for vertical accommodation, **not a proved bend shape**; the screen exit height, connector seating height, local bend radius and delivered tolerances are still open.

The previous connector position required about 3.5 mm more tail length to be taken up in the gap. Moving J2 reduces that excess without using the FPC to pull the screen away from the aperture datum. C14–C22 follow J2 by the same translation, preserving their served-pin distances.

## Pin orientation correction

A transient verbal warning about reversed pin order was caused by mixing a downward-positive review-image Y axis with the upward-positive CAD coordinate system. Rechecking the full manufacturer front view and the user's plugged photograph resolves it:

- With the screen FPC pointing right, screen pin 1 is at the smaller Y coordinate and pin 24 at the larger Y coordinate.
- Current J2 pin 1 is Y28.51 mm; pin 24 is Y40.01 mm, matching the 34.26 mm centre and 11.5 mm contact-centre span.
- J2 rotation remains −90°. **No footprint pin numbers, nets or schematic connections were reversed.**

The script checks the two end contacts against the drawing-derived positions. Netlist consistency separately checks all 238 component pins; it does not by itself establish physical FPC orientation.

## Assembly sequence and limits

Position the display's active area against the window datum using a registration fixture, bond the glass border, and retain the screen independently of the FPC. Insert the tail fully with the connector latch open, then close the latch and check that the screen remains seated without tension. Keep the 6 mm reinforcing segment straight. Adhesive compatibility, allowed bend radius and latch handling follow the delivered component instructions; the model does not qualify them.

The nominal window margin must cover actual print error and placement error together; the supplier's broad ±0.2 mm claim is not a feature-specific tolerance guarantee. Verify the assembled active-area centring and FPC bend before printing an order batch or routing is frozen. The current 5.8 mm case passes the recorded nominal solid checks, but those checks use a service volume rather than a measured folded flex.

Reproduce the drawing and pin checks after exporting current native pads and body bounds:

```sh
python3 projects/nfc-business-card/scripts/review-e20d-fpc.py
```
