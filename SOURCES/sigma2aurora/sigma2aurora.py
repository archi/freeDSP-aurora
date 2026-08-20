import xml.etree.ElementTree as ET
import json
import io
import argparse
import os
import struct
import shutil

try:
    to_unicode = unicode
except NameError:
    to_unicode = str


class GrowingList(list):
    def __setitem__(self, index, value):
        if index >= len(self):
            self.extend([None]*(index + 1 - len(self)))
        list.__setitem__(self, index, value)


class ParamHp:
    name = ""

    def __init__(self):
        self.addr = [-1, -1, -1, -1]


class ParamLp:
    name = ""

    def __init__(self):
        self.addr = [-1, -1, -1, -1]


class ParamShelv:
    name = ""
    addr = -1


class ParamPeq:
    name = ""
    addr = -1


class ParamPeqBank:
    name = ""

    def __init__(self):
        self.addr = [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1]


class ParamPhase:
    name = ""
    addr = -1


class ParamDelay:
    name = ""
    addr = -1


class ParamGain:
    name = ""
    addr = -1


class ParamFir:
    name = ""
    addr = -1
    len = 0


class ParamXO:
    hpname = ""
    lpname = ""

    def __init__(self):
        self.hpaddr = [-1, -1, -1, -1]
        self.lpaddr = [-1, -1, -1, -1]


parser = argparse.ArgumentParser()
parser.add_argument("input", help="SigmaStudio project file")
parser.add_argument("plugin", help="Name of plugin")
parser.add_argument("--gui", help="Path to html gui", type=str)
parser.add_argument("--version", help="Version of plugin", type=str)
parser.add_argument("--outputdir", help="Output directory", type=str)
parser.add_argument("--plus", help="Ingest SigmaStudio+ data", action='store_true')
parser.add_argument("--verbose", help="Print some debug output", action='store_true')

# Read arguments from the command line
args = parser.parse_args()

# Check arguments
if args.input:
    print("SigmaStudio project file: %s" % args.input)
    path_sigmastudioproject = args.input
if args.plugin:
    print("Name of plugin: %s" % args.plugin)
    nameplugin = args.plugin
if args.version:
    version = args.version
else:
    version = "0.0.0"
if args.outputdir:
    outputdir = args.outputdir
else:
    outputdir = ""
if args.plus:
    plus = args.plus
else:
    plus = False
if args.verbose:
    verbose = args.verbose
else:
    verbose = False

if plus:
    print("Parsing data for SigmaStudio+ (3.4.0)")
else:
    print("Parsing data for SigmaStudio Classic (4.7)")

projectname = os.path.splitext(os.path.basename(path_sigmastudioproject))[0]
projectdir = os.path.dirname(path_sigmastudioproject)

# --- filenames and some paths differ depending on SigmaStudio Edition ---
# Mind this is not the only switch on 'plus'!
if plus:
    scheme_prefix = projectname + "_ADAU145xSchematic_0"
    xml_prefix = projectname + "_ADAU1452_0"

    txbuffer_file = scheme_prefix + "_TxBuffer.dat"
    numbytes_file = scheme_prefix + "_NumBytes.dat"
    netlist_xml_file = xml_prefix + "_NetList.xml"
    projectxml_file = xml_prefix + ".xml"

else:
    txbuffer_file = "TxBuffer_IC_1.dat"
    numbytes_file = "NumBytes_IC_1.dat"
    netlist_xml_file = projectname + "_NetList.xml"
    projectxml_file = projectname + ".xml"


# --- Read TxBuffer file
txbuffer_path = os.path.join(projectdir, txbuffer_file)
print("Reading " + txbuffer_path)
if not os.path.exists(txbuffer_path):
    print("Could not find file "+txbuffer_file+" in project directory")
    exit()
txbuffer = bytearray()
with open(txbuffer_path) as fp:
    line = fp.readline()
    while line:
        strlst = line.split(",")
        for ii in range(0, len(strlst)):
            str_ = strlst[ii].strip()
            if str_.startswith('0x'):
                txbuffer += bytearray.fromhex(str_[2:])
        line = fp.readline()

# --- Read NumBytes file
numbytes_path = os.path.join(projectdir, numbytes_file)
print("Reading " + numbytes_path)
if not os.path.exists(numbytes_path):
    print("Could not find file "+numbytes_file+" in project directory")
    exit()
numbytes = []
with open(numbytes_path) as fp:
    line = fp.readline()
    while line:
        strlst = line.split(",")
        numbytes.append(int(strlst[0].strip()))
        line = fp.readline()

# --- Create output directory
try:
    if not os.path.exists(outputdir):
        os.mkdir(outputdir)
except OSError:
    print("Creation of output directory %s failed" % outputdir)

if outputdir:
    outputdir = outputdir + "/"

try:
    if not os.path.exists(outputdir + projectname):
        os.mkdir(outputdir + projectname)
except OSError:
    print("Creation of output directory %s failed" % projectname)


# --- Write dsp.fw
print("Writing DSP firmware")
dspfw_path = os.path.join(outputdir + projectname, 'dsp.fw')
with open(dspfw_path, 'wb') as file:
    idx = 0
    for ii in range(0, len(numbytes)):
        file.write(bytearray(struct.pack("!I", numbytes[ii])))
        for nn in range(0, numbytes[ii]):
            file.write(bytearray(struct.pack("!B", txbuffer[idx])))
            idx = idx + 1


spdifoutmux_channel = []
spdifoutmux_channel.append(GrowingList())
spdifoutmux_channel.append(GrowingList())
spdifoutmux_port = [0, 0]

lshelv = []
hshelv = []
peq = []
peqbank = []
peqband = []
hp = []
lp = []
phase = []
dly = []
gain = []
xohp = []
xolp = []
fir = []

# --- Reading project xml file
netlist_xml_path = os.path.join(projectdir, netlist_xml_file)
print("Reading netlist XML " + netlist_xml_path)
tree = ET.parse(netlist_xml_path)
root = tree.getroot()

# --- Count outputs
noutputs = 0
if plus:
    for algo in root.findall("Core/Schematic/Algorithm"):
        cell = algo.get("name")
        if cell.startswith("Output_") and not cell.startswith("Output_UAC"):
            noutputs = noutputs + 1
else:
    for algo in root.findall("IC/Schematic/Algorithm"):
        cell = algo.get("cell")
        if cell.startswith("Output "):
            noutputs = noutputs + 1

if verbose:
    print("Found " + str(noutputs) + " outputs")

# --- Reading project xml file
ninputs = 0
projectxml_path = os.path.join(projectdir, projectxml_file)
print("Reading project XML: " + projectxml_path)
tree = ET.parse(projectxml_path)
root = tree.getroot()

# --- helper to read an abstract parameter
def plus_abstract_parameter(module, qname):
    for aparam in module.findall("AbstractParameter"):
        name = aparam.find("Name")
        if name.text == qname:
            value = aparam.find("Value")
            return value.text

# --- Count inputs
if plus:
    for module in root.findall('Core/Schematic/Module/Algorithm'):
        cellname = module.find('AlgoName')

        # has a "NumChannels" parameter we can use
        if cellname.text.startswith('Nx11_Analog'):
            ninputs = int(plus_abstract_parameter(module, "NumChannels"))

else:
    for module in root.findall('IC/Module'):
        cellname = module.find('CellName')

        if cellname.text.startswith('InputSelect'):
            strlist = cellname.text.split('_', 2)
            if len(strlist) > 2:
                if "Analog" in strlist[2]:
                    ninputs = ninputs + 1

if verbose:
    print ("Found " + str(ninputs) + " inputs")

inputselect_analog = []
for ii in range(0, ninputs):
    inputselect_analog.append(GrowingList())

inputselect_spdif = []
for ii in range(0, ninputs):
    inputselect_spdif.append(GrowingList())

inputselect_uac2 = []
for ii in range(0, ninputs):
    inputselect_uac2.append(GrowingList())

inputselect_exp = []
for ii in range(0, ninputs):
    inputselect_exp.append(GrowingList())

inputselect_port = []
for ii in range(0, ninputs):
    inputselect_port.append(GrowingList())

npeqbank = 0

# for non-plus:
def intaddr(node):
    return int(node.find('Address').text)

# for plus:
def plus_intaddr(module, module_parameter_name):
    for modparam in module.findall("ModuleParameter"):
        name = modparam.find("Name")
        if name.text == module_parameter_name:
            return intaddr(modparam)

# In SS+ names are not prefixed with "Plugin.", but in classic they are (since that's the name of the schematic)
# I am not 100% sure it's the best way to just ignore schematics, but for now let's do that.
# The "Plugin." is later stripped (or rather ignored), but I don't want to change that during the first stage.
# Instead, I just add the "Plugin." prefix to SS+ names.
# This can later be swapped and to allow simplification of the later processing code :)
def normalize_name(name):
    if (plus):
        return "Plugin." + name
    return name

if plus:
    search_path = "Core/Schematic/Module/Algorithm"
    param_path = "ModuleParameter"
    cellname_block = "AlgoName"
else:
    search_path = "IC/Module"
    param_path = "Algorithm/ModuleParameter"
    cellname_block = "CellName"

counted_things = {}
def count(thing):
    if thing in counted_things.keys():
        counted_things[thing] += 1
    else:
        counted_things[thing] = 1

for module in root.findall(search_path):
    cellname = module.find(cellname_block)

    if cellname.text.startswith('InputSelect') or (plus and cellname.text.startswith("Nx11_")):
        count("InputSelect")

        # Plus:     Nx11_Analog, the Channel index X is <AbstractParameter><Name>SelectedVal</name><Value>X</...
        # Classic:  InputSelect_8.Nx1-1_Analog
        strlist = cellname.text.split('_', 2)

        if plus and len(strlist) > 1:
            itype = strlist[1]
            idx = int(plus_abstract_parameter(module, "SelectedVal"))
        elif not plus and len(strlist) > 2:
            itype = strlist[2]
            idx = int(strlist[1].split('.', 1)[0])
        else:
            itype = "UNKNOWN"

        if "Analog" in itype:
            modparam = module.find(param_path)
            inputselect_analog[idx - 1][0] = intaddr(modparam)
        elif "SPDIF" in itype:
            modparam = module.find(param_path)
            inputselect_spdif[idx - 1][0] = intaddr(modparam)
        elif "UAC" in itype:
            modparam = module.find(param_path)
            inputselect_uac2[idx-1][0] = intaddr(modparam)
        elif "Exp" in itype:
            modparam = module.find(param_path)
            inputselect_exp[idx-1][0] = intaddr(modparam)
        elif "Mux" in itype:
            modparam = module.find(param_path)
            inputselect_port[idx-1][0] = intaddr(modparam)
        elif "ESP32" in itype:
            # do noting with ESP32:
            True
        else:
            print("[WARNING] Can not determine input type for input selector '" + cellname.text + "'!\n")

    elif cellname.text.startswith('SpdifOutMux') or (plus and cellname.text.startswith("Nx_")):
        # For SS+ and classic SS this works the same, just a different cellname
        count("SpdifOutMux")
        strlist = cellname.text.split('_')
        if len(strlist) > 2:
            if "Analog" in strlist[1]:
                modparam = module.find(param_path)
                if "Left" in strlist[2]:
                    spdifoutmux_channel[0][0] = intaddr(modparam)
                elif "Right" in strlist[2]:
                    spdifoutmux_channel[1][0] = intaddr(modparam)
            elif "UAC2" in strlist[1]:
                modparam = module.find(param_path)
                if "Left" in strlist[2]:
                    spdifoutmux_channel[0][1] = intaddr(modparam)
                elif "Right" in strlist[2]:
                    spdifoutmux_channel[1][1] = intaddr(modparam)
            elif "Exp" in strlist[1]:
                modparam = module.find(param_path)
                if "Left" in strlist[2]:
                    spdifoutmux_channel[0][2] = intaddr(modparam)
                elif "Right" in strlist[2]:
                    spdifoutmux_channel[1][2] = intaddr(modparam)
            elif "ESP32" in strlist[1]:
                modparam = module.find(param_path)
                if "Left" in strlist[2]:
                    spdifoutmux_channel[0][3] = intaddr(modparam)
                elif "Right" in strlist[2]:
                    spdifoutmux_channel[1][3] = intaddr(modparam)
            elif "SPDIF" in strlist[1]:
                modparam = module.find(param_path)
                if "Left" in strlist[2]:
                    spdifoutmux_channel[0][4] = intaddr(modparam)
                elif "Right" in strlist[2]:
                    spdifoutmux_channel[1][4] = intaddr(modparam)
            elif "Out" in strlist[1]:
                modparam = module.find(param_path)
                if "Left" in strlist[2]:
                    spdifoutmux_channel[0][5] = intaddr(modparam)
                elif "Right" in strlist[2]:
                    spdifoutmux_channel[1][5] = intaddr(modparam)
        else:
            modparam = module.find(param_path)
            if "Left" in strlist[1]:
                spdifoutmux_port[0] = intaddr(modparam)
            elif "Right" in strlist[1]:
                spdifoutmux_port[1] = intaddr(modparam)

    # --- HP blocks
    elif cellname.text.lower().startswith('plugin.hp') or (plus and cellname.text.lower().startswith('hp')):
        count("HP")
        if plus:
            name = cellname.text[:2]
            nn = int(cellname.text[3])-1
        else:
            name = cellname.text.split(':', 1)[0]
            nn = int(cellname.text.split(':', 1)[1]) - 1
        name = normalize_name(name)

        idx = -1
        for m in range(0, len(hp)):
            if hp[m].name == name:
                idx = m
        if idx == -1:
            newHp = ParamHp()
            hp.append(newHp)
            idx = len(hp) - 1
        hp[idx].name = name
        for modparam in module.findall(param_path):
            modname = modparam.find('Name').text
            if "B2" in modname:
                hp[idx].addr[nn] = intaddr(modparam)
                count("HP::B2")

    # --- LP blocks
    elif cellname.text.lower().startswith('plugin.lp') or (plus and cellname.text.lower().startswith('lp')):
        count("LP")
        if plus:
            name = cellname.text[:2]
            nn = int(cellname.text[3])-1
        else:
            name = cellname.text.split(':', 1)[0]
            nn = int(cellname.text.split(':', 1)[1]) - 1
        name = normalize_name(name)

        idx = -1
        for m in range(0, len(lp)):
            if lp[m].name == name:
                idx = m
        if idx == -1:
            newLp = ParamLp()
            lp.append(newLp)
            idx = len(lp) - 1
        lp[idx].name = name
        for modparam in module.findall(param_path):
            modname = modparam.find('Name').text
            if "B2" in modname:
                lp[idx].addr[nn] = intaddr(modparam)
                count("LP::B2")

    # --- LowShelv blocks
    elif cellname.text.lower().startswith('plugin.lowshelv') or (plus and cellname.text.lower().startswith('lowshelv')):
        count("LowShelv")
        for modparam in module.findall(param_path):
            modname = modparam.find('Name').text
            if "B2" in modname:
                newLShelv = ParamShelv()
                newLShelv.addr = intaddr(modparam)
                newLShelv.name = name = normalize_name(cellname.text)
                lshelv.append(newLShelv)
                count("LowShelv::B2")

    # --- HighShelv blocks
    elif cellname.text.lower().startswith('plugin.highshelv') or (plus and cellname.text.lower().startswith('highshelv')):
        count("HighShelv")
        for modparam in module.findall(param_path):
            modname = modparam.find('Name').text
            if "B2" in modname:
                newHShelv = ParamShelv()
                newHShelv.addr = intaddr(modparam)
                newHShelv.name = name = normalize_name(cellname.text)
                hshelv.append(newHShelv)
                count("HighShelv::B2")

    # --- PEQ banks
    elif cellname.text.lower().startswith('plugin.peqbank') or (plus and cellname.text.lower().startswith('peqbank')):
        count("PeqBank")
        newPeqBank = ParamPeqBank()
        newPeqBank.name = normalize_name(cellname.text)
        idx = 0
        for modparam in module.findall(param_path):
            modname = modparam.find('Name').text
            if "B2" in modname:
                if idx < 10:
                    newPeqBank.addr[idx] = intaddr(modparam)
                else:
                    # at least SS+ can do more, not sure why we're limiting here?
                    print("[ERROR] Not more then 10 PEQs per bank allowed.")
                idx = idx + 1
                count("PeqBank::B2")
        peqbank.append(newPeqBank)
        peqband.append(len(newPeqBank.addr))
        npeqbank = npeqbank + 1

    # --- PEQ blocks
    elif cellname.text.lower().startswith('plugin.peq') or (plus and cellname.text.lower().startswith('peq')):
        # TODO SS+: My project doesn't have plain PEQs, so I'm just vibing this here
        count("PEQ")
        for modparam in module.findall(param_path):
            modname = modparam.find('Name').text
            if "B2" in modname:
                newPeq = ParamPeq()
                newPeq.addr = intaddr(modparam)
                newPeq.name = normalize_name(cellname.text)
                peq.append(newPeq)
                count("PEQ::B2")

    # --- Phase blocks
    elif cellname.text.lower().startswith('plugin.phase') or (plus and cellname.text.lower().startswith('phase')):
        count("Phase")
        for modparam in module.findall(param_path):
            modname = modparam.find('Name').text
            if "B2" in modname:
                newPhase = ParamPhase()
                newPhase.addr = intaddr(modparam)
                newPhase.name = normalize_name(cellname.text)
                phase.append(newPhase)
                count("Phase::B2")

    # --- Delay blocks
    elif cellname.text.lower().startswith('plugin.delay') or (plus and cellname.text.lower().startswith('delay')):
        count("Delay")
        if plus:
            addr = plus_intaddr(module, "Delay")
        else:
            addr = False
            for modparam in module.findall(param_path):
                modname = modparam.find('Name').text
                if "delay" in modname:
                    addr = intaddr(modparam)
        if addr:
            newDelay = ParamDelay()
            newDelay.addr = addr
            newDelay.name = normalize_name(cellname.text)
            dly.append(newDelay)
            count("Delay::Delay")

    # --- Gain blocks
    elif cellname.text.lower().startswith('plugin.gain') or (plus and cellname.text.lower().startswith('gain')):
        count("Gain")
        if plus:
            addr = plus_intaddr(module, "Gain")
        else:
            addr = False
            for modparam in module.findall(param_path):
                modname = modparam.find('Name').text
                if "target" in modname:
                    addr = intaddr(modparam)

        if addr:
            newGain = ParamGain()
            newGain.addr = addr
            newGain.name = normalize_name(cellname.text)
            gain.append(newGain)
            count("Gain::Gain")

    # --- FIR blocks
    elif cellname.text.lower().startswith('plugin.fir') or (plus and cellname.text.lower().startswith('fir')):
        count("Fir")
        if plus:
            addr = plus_intaddr(module, "TableValues")
        else:
            addr = False
            for modparam in module.findall(param_path):
                modname = modparam.find('Name').text
                if "fircoeff" in modname:
                    addr = intaddr(modparam)

        if addr:
            newFir = ParamFir()
            newFir.addr = addr
            newFir.len = int(modparam.find('Size').text) / 4
            newFir.name = normalize_name(cellname.text)
            fir.append(newFir)
            count("Fir::Fir")

    # --- XO-HP blocks
    elif cellname.text.lower().startswith('plugin.xohp') or (plus and cellname.text.lower().startswith('xohp')):
        count("XO")
        if plus:
            searchlpname = cellname.text.lower().replace('xohp', 'xolp')
        else:
            searchlpname = cellname.text.lower().replace('plugin.xohp', 'plugin.xolp')
        # Search the corresponding LP block
        foundlp = False
        for modulelp in root.findall(search_path):
            cellnamelp = modulelp.find(cellname_block)
            if cellnamelp.text.lower().startswith(searchlpname):
                foundlp = True
                if plus:
                    name = cellname.text[:4]
                    nn = int(cellname.text[5])-1
                else:
                    name = cellname.text.split(':', 1)[0]
                    nn = int(cellname.text.split(':', 1)[1]) - 1
                name = normalize_name(name)
                idx = -1
                for m in range(0, len(xolp)):
                    if xolp[m].name == name:
                        idx = m
                if idx == -1:
                    newLp = ParamLp()
                    xolp.append(newLp)
                    idx = len(xolp) - 1
                xolp[idx].name = name
                for modparamlp in modulelp.findall(param_path):
                    modnamelp = modparamlp.find('Name').text
                    if "B2" in modnamelp:
                        xolp[idx].addr[nn] = intaddr(modparamlp)
                        count("XOLP::B2")
        if foundlp:
            if plus:
                name = cellname.text[:4]
                nn = int(cellname.text[5])-1
            else:
                name = cellname.text.split(':', 1)[0]
                nn = int(cellname.text.split(':', 1)[1]) - 1
            name = normalize_name(name)
            idx = -1
            for m in range(0, len(xohp)):
                if xohp[m].name == name:
                    idx = m
            if idx == -1:
                newHp = ParamHp()
                xohp.append(newHp)
                idx = len(xohp) - 1
            xohp[idx].name = name
            for modparam in module.findall(param_path):
                modname = modparam.find('Name').text
                if "B2" in modname:
                    xohp[idx].addr[nn] = intaddr(modparam)
                    count("XOHP::B2")
        else:
            print("[ERROR] Could not find matching lp block for " + cellname.text)

    # --- XO-LP blocks
    elif cellname.text.lower().startswith('plugin.xolp'):
        # Do nothing, handled by plugin.xohp
        pass

    elif cellname.text.startswith('BypassVolPoti') or (plus and cellname.text.startswith('BypassVolPoti')):
        count("BypassVolPoti")
        modparam = module.find(param_path)
        vpot = intaddr(modparam)

    elif cellname.text.startswith('MasterVolume'):
        count("MasterVolume")
        if plus:
            mastervol = plus_intaddr(module, "Gain")
        else:
            for modparam in module.findall(param_path):
                modname = modparam.find('Name').text
                if "target" in modname:
                    mastervol = intaddr(modparam)

    elif cellname.text.lower().startswith('plugin.'):
        print("[WARNING] Unkown dsp block in plugin: " + cellname.text)

if verbose:
    print("Parsing the project XML the following things have been accounted for:")
    total = 0
    for thing in counted_things.keys():
        print("    * " + str(counted_things[thing]) + " " + thing)
        total += counted_things[thing]
    print("    + Total: " + str(total))

inputselect_analog_t = GrowingList()
idx = 0
for m in range(0, len(inputselect_analog)):
    for n in range(0, len(inputselect_analog[m])):
        inputselect_analog_t[idx] = inputselect_analog[m][n]
        idx = idx+1

inputselect_spdif_t = GrowingList()
idx = 0
for m in range(0, len(inputselect_spdif)):
    for n in range(0, len(inputselect_spdif[m])):
        inputselect_spdif_t[idx] = inputselect_spdif[m][n]
        idx = idx+1

inputselect_uac2_t = GrowingList()
idx = 0
for m in range(0, len(inputselect_uac2)):
    for n in range(0, len(inputselect_uac2[m])):
        inputselect_uac2_t[idx] = inputselect_uac2[m][n]
        idx = idx+1

inputselect_exp_t = GrowingList()
idx = 0
for m in range(0, len(inputselect_exp)):
    for n in range(0, len(inputselect_exp[m])):
        inputselect_exp_t[idx] = inputselect_exp[m][n]
        idx = idx+1

inputselect_port_t = GrowingList()
idx = 0
for m in range(0, len(inputselect_port)):
    for n in range(0, len(inputselect_port[m])):
        inputselect_port_t[idx] = inputselect_port[m][n]
        idx = idx+1

spdifoutmux_channel_t = GrowingList()
idx = 0
for m in range(0, len(spdifoutmux_channel)):
    for n in range(0, len(spdifoutmux_channel[m])):
        spdifoutmux_channel_t[idx] = spdifoutmux_channel[m][n]
        idx = idx+1
spdifoutmux_channel_t.append(spdifoutmux_port[0])
spdifoutmux_channel_t.append(spdifoutmux_port[1])


# HP addresses
hp_t = GrowingList()
idx = 0
for m in range(0, len(hp)):
    for n in range(0, 4):
        if hp[m].addr[n] != -1:
            hp_t[idx] = hp[m].addr[n]
            idx = idx+1

# LP addresses
lp_t = GrowingList()
idx = 0
for m in range(0, len(lp)):
    for n in range(0, 4):
        if lp[m].addr[n] != -1:
            lp_t[idx] = lp[m].addr[n]
            idx = idx+1

# LowShelv addresses
lshelv_t = GrowingList()
for m in range(0, len(lshelv)):
    lshelv_t[m] = lshelv[m].addr

# HighShelv addresses
hshelv_t = GrowingList()
for m in range(0, len(hshelv)):
    hshelv_t[m] = hshelv[m].addr

# PEQ bank addresses
peqbank_t = GrowingList()
idx = 0
for m in range(0, len(peqbank)):
    for n in range(0, len(peqbank[m].addr)):
        if peqbank[m].addr[n] != -1:
            peqbank_t[idx] = peqbank[m].addr[n]
            idx = idx+1

# PEQ addresses
peq_t = GrowingList()
for m in range(0, len(peq)):
    peq_t[m] = peq[m].addr

# Phase addresses
phase_t = GrowingList()
for m in range(0, len(phase)):
    phase_t[m] = phase[m].addr

# Delay addresses
dly_t = GrowingList()
for m in range(0, len(dly)):
    dly_t[m] = dly[m].addr

# Gain address
gain_t = GrowingList()
for m in range(0, len(gain)):
    gain_t[m] = gain[m].addr

# FIR addresses + lengths
fir_t = GrowingList()
firlen_t = GrowingList()
for m in range(0, len(fir)):
    fir_t[m] = fir[m].addr
    firlen_t[m] = fir[m].len

# XO-HP addresses
xohp_t = GrowingList()
idx = 0
for m in range(0, len(xohp)):
    for n in range(0, 4):
        xohp_t[idx] = xohp[m].addr[n]
        idx = idx+1

# XO-LP addresses
xolp_t = GrowingList()
idx = 0
for m in range(0, len(xolp)):
    for n in range(0, 4):
        xolp_t[idx] = xolp[m].addr[n]
        idx = idx+1

nhp = int(len(hp_t)/4)
nlp = int(len(lp_t)/4)
nxolp = int(len(xolp_t)/4)
nxohp = int(len(xohp_t)/4)
nxo = nxohp
if nxo != nxolp:
    print('[ERROR] Counts of XO_LP and XO_HP do not match.')

nlshelv = len(lshelv_t)
nhshelv = len(hshelv_t)
npeq = len(peq_t)
#npeqbank = len(peqbank_t)
nphase = len(phase_t)
ndly = len(dly_t)
ngain = len(gain_t)
nfir = len(fir_t)

if nlp > 16:
    print("[ERROR] Number of low pass blocks exceeds the limit of 16")
if nhp > 16:
    print("[ERROR] Number of high pass blocks exceeds the limit of 16")
if nlshelv > 16:
    print("[ERROR] Number of low shelving blocks exceeds the limit of 16")
if nhshelv > 16:
    print("[ERROR] Number of high shelving blocks exceeds the limit of 16")
if npeq > 160:
    print("[ERROR] Number of peq blocks exceeds the limit of 160")
if npeqbank > 160:
    print("[ERROR] Number of peqbank blocks exceeds the limit of 16")
if nphase > 16:
    print("[ERROR] Number of phase blocks exceeds the limit of 16")
if ndly > 16:
    print("[ERROR] Number of delay blocks exceeds the limit of 16")
if ngain > 16:
    print("[ERROR] Number of gain blocks exceeds the limit of 16")
if nfir > 8:
    print("[ERROR] Number of FIR blocks exceeds the limit of 8")
if nxo > 16:
    print("[ERROR] Number of crossover blocks exceeds the limit of 16")

# --- Write plugin.ini
print("Writing plugin.ini")
data = {
    "name": nameplugin,
    "ninputs": ninputs,
    "noutputs": noutputs,
    "nhp": nhp,
    "nlshelv": nlshelv,
    "npeq": npeq,
    "npeqbank": npeqbank,
    "nhshelv": nhshelv,
    "nphase": nphase,
    "nlp": nlp,
    "ndly": ndly,
    "ngain": ngain,
    "nxo": nxo,
    "nfir": nfir,
    "analog": inputselect_analog_t,
    "spdif": inputselect_spdif_t,
    "uac": inputselect_uac2_t,
    "exp": inputselect_exp_t,
    "port": inputselect_port_t,
    "spdifout": spdifoutmux_channel_t,
    "hp": hp_t,
    "lshelv": lshelv_t,
    "peq": peq_t,
    "peqbank": peqbank_t,
    "peqband": peqband,
    "hshelv": hshelv_t,
    "lp": lp_t,
    "phase": phase_t,
    "dly": dly_t,
    "gain": gain_t,
    "xohp": xohp_t,
    "xolp": xolp_t,
    "fir": fir_t,
    "firlen": firlen_t,
    "vpot": vpot,
    "master": mastervol,
    "version": version,
}

webapp_path = os.path.join('..', 'WEBAPP')
project_path = os.path.join('.', outputdir + projectname)

# --- Write plugin.ini
plugin_ini_path = os.path.join(project_path, "plugin.ini")
with io.open(plugin_ini_path, 'w', encoding='utf8') as outfile:
    str_ = json.dumps(data,
                      indent=0, sort_keys=False,
                      separators=(',', ': '), ensure_ascii=False)
    outfile.write(to_unicode(str_))

# --- Copy aurora.jgz
print("Copying aurora.jgz")
aurora_jgz_src_path = os.path.join(webapp_path, 'js', 'aurora.jgz')
aurora_jgz_dst_path = os.path.join(project_path, 'aurora.jgz')
shutil.copy2(aurora_jgz_src_path, aurora_jgz_dst_path)

# --- Copy stylesheet
print("Copying dark.css")
darkcss_src_path = os.path.join(webapp_path, 'css', 'dark.css')
darkcss_dst_path = os.path.join(project_path, 'dark.css')
shutil.copy2(darkcss_src_path, darkcss_dst_path)

# ------------------------------------------------------------------------------
# GUI creation
# ------------------------------------------------------------------------------
chnames_txt_path = os.path.join(project_path, "chnames.txt")
chnames_txt_created = False

if args.gui:
    # --- Copy custom GUI html
    print("Copying custom dsp.html")
    print(args.gui)

    with open(args.gui, 'r') as f:
        dsphtml = str(f.read())

        # --- replace LP names
        for m in range(0, len(lp)):
            dsphtml = dsphtml.replace(
                "id=\"" + lp[m].name.split('.', 1)[1] + "\"",
                "id=\"lp" + str(m) + "\" onclick=\"openLP(" + str(m) + ");\""
            )

        # --- replace HP names
        for m in range(0, len(hp)):
            dsphtml = dsphtml.replace(
                "id=\"" + hp[m].name.split('.', 1)[1] + "\"",
                "id=\"hp" + str(m) + "\" onclick=\"openHP(" + str(m) + ");\""
            )

        # --- LowShelv blocks
        for m in range(0, len(lshelv)):
            dsphtml = dsphtml.replace(
                "id=\"" + lshelv[m].name.split('.', 1)[1] + "\"",
                "id=\"ls" + str(m) + "\" onclick=\"openLShelv(" + str(m) + ");\""
            )

        # --- HighShelv blocks
        for m in range(0, len(hshelv)):
            dsphtml = dsphtml.replace(
                "id=\"" + hshelv[m].name.split('.', 1)[1] + "\"",
                "id=\"hs" + str(m) + "\" onclick=\"openHShelv(" + str(m) + ");\""
            )

        # --- PEQ banks
        for m in range(0, len(peqbank)):
            dsphtml = dsphtml.replace(
                "id=\"" + peqbank[m].name.split('.', 1)[1] + "\"",
                "id=\"peqbank" + str(m) + "\" onclick=\"openPeqBank(" + str(m) + ");\""
            )

        # --- PEQ blocks
        for m in range(0, len(peq)):
            dsphtml = dsphtml.replace(
                "id=\"" + peq[m].name.split('.', 1)[1] + "\"",
                "id=\"peq" + str(m) + "\" onclick=\"openPEQ(" + str(m) + ");\""
            )

        # --- Phase blocks
        for m in range(0, len(phase)):
            dsphtml = dsphtml.replace(
                "id=\"" + phase[m].name.split('.', 1)[1] + "\"",
                "id=\"ph" + str(m) + "\" onclick=\"openPhase(" + str(m) + ");\""
            )

        # --- Delay blocks
        for m in range(0, len(dly)):
            dsphtml = dsphtml.replace(
                "id=\"" + dly[m].name.split('.', 1)[1] + "\"",
                "id=\"dly" + str(m) + "\" onclick=\"openDelay(" + str(m) + ");\""
            )

        # --- Gain blocks
        for m in range(0, len(gain)):
            dsphtml = dsphtml.replace(
                "id=\"" + gain[m].name.split('.', 1)[1] + "\"",
                "id=\"gn" + str(m) + "\" onclick=\"openGain(" + str(m) + ");\""
            )

        # --- FIR blocks
        for m in range(0, len(fir)):
            dsphtml = dsphtml.replace(
                "id=\"" + fir[m].name.split('.', 1)[1] + "\"",
                "id=\"fir" + str(m) + "\" onclick=\"openFIR(" + str(m) + ");\""
            )

        # --- XO-HP blocks
        for m in range(0, len(xohp)):
            dsphtml = dsphtml.replace(
                "id=\"" + xohp[m].name.split('.', 1)[1].replace("HP", "") + "\"",
                "id=\"xo" + str(m) + "\" onclick=\"openXO(" + str(m) + ");\""
            )

        # --- XO-LP blocks
        # Handled by xohp

    dsp_html_path = os.path.join(project_path, 'dsp.html')
    with open(dsp_html_path, "w") as f1:
        f1.write(dsphtml)

    custom_chnames_path = args.gui.replace("dsp.html", "chnames.txt")
    if os.path.isfile(custom_chnames_path):
        print("Copying custom chnames.txt from " + custom_chnames_path)
        shutil.copy2(custom_chnames_path, chnames_txt_path)
        chnames_txt_created = True
else:
    # --- Copy GUI template
    print("Copying template dsp.html")
    template_dsp_html_path = os.path.join(webapp_path, 'plugins', 'template', 'dsp.html')
    project_dsp_html_path = os.path.join(project_path, 'dsp.html')
    shutil.copy2(template_dsp_html_path, project_dsp_html_path)

if not chnames_txt_created:
    # --- Writing chnames.txt
    print("Writing default chnames.txt")
    with open(chnames_txt_path, 'w') as file:
        for ii in range(0, ninputs):
            file.write("Channel " + str(ii + 1) + "\n")
        for ii in range(0, noutputs):
            file.write("Out " + str(ii + 1) + "\n")
        file.write("Preset A\n")
        file.write("Preset B\n")
        file.write("Preset C\n")
        file.write("Preset D\n")
