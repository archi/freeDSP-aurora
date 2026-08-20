# FORK WARNING

**Careful: This branch/fork does experiment with adding SigmaStudio+ support to `sigma2aurora.py`. IT IS NOT TESTED!!**

My initial impression was that SS+ would be more efficient, but any space saving came from it converting PEQs with 10 banks to singular/single-banked PEQs. D'oh!

Though it has it advantages:

1. Put delays into unused `PM` (Program Memory) to free up precious `DM` (Data Memory) for FIR filters
2. More fluent UI
3. Dark Mode for those late-night DSP-coding sessions

Importing seems straight-forward, but after importing via *Action* -> *Import SigmaStudio Projects* SS+ tells you what you need to check.
Takes this seriously to not mess things up!

What *I* had to do (your progam might vary):

1. Replace your PEQ banks (which are now singular PEQs) with graphical PEQs (which are actual PEQ banks)
2. Fix the output channels assignments:
  * `Output_1` takes `Ch0`, `Output_2` takes `Ch1` and so on
  * `Output_UAC1` takes `Ch8`, `Output_UAC2` takes `Ch9` and so on
3. Re-arrange my layouts because some of them became even more messed up
4. During my first import, it turned half a dozen 1 channel 1500 tap FIR Filters with a into 1500 channel 1 tap FIR Filters
  * Not a huge issue in itself, but the rendering became excrudingly slow on my fast machine.
  * For my next import, I reduced the filters to 10 taps in classic SigmaStudio, but the error didn't show up again
  
Export works similar to before. To get the correct file names, just select your `.ssprj`-file. Don't worry, it will not be overwritten ;-)

**Now to address the elephant in the room:** Yes, you can convert your export the usual way, just add the `--plus` flag.
However:

1. Use the new `--verbose` flag to check the numbers it reports; also compare them to your old, classic SigmaStudio export (still supported by `sigma2aurora.py`)
2. The output addresses for a few controls are vastly smaller than the addresses in the old export. This might be just a different memory layout with the new SS+ compiler, but it might also be a indicator that something is off.

I will eventually test this with a scope or trash speakers, but for now I have other priorities.

# HEED THE ABOVE WARNING

seriously, if you don't understand even half of what I wrote above: That's okay, but please don't kill your valuable speakers or brick a rare Aurora DSP board - stick to the original firmware instead.

# I DID NEITHER VERIFY NOR TEST THE RESULTS, yet

I will, but sadly there are now new Auroras, so this is quite niche and I'm mostly doing it for myself I guess.

Maybe I get around to test it September even August, but maybe it will be August 2030 ;-)

Feel free to open an issue if you find this useful or want to know the status. I'm more than happy to talk to fellow Aurora users :-)

# Some neat additions, maybe?

I also commited my DSP program with some slightly modifed JS inside the `dsp.html` to add altering the volume via the scroll wheel.
You can steal that to use with your `dsp.html`; it doesn't depend on any changes made in my fork.

I'm not 100% happy yet, but as a proof of concept it's imho pretty nice and I'm happy for pull-requests making this better.

# Shoutout to Auverdion!

Thanks again for the nice DSP. I hope you're doing well! :)

I think you were just ahead of the curve there.

# Original README:

Now to something... not so different:


![FreeDSP logo](https://github.com/freeDSP/WIKI-AND-GENERAL-TOPICS/raw/master/LOGOs/freeDSP/freeDSP%20LOGO/freeDSP_LOGO.png)

# freeDSP aurora

An open source and open hardware [freeDSP](https://freedsp.github.io) board based on ADAU1452 with 8 analog I/O, S/P-DIF I/O, ADAT I/O, USB Audio, WiFi, Bluetooth.

It supports various and convenient physical addons and multiple software plugins, and is controlled by web interface.


## Main features

* Analog Devices ADAU1452, 294.912 MHz, 32-bit SigmaDSP
	* 6144 SIMD instructions per sample @ 48kHz fs
	* 40kWords of data RAM
	* 800ms digital audio delay pool @ 48kHz fs
	* 8 stereo ASRCs with 139dB DNR
* XMOS XE216-512-TQ128 for multichannel bidirectional audio streaming
* ESP32 for WiFi or Bluetooth control
* AKM AK4458 32bit-DAC
* AKM AK5558 32bit-ADC
* Supporting sample rates between 44.1kHz and 192kHz
* 8 analog balanced input channels, +6dBu
* 8 analog balanced output channels, +6dBu
* S/P-DIF input and output
* ADAT input and output
* Wordclock input and output
* Support for display, rotary encoder, volume potentiometer, temperature sensor, PWM controlled fan, IR sensor
* One freeDSP expansion header
* USB Audio Class 2 Bidirectional streaming with 8 channels in and 8 channels out, full-duplex. Works with ASIO driver under Windows 10 and driverless under macOS and Linux.
* Realtime control software over WiFi or Bluetooth available under an open source license
* THD DAC: -103dB @ 1kHz, 0dBfs, fs=48kHz
* THD ADC: -101dB @ 1kHz, 0dBfs, fs=48kHz
* Latency: 1.125ms (talkthrough ADC->DSP->DAC)
* Board dimensions: 110mm x 110mm

MAIN COORDINATOR: [dspverden](https://github.com/dspverden)


## Contributing

**Please take care on which branch you're currently working!**

Branches:

- *master* - this branch always holds the latest released revision
- *develop* - this is the develop branch with new features. Please base your patches on this branch.

[Build instructions](BUILDING.md) | [Addons](ADDONS/README.md) | [User Documentation](DOCUMENTATION/)


## License
<a rel="license" href="http://creativecommons.org/licenses/by-sa/4.0/"><img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by-sa/4.0/88x31.png" /></a><br />This work is licensed under a <a rel="license" href="http://creativecommons.org/licenses/by-sa/4.0/">Creative Commons Attribution-ShareAlike 4.0 International License</a>.

## Related Projects
- [Generate Aurora Plugins from SigmaStudio Exports (Alternative to Aurora's python scripts)](https://github.com/archi/aurora-tool)
- [PCB with startup delay (I2C) mod with a DM 2.4" OLED](https://github.com/Ca-Wi/freeDSP-aurora-extension-i2c-mod-display)
- [PCB to expand the freeDSP aurora expansion port with 3V3 regulator](https://github.com/Ca-Wi/freeDSP-aurora-expansion-port-extender)

## Custom Plugins
- [7.1 Homecinema Plugin with Highpassfilter by pillepalle1234](https://github.com/pillepalle1234/FreeDSP-Aurora-7.1-Homecinema-Plugin-Highpass)

## Links

- [Buy Aurora board and addons](https://auverdion.de/)
- [freeDSP](https://freedsp.github.io)
- [Kickstarter campaign](https://www.kickstarter.com/projects/auverdion/freedsp-aurora-dsp)
- [DIYAudio forum (english)](https://www.diyaudio.com/forums/digital-line-level/334055-freedsp-aurora-dsp-8-os-usb-audio-dif-adat-bluetooth-wifi-contro.html)
- [DIYHifi forum (german, features)](https://www.diy-hifi-forum.eu/forum/showthread.php?18572-freeDSP-aurora-Der-Feature-Thread)
- [DIYHifi forum (german, specs)](https://www.diy-hifi-forum.eu/forum/showthread.php?15019-Verst%E4rkermodul-mit-DSP-600W-1-4Kan%E4le-low-budget-high-quality&p=249786&viewfull=1#post249786)
- [ADAU1452 at Analog Devices](https://www.analog.com/en/products/adau1452.html)
- [ESP32 at Espressif](https://www.espressif.com/en/products/socs/esp32/overview)
- [XMOS XE216-512-TQ128 datasheet](https://www.xmos.com/file/xe216-512-tq128-datasheet)
- [AKM 4458](https://www.akm.com/us/en/products/audio/audio-dac/ak4458vn/)
- [AKM 5558](https://www.akm.com/us/en/products/audio/audio-adc/ak5558vn/)
