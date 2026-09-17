# TorQ — Simple Shopping List (all Amazon)

Same parts as `SHOPPING-SIMPLE.md`, every one from Amazon. Prices checked **2026-09-15**, before filament and tax.
Paper clips and the USB camera you already have.

| Buy | Part | $ |
|---|---|--:|
| 1 box | [M3 bolt kit, 810 pc](https://www.amazon.com/dp/B0GG8MGH1H) | 9.99 |
| 1 pack | [32mm eye lenses, 5 pc (need 2)](https://www.amazon.com/dp/B0DFHQBRS4) | 5.69 |
| 1 pack | [MG90S servos, 10-pack (need 7)](https://www.amazon.com/dp/B0DFXY714F) | 26.99 |
| 2 | [12V 100 RPM 37mm geared motor, off-centre shaft](https://www.amazon.com/dp/B0721T1PXQ) | 29.98 |
| 1 | [ELEGOO UNO R3](https://www.amazon.com/dp/B01EWOE0UU) | 16.99 |
| 1 | [Arduino Motor Shield Rev3 (genuine)](https://www.amazon.com/dp/B0084ZQF3O) | 28.40 |
| 1 | [PCA9685 servo driver](https://www.amazon.com/dp/B01D1D0CX2) | 8.99 |
| 1 | [PiiKit Raspberry Pi 5 4GB kit — Pi, Active Cooler, official 32GB SD, 27W PSU](https://www.amazon.com/dp/B0GK9HYS21) | 174.90 |
| 1 | [12V→5V 5A USB-C buck converter (Pi)](https://www.amazon.com/dp/B0CRVW7N2J) | 8.99 |
| 1 pack | [XL4015 5A adjustable buck converter, 3-pack (servos)](https://www.amazon.com/dp/B00LOG4XC0) | 9.49 |
| 1 pack | [CNHL 2200mAh 3S 30C LiPo, XT60, 2-pack](https://www.amazon.com/dp/B08KD1YN9F) | 32.99 |
| 1 | [SUPULSE B3 2S–3S LiPo balance charger](https://www.amazon.com/dp/B0936KKWXP) | 12.47 |
| 5 pairs | [Amass XT60H connectors](https://www.amazon.com/dp/B07PZ15Z2D) | 8.99 |
| 1 | [HONKYOB USB mini speaker](https://www.amazon.com/dp/B075M7FHM1) | 13.99 |
| 1 pack | [1.3in I²C OLED, 2-pack](https://www.amazon.com/dp/B0F1LLM9MP) | 9.88 |
| 1 kit | [1% resistor kit, 30 values (has 100kΩ + 47kΩ)](https://www.amazon.com/dp/B099W6BTCX) | 5.00 |
| 1 | [Waveshare 5in DSI touchscreen (belly)](https://www.amazon.com/dp/B0GL125N9S) | 50.99 |
| 1 | [Waveshare Pi 5 DSI cable, 22→15-pin, 300mm](https://www.amazon.com/dp/B0CX1V3QW3) | 7.67 |
| | **Total** | **462.39** |

## Add everything to your cart in one click

[**Add all 18 items to Amazon cart**](https://www.amazon.com/gp/aws/cart/add.html?ASIN.1=B0GG8MGH1H&Quantity.1=1&ASIN.2=B0DFHQBRS4&Quantity.2=1&ASIN.3=B0DFXY714F&Quantity.3=1&ASIN.4=B0721T1PXQ&Quantity.4=2&ASIN.5=B01EWOE0UU&Quantity.5=1&ASIN.6=B0084ZQF3O&Quantity.6=1&ASIN.7=B01D1D0CX2&Quantity.7=1&ASIN.8=B0GK9HYS21&Quantity.8=1&ASIN.9=B0CRVW7N2J&Quantity.9=1&ASIN.10=B00LOG4XC0&Quantity.10=1&ASIN.11=B08KD1YN9F&Quantity.11=1&ASIN.12=B0936KKWXP&Quantity.12=1&ASIN.13=B07PZ15Z2D&Quantity.13=1&ASIN.14=B075M7FHM1&Quantity.14=1&ASIN.15=B0F1LLM9MP&Quantity.15=1&ASIN.16=B099W6BTCX&Quantity.16=1&ASIN.17=B0GL125N9S&Quantity.17=1&ASIN.18=B0CX1V3QW3&Quantity.18=1) — Amazon shows a confirmation page; press **Continue** / **Add to Cart**. Motors are pre-set to quantity 2.

## Notes

- **Nothing on this list needs another store.**
- **Costs $32.78 more than the mixed-store list ($429.61).** Almost all of that is the Pi: Amazon only sells the bare Pi 5 4GB through a $159 third-party seller, so the kit is the better buy. It adds a 27W power supply for bench testing.
- **If the PiiKit sells out** (10 left): [iRasptek Pi 5 4GB + Active Cooler kit](https://www.amazon.com/dp/B0D4TH2BS1), $151.99, plus a [SanDisk 32GB card](https://www.amazon.com/dp/B073JWXGNT), $24.80.
- **Low stock:** the DSI cable (4 left).
- **The B3 charger charges through the balance lead** at 800mA, so about 3 hours per pack.
- **Set the XL4015 to 5.0–6.0V with a multimeter before connecting servos.**
- **Measure the belly opening** against [Waveshare's outline drawing](https://www.waveshare.com/5inch-dsi-lcd-d.htm).
- **Add `usb_max_current_enable=1` to `config.txt`.**
