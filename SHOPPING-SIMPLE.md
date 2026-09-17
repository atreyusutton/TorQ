# TorQ — Simple Shopping List

Chillibasket's parts, a Raspberry Pi 5, a belly touchscreen and its cable, plus the cooler and servo converter the Pi 5 needs.
Prices checked **2026-09-15**, USD, before filament, shipping and tax. Paper clips and the USB camera you already have.

| Buy | Part | Vendor | $ |
|---|---|---|--:|
| 1 box | [M3 bolt kit, 810 pc](https://www.amazon.com/dp/B0GG8MGH1H) | Amazon | 9.99 |
| 1 pack | [32mm eye lenses, 5 pc (need 2)](https://www.amazon.com/dp/B0DFHQBRS4) | Amazon | 5.69 |
| 1 pack | [MG90S servos, 10-pack (need 7)](https://www.amazon.com/dp/B0DFXY714F) | Amazon | 26.99 |
| 2 | [12V **100 RPM** 37mm geared motor, off-centre shaft](https://www.amazon.com/dp/B0721T1PXQ) | Amazon | 29.98 |
| 1 | [ELEGOO UNO R3](https://www.amazon.com/dp/B01EWOE0UU) | Amazon | 16.99 |
| 1 | [Arduino Motor Shield Rev3](https://store-usa.arduino.cc/products/arduino-motor-shield-rev3) | Arduino Store USA | 28.40 |
| 1 | [PCA9685 servo driver](https://www.amazon.com/dp/B01D1D0CX2) | Amazon | 8.99 |
| 1 | [Raspberry Pi 5, 4GB](https://www.canakit.com/raspberry-pi-5-4gb.html) | CanaKit | 110.00 |
| 1 | [Raspberry Pi Active Cooler](https://www.pishop.us/product/raspberry-pi-active-cooler/) | PiShop.us | 10.95 |
| 1 | [Raspberry Pi microSD, 32GB](https://www.pishop.us/product/raspberry-pi-sd-card-32gb/) | PiShop.us | 19.95 |
| 1 | [12V→5V 5A USB-C buck converter (Pi)](https://www.amazon.com/dp/B0CRVW7N2J) | Amazon | 8.99 |
| 1 pack | [XL4015 5A adjustable buck converter, 3-pack (servos)](https://www.amazon.com/dp/B00LOG4XC0) | Amazon | 9.49 |
| 1 pack | [2200mAh 3S 30C LiPo, XT60, 2-pack](https://www.amazon.com/CNHL-2200mAh-Battery-Airplane-Quadcopter/dp/B08KD1YN9F) | Amazon | 32.99 |
| 1 | [SkyRC e3 LiPo balance charger](https://supergdrift.com/products/e3-lipo-ac-1-2a-11w-2-3s-balance-charger-sky-rc-sk-100081-08) | Super-G R/C | 17.99 |
| 5 pairs | [XT60 connectors](https://www.asiarcdepot.com/products/xt60-connectors) | Asia RC Depot | 6.90 |
| 1 | [USB speaker](https://www.adafruit.com/product/3369) | Adafruit | 12.50 |
| 1 pack | [1.3in I²C OLED, 2-pack](https://www.amazon.com/dp/B0F1LLM9MP) | Amazon | 9.88 |
| 1 kit | [Resistor kit (has 100kΩ + 47kΩ)](https://www.sparkfun.com/resistor-kit-1-4w-500-total.html) | SparkFun | 9.95 |
| 1 | [Waveshare 5in DSI touchscreen (belly)](https://www.amazon.com/dp/B0GL125N9S) | Amazon | 50.99 |
| 1 | [Pi 5 display cable, 300mm](https://www.adafruit.com/product/5822) | Adafruit | 2.00 |
| | **Total** | | **429.61** |

## Before you order

- **Motors: 100 RPM.** It matches his exact part (Pololu #4745). You get more torque and finer control on the tracks than at 150.
- **Set the XL4015 to 5.0–6.0V with a multimeter before connecting servos.** They often ship set higher.
- **Measure the belly opening** against [Waveshare's outline drawing](https://www.waveshare.com/5inch-dsi-lcd-d.htm).
- **Screen power:** it gets 5V through pins when the Pi is screwed to its back. Otherwise run a 5V wire to it.
- **Add `usb_max_current_enable=1` to `config.txt`** so the speaker and camera get USB power.
- **About 1 hour per LiPo.** Store and charge them in a fire-safe bag.
