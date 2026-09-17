# TorQ — Shopping List

Every part in `BOM.md` v4, priced against a live listing on **2026-09-15**, USD,
**before shipping and tax.** Each part name links to where to buy it. Prices move,
especially on Amazon, so re-check before you order.

## Totals

| | $ |
|---|--:|
| 1. Chassis and motion | 152.80 |
| 2. Compute, power and audio | 350.26 |
| 3. Screen and arms | 171.36 |
| 4. Light, sensing and input | 146.35 |
| 5. Body, wiring and filament | 129.93 |
| **Core — everything you need** | **950.70** |
| + Spares (§6) | 1,044.58 |
| + Camera Module 3 Wide + cable (magnifier) | 1,085.78 |
| + OBD-II dongle | 1,114.77 |
| + AI HAT+ | 1,184.77 |

**Shipping:** this list uses about 15 vendors. Expect **$60–120** in shipping on
top. Moving the small items to Amazon cuts that down.

### Why it's $951 and not $637

- **Pi 5 4GB is $110, not $60.** RAM shortages pushed the price up three times since December 2025.
- **The 5V and 6V buck converters are $64, not $18.** These are Pololu parts. A cheap buck on the Pi rail is the brownout risk `BOM.md` warns about, so don't cut this one.
- **The STS3215 servos cost $24 each, not $15–18,** and the 12V version is the one to buy.
- **Storage is $55, not $25.** Flash memory prices are up too.
- **Four things were missing from BOM.md** and have been added: the Pi Active Cooler, inline fuse holders, sensor cables and a crimper.

### Ways to save ~$120 if the group balks

| Swap | Saves |
|---|--:|
| Spares: buy generic 5A bucks instead of Pololu (keep Pololu on the live rails) | ~45 |
| Spare motor drivers: buy one instead of two | 15 |
| Skip the crimper if someone in the group has one | 21 |
| 256GB microSD instead of the USB flash drive | 12 |
| Skip the Harbor Freight work light (use one you own) | 25 |

## ⚠ Corrections to BOM.md found while pricing

1. **MAX17048 fuel gauge will not work.** It's a single-cell gauge; our pack is 3S. Replaced with an **INA260** voltage/current sensor. It reports voltage and current, and the software turns that into a charge percentage.
2. **Buy the 12V STS3215 (C047), not the 7.4V version, and run it straight off the pack.** The 7.4V version on the 6V rail loses torque. The 12V one is rated to 12.6V, which is exactly a full 3S pack. Never put a 4S pack on it. The 6V rail now only feeds the MG90S servos.
3. **The 5in DSI screen needs its own 5V wire.** It normally draws power through pogo pins from a Pi bolted to its back. Ours sits at the end of a 300mm ribbon, so run 5V to it separately. Check the Waveshare wiki pinout first.
4. **Feeding the Pi 5 from a buck, not USB-C PD, limits its USB ports to 600mA.** That will starve the flash drive. Set `usb_max_current_enable=1` in `config.txt`.
5. **Fuse the pack.** Put a 15A ATC fuse at pack +. The BMS protects the cells, not the wiring.
6. **The FE-URT-1 is replaced by the Waveshare Bus Servo Adapter (A)**, which does the same job for half the price.

## 1. Chassis and motion (chillibasket stock parts)

| Buy | Part | Vendor | $ | Notes |
|---|---|---|--:|---|
| 1 box | [M3 socket-head kit, 810 pc (covers all 14×10mm, 12×20mm, 2×6mm, 26 nuts)](https://www.amazon.com/dp/B0GG8MGH1H) | Amazon | 9.99 |  |
| 1 pack | [M3 nyloc nuts, 100 pc](https://www.amazon.com/dp/B07FRLRWD4) | Amazon | 8.99 | Also covers the elbow/wrist nyloc pivots (§2c) |
| 1 pack (need 2) | [JIATONG 32mm plano-convex glass lens, 5 pc](https://www.amazon.com/dp/B0DFHQBRS4) | Amazon | 5.69 | Short focal length, looks more domed than stock. Closer match: [eBay K9 32mm FL65](https://www.ebay.com/itm/376064604967), ~$6.49, unverified |
| 1 pack (need 5) | [MG90S metal-gear servo, 180°, 10-pack](https://www.amazon.com/dp/B0DFXY714F) | Amazon | 26.99 | Only 5 used now; the other 5 are your spares. Avoid the $9.99 8-pack, it's 360° continuous |
| 2 | [Greartisan 12V 120 RPM 37mm geared motor, eccentric shaft](https://www.amazon.com/dp/B071KFSVRN) | Amazon | 29.98 | His exact part: [Pololu #4745](https://www.pololu.com/product/4745), $77.90 for two |
| 1 | [ELEGOO UNO R3](https://www.amazon.com/dp/B01EWOE0UU) | Amazon | 16.99 | Genuine: [Arduino store](https://store-usa.arduino.cc/products/arduino-uno-rev3), $27.60 |
| 1 | [Arduino Motor Shield Rev3 (A000079), genuine](https://store-usa.arduino.cc/products/arduino-motor-shield-rev3) | Arduino Store USA | 28.40 | Genuine here because cheap L298P clones often use a different pinout |
| 1 | [HiLetgo PCA9685 16-ch servo driver](https://www.amazon.com/dp/B01D1D0CX2) | Amazon | 8.99 | Adafruit #815 is out of stock |
| 5 pairs | [Genuine Amass XT60, 5 male + 5 female](https://www.asiarcdepot.com/products/xt60-connectors) | Asia RC Depot | 6.90 |  |
| 1 pack | [1.3in I²C OLED, SH1106, 2-pack](https://www.amazon.com/dp/B0F1LLM9MP) | Amazon | 9.88 | Check VCC/GND pin order before wiring |

**Subtotal: $152.80**

## 2. Compute, power and audio

| Buy | Part | Vendor | $ | Notes |
|---|---|---|--:|---|
| 1 | [Raspberry Pi 5, 4GB](https://www.canakit.com/raspberry-pi-5-4gb.html) | CanaKit | 110.00 | Was $60. RAM shortage price, same at PiShop |
| 1 | [Raspberry Pi Active Cooler (SC1148) — **not in BOM.md**](https://www.pishop.us/product/raspberry-pi-active-cooler/) | PiShop.us | 10.95 | A Pi 5 running Chromium + video inside a closed body will throttle without it |
| 1 | [Raspberry Pi Flash Drive 256GB, USB 3.0](https://www.pishop.us/product/raspberry-pi-flash-drive-256gb/) | PiShop.us | 54.95 | Cheaper: [official 256GB A2 microSD](https://www.pishop.us/product/official-raspberry-pi-microsd-card-a2-v30-256gb-blank/), $42.95. Small USB SSDs are mostly gone |
| 1 | [Pololu D42V55F5, 12V→5V 6A](https://www.pololu.com/product/5571) | Pololu | 31.95 | Marked "Rationed" — order early |
| 1 | [Pololu D42V55F6, 12V→6V 5.5A (MG90S rail)](https://www.pololu.com/product/5573) | Pololu | 31.95 |  |
| 1 pack | [1000µF 25V electrolytic capacitor, 5-pack](https://protosupplies.com/product/capacitor-electrolytic-1000uf-25v/) | ProtoSupplies | 1.95 |  |
| 6 | [Molicel P28A 18650, 2800mAh, 35A](https://www.18650batterystore.com/products/molicel-p28a) | 18650BatteryStore | 35.94 | $5.99 sale price. Hazmat shipping may apply |
| 1 pack | [3S 25A balanced BMS, 2-pack](https://www.amazon.com/dp/B07JMY631D) | Amazon | 9.59 | Second board is a spare. Generic; the 25A rating is optimistic |
| 1 | [Bistook 3S2P solderless 18650 holder](https://www.amazon.com/dp/B0GFW2C5G1) | Amazon | 16.15 | Flat-top cells only. Threadlock the screw contacts; tracks vibrate |
| 1 | [TalentCell 12.6V 2A charger, UL](https://www.amazon.com/dp/B07P8DMSZ8) | Amazon | 14.99 |  |
| 1 pack | [Nilight 14AWG inline ATC fuse holders, 10-pack — **not in BOM.md**](https://www.nilight.com/products/nilight-10-pack-ni-fh01-inline-holder-14awg-wiring-harness-atc-ato-30amp-blade-automotive-fuse-holder-10-2-years-warranty) | Nilight | 10.99 | 15A at pack +. Fuses not included — you'll have ATC fuses already |
| 1 | [Adafruit INA260 voltage/current sensor — **replaces MAX17048**](https://www.adafruit.com/product/4226) | Adafruit | 9.95 | MAX17048 is 1S only; it cannot read a 3S pack |
| 1 | [Adafruit MAX98357A I²S amp](https://www.adafruit.com/product/3006) | Adafruit | 5.95 |  |
| 1 | [Adafruit 40mm 4Ω 5W speaker](https://www.adafruit.com/product/3968) | Adafruit | 4.95 | Give it a small sealed box for speech |

**Subtotal: $350.26**

## 3. Screen and arms

| Buy | Part | Vendor | $ | Notes |
|---|---|---|--:|---|
| 1 | [Waveshare 5inch DSI LCD (D), 720×1280 touch](https://www.amazon.com/dp/B0GL125N9S) | Amazon | 50.99 | Direct from [Waveshare](https://www.waveshare.com/5inch-dsi-lcd-d.htm), $55.99. Panel is 15-pin |
| 2 | [Pi 5 display cable, 22→15-pin, 300mm](https://www.adafruit.com/product/5822) | Adafruit | 4.00 | One is the spare |
| 1 kit | [M2.5 nylon standoff kit with washers, 435 pc](https://www.amazon.com/dp/B0B5M1M822) | Amazon | 12.99 |  |
| 3 | [Feetech STS3215 **12V** (C047, 30kg·cm)](https://www.seeedstudio.com/STS3215-30KG-Serial-Servo-p-6340.html) | Seeed Studio | 71.97 | 2 shoulders + 1 spare. **12V version, run straight off the pack** — not the 6V rail |
| 1 | [Waveshare Bus Servo Adapter (A)](https://www.waveshare.com/bus-servo-adapter-a.htm) | Waveshare | 4.99 | Replaces FE-URT-1 ($10). Takes 9–12.6V |
| 1m | [CST 4mm pultruded carbon tube (CS-508 1M), cut to 2×500mm](https://www.cstsales.com/Carbon_Fiber_Tubes.html) | CST | 8.49 | Category page — find CS-508 |
| 1 pack | [uxcell F623ZZ flanged bearing 3×10×4, 10 pc](https://www.amazon.com/dp/B07Z3CHXT5) | Amazon | 8.79 | For M3 pivots. If pivoting on the 4mm tube, get F684ZZ |
| 1 pack | [M4 stainless ball spring plunger, 20 pc](https://www.amazon.com/dp/B07WGGBS1L) | Amazon | 9.14 | Spring force not stated — test before printing the detent pockets |

**Subtotal: $171.36**

## 4. Light, sensing and input

| Buy | Part | Vendor | $ | Notes |
|---|---|---|--:|---|
| 1 pack | [60mm white COB halo ring, 12V, 2-pack](https://www.amazon.com/dp/B078SR4JRS) | Amazon | 10.44 | ~50mm ID clears the lens. 8000K (blue) — use for aim/fill; the Nichia is for colour |
| 1 | [Nichia 519AT 4500K 90+ CRI on 20mm star](https://mtnelectronics.com/index.php?product_id=1068&route=product%2Fproduct) | Mountain Electronics | 5.59 | Needs a heatsink — bolt to aluminium scrap |
| 1 | [Mean Well LDD-700L constant-current driver](https://www.trcelectronics.com/products/mean-well-ldd-700l) | TRC Electronics | 4.48 | Pi GPIO can drive its DIM pin directly |
| 2 | [Adafruit MOSFET driver (AO3406) #5648](https://www.adafruit.com/product/5648) | Adafruit | 7.90 | Works at 3.3V. Avoid IRF520 modules |
| 1 | [BRAUN 500lm rechargeable magnetic work light](https://www.harborfreight.com/500-lumen-led-rechargeable-magnetic-handheld-foldable-slim-bar-work-light-59536.html) | Harbor Freight | 24.99 |  |
| 1 | [Adafruit BNO085 IMU #4754](https://www.adafruit.com/product/4754) | Adafruit | 29.50 |  |
| 3 | [Adafruit VL53L1X ToF #3967](https://www.adafruit.com/product/3967) | Adafruit | 44.85 | All start at 0x29 — re-address via XSHUT at every boot |
| 5 | [STEMMA QT cable, 100mm — **not in BOM.md**](https://www.adafruit.com/product/4210) | Adafruit | 4.75 | Daisy-chains IMU + ToF |
| 1 | [STEMMA QT to female header cable](https://www.adafruit.com/product/4397) | Adafruit | 0.95 | Pi header → first sensor |
| 1 | [Adafruit SPH0645 I²S mic #3421](https://www.adafruit.com/product/3421) | Adafruit | 6.95 | 3.3V only. INMP441 [at Vetco](https://vetco.net/products/omnidirectional-microphone-module-inmp441-high-precision-i2s) $4.95, stock unverified |
| 1 | [Adafruit 60mm arcade button #1192](https://www.adafruit.com/product/1192) | Adafruit | 5.95 | Not sealed. Garage-proof upgrade in Optional |

**Subtotal: $146.35**

## 5. Body, wiring and filament

| Buy | Part | Vendor | $ | Notes |
|---|---|---|--:|---|
| 7 pairs | [K&J R822CS-P ½"×⅛" countersunk N42 ring magnet](https://www.kjmagnetics.com/r822cs-p-neodymium-countersunk-ring-magnet) | K&J Magnetics | 15.89 | 2 pairs chest dock + 5 pairs sweeper strip |
| 1 | [Pittsburgh 4" magnetic parts tray #90566](https://www.harborfreight.com/4-inch-magnetic-parts-tray-90566.html) | Harbor Freight | 2.99 |  |
| 1 pack | [StanceMagic ¼oz stick-on steel wheel weights, 48 pc (~340g)](https://www.amazon.com/StanceMagic-0-25oz-Adhesive-Weights-Profile/dp/B07PMG6CCZ) | Amazon | 7.89 | Rear counterweight; ~35 pcs = 250g |
| 1 kit | [HALJIA JST-XH 560 pc kit](https://www.haljia.com/products/haljia-560pcs-2-54mm-jst-xh-jst-connector-kit-2-54mm-pitch-female-pin-header-jst-xh-2-3-4-5pin-housing-jst-adapter-cable-connector-socket-male-and-female-assortment-kit) | HALJIA | 8.99 |  |
| 1 | [IWISS SN-28B ratchet crimper](https://www.icrimptools.com/products/iwiss-sn-28b-dupont-crimping-tool-for-3-96mm-2-54mm-2-5mm-pitch-dupont-jst-xh-vh-connectors-awg-18-to-28) | iCrimp | 20.99 | Skip if you own one. Doesn't do JST-PH |
| 1 kit | [BNTECHGO 22AWG silicone wire, 5×30ft](https://bntechgo.com/bntechgo-22-gauge-silicone-wire-kit-ultra-flexible-5-colors-each-30-ft-high-temp-200-c-600v-22-awg-silicone-wire-60-strands-of-tinned-copper-wire-stranded-wire/) | BNTECHGO | 16.73 |  |
| 1 | [BNTECHGO 18AWG silicone wire, red+black](https://www.amazon.com/BNTECHGO-Silicone-Flexible-Strands-Stranded/dp/B01AQOI36M) | Amazon | 9.48 | Power runs |
| 2kg | [ELEGOO PETG 1.75mm, 2×1kg](https://www.amazon.com/ELEGOO-Filament-Plastic-Spool-Black/dp/B0D86GR3T7) | Amazon | 23.98 | $12/kg |
| 1kg | [Overture TPU 95A 1.75mm](https://overture3d.com/products/overture-tpu) | Overture | 22.99 | Track pads. Dry before printing |

**Subtotal: $129.93**

## 6. Spares

The spare STS3215, spare DSI cable, spare BMS and 5 spare MG90S are already in the lines above.

| Buy | Part | Vendor | $ | Notes |
|---|---|---|--:|---|
| 2 | [KOOBOOK L298P Motor Shield R3 (Rev3 pinout)](https://www.amazon.com/dp/B07Y1J34P3) | Amazon | 29.98 | Listing's pinout drawing is wrong; board is Rev3 layout (D3/D12, D11/D13) |
| 1 | [Pololu D42V55F5 spare 5V buck](https://www.pololu.com/product/5571) | Pololu | 31.95 |  |
| 1 | [Pololu D42V55F6 spare 6V buck](https://www.pololu.com/product/5573) | Pololu | 31.95 |  |

**Subtotal: $93.88**

## 7. Optional

| Buy | Part | Vendor | $ | Notes |
|---|---|---|--:|---|
| 1 | [Raspberry Pi Camera Module 3 Wide](https://www.pishop.us/product/raspberry-pi-camera-module-3-wide/) | PiShop.us | 38.50 | Only for the magnifier |
| 1 | [Pi 5 camera cable 22→15-pin, 200mm](https://www.adafruit.com/product/5818) | Adafruit | 2.70 | **Required** with the camera — it ships with the wrong cable |
| 1 | [Vgate iCar Pro **BT3.0** OBD-II](https://www.vgatemall.com/products-detail/i-11/) | Vgate | 28.99 | Get BT3.0, not the BLE version. 1996+ cars |
| 1 | [Raspberry Pi AI HAT+ 13 TOPS (Hailo-8L)](https://www.canakit.com/raspberry-pi-ai-hat-13.html) | CanaKit | 70.00 | v2 vision |
| 1 | [Cole Hersee M-608-BP sealed rubber-cap switch](https://www.amazon.com/dp/B002JQ5PO4) | Amazon | 35.11 | Garage-proof push-to-talk, instead of the arcade button |
