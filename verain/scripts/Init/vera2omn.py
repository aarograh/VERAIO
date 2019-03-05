###############################################################################
# File  : VERAInExt/verain/scripts/utils/vera2omn.py
# Author: Katherine E Royston
# Date  : Wed Feb 20 14:43:58 EST 2019
#
# Generate excore omnibus input from VERA input
###############################################################################
from __future__ import (division, absolute_import, print_function, )

import numpy as np
import re
import sys
import xml.etree.ElementTree as etree
###############################################################################

def _strictly_increasing(a):
    return all(x<y for x, y in zip(a, a[1:]))

###############################################################################
# DetectorType
###############################################################################

class DetectorType(object):
    """Detector object for each unique detector specification"""

    def __init__(self, ):
        self.label     = ''
        self.det_type  = ''
        self.mats      = []
        self.radii     = []
        self.heights   = []
        self.response  = ''
        self.well_type = ''

    def load(self, block):
        for child in block:
            if child.attrib["name"] == "label":
                self.label = child.attrib["value"]
            elif child.attrib["name"] == "type":
                self.det_type = child.attrib["value"]
            elif child.attrib["name"] == "mats":
                mats_str = re.sub(r"[{}]", "", child.attrib['value'])
                self.mats = mats_str.strip().split(',')
            elif child.attrib["name"] == "radii":
                rad_str = re.sub(r"[{}]", "", child.attrib['value'])
                self.radii = rad_str.strip().split(',')
                self.radii = [float(i) for i in self.radii]
            elif child.attrib["name"] == "heights":
                rad_str = re.sub(r"[{}]", "", child.attrib['value'])
                self.heights = rad_str.strip().split(',')
                self.heights = [float(i) for i in self.heights]
            elif child.attrib["name"] == "response":
                self.response = re.sub(r"[{}]", "", child.attrib["value"])
            elif child.attrib["name"] == "well_type":
                self.well_type = child.attrib["value"]

###############################################################################
# VERAOmnibusGenerator
###############################################################################

class VERAOmnibusGenerator(object):

    def __init__(self, basename, script_dir):
        self.infile           = basename + ".xml"
        self.outfile          = basename + ".omn"
        self.xml_data         = None
        self.xml_shift        = None
        self.template_file    = script_dir + "Init/omnibus_template.txt"
        self.cell_file        = script_dir + "Init/cell_template.txt"
        self.shape_file       = script_dir + "Init/shape_template.txt"
        self.tally_file       = script_dir + "Init/tally_template.txt"
        self.bioshield_mats   = None
        self.bioshield_radii  = None
        self.vessel_rads      = None
        self.height           = 0.0
        self.lower_refl       = 0.0
        self.upper_refl       = 0.0
        self.lower_plate      = 0.0
        self.upper_plate      = 0.0
        self.det_type_list    = []
        self.detectors        = []
        self.det_label_locs   = []
        self.det_rad_locs     = []
        self.det_azi_locs     = []
        self.det_elev_locs    = []
        self.translate        = [0.0, 0.0, 0.0]
        self.materials        = []
        self.tally_cells      = []

    def load(self):

        core_block = None

        # Load the xml file
        self.xml_data = etree.parse(self.infile)
        xml_root = self.xml_data.getroot()

        # Look for the CORE block
        for child in xml_root:
            if child.attrib['name'] == 'CORE':
                core_block = child

                # Check for parameters needed
                for core_child in core_block:

                    # Get the bioshield materials
                    if core_child.attrib['name'] == 'bioshield_mats':
                        mats_str = re.sub(r"[{}]", "",
                                core_child.attrib['value'])
                        self.bioshield_mats = mats_str.strip().split(',')

                    # Get the bioshield radii
                    if core_child.attrib['name'] == 'bioshield_radii':
                        rads_str = re.sub(r"[{}]", "",
                                core_child.attrib['value'])
                        self.bioshield_radii = rads_str.strip().split(',')
                        self.bioshield_radii = \
                                [float(i) for i in self.bioshield_radii]

                    # Get the vessel radii
                    if core_child.attrib['name'] == 'vessel_radii':
                        rads_str = re.sub(r"[{}]", "",
                                core_child.attrib['value'])
                        self.vessel_rads = rads_str.strip().split(',')
                        self.vessel_rads = [float(i) for i in self.vessel_rads]

                    # Get the height
                    if core_child.attrib['name'] == 'height':
                        self.height = float(core_child.attrib['value'].strip())

                    # Get the lower plate thickeness
                    if core_child.attrib['name'] == 'lower_thick':
                        self.lower_plate = float(core_child.attrib['value'].strip())

                    # Get the upper plate thickeness
                    if core_child.attrib['name'] == 'upper_thick':
                        self.upper_plate = float(core_child.attrib['value'].strip())

                    # Get the lower reflector thickeness
                    if core_child.attrib['name'] == 'lower_refl_thicks':
                        refl_str = re.sub(r"[{}]", "",
                                core_child.attrib['value'])
                        refl_thicks = refl_str.strip().split(',')
                        refl_thicks = [float(i) for i in refl_thicks]
                        self.lower_refl = sum(refl_thicks)

                    # Get the upper reflector thickeness
                    if core_child.attrib['name'] == 'upper_refl_thicks':
                        refl_str = re.sub(r"[{}]", "",
                                core_child.attrib['value'])
                        refl_thicks = refl_str.strip().split(',')
                        refl_thicks = [float(i) for i in refl_thicks]
                        self.upper_refl = sum(refl_thicks)

                    # Get the specifications for each detector type and build
                    if core_child.attrib['name'] == "Excore_Detectors":
                        for det_block in core_child:
                            det = DetectorType()
                            det.load(det_block)
                            self.det_type_list.append(det)

                    # Get the detector locations
                    if core_child.attrib['name'] == "det_label_locs":
                        det_str = re.sub(r"[{}]", "",
                                core_child.attrib['value'])
                        self.det_label_locs = det_str.strip().split(',')
                    if core_child.attrib['name'] == "det_rad_locs":
                        det_str = re.sub(r"[{}]", "",
                                core_child.attrib['value'])
                        self.det_rad_locs = det_str.strip().split(',')
                        self.det_rad_locs = \
                                [float(i) for i in self.det_rad_locs]
                    if core_child.attrib['name'] == "det_azi_locs":
                        det_str = re.sub(r"[{}]", "",
                                core_child.attrib['value'])
                        self.det_azi_locs = det_str.strip().split(',')
                        self.det_azi_locs = \
                                [float(i) for i in self.det_azi_locs]
                    if core_child.attrib['name'] == "det_elev_locs":
                        det_str = re.sub(r"[{}]", "",
                                core_child.attrib['value'])
                        self.det_elev_locs = det_str.strip().split(',')
                        self.det_elev_locs = \
                                [float(i) for i in self.det_elev_locs]

            if child.attrib['name'] == 'SHIFT':
                self.xml_shift = child
                for shift_child in self.xml_shift:
                    if shift_child.attrib['name'] == 'core_translate':
                        trans_str = re.sub(r"[{}]", "",
                                shift_child.attrib['value'])
                        self.translate = trans_str.strip().split(',')
                        self.translate = [float(i) for i in self.translate]

        # To generate the Omnibus excore file, there must be a CORE block and
        # it must contain bioshield materials, bioshield radii, and vessel
        # radii. There also must be a SHIFT block.
        if (core_block == None or
                self.xml_shift == None or
                self.bioshield_mats == None or
                self.bioshield_radii == None or
                self.vessel_rads == None):
            return False

        if _strictly_increasing(self.bioshield_radii) == False:
            print("Error: bioshield radii must be monotonically increasing!")
            exit()

        if self.bioshield_radii[0] < self.vessel_rads[-1]:
            print("Error: bioshield radii must be larger than vessel")
            exit()

        return True

    def write(self):

        # Read in the Omnibus template file
        with open(self.template_file, 'r') as temp_file:
            template = temp_file.readlines()

        # Determine bounds
        min_z = 0.0 - self.lower_refl - self.lower_plate
        max_z = self.height + self.upper_refl + self.upper_plate
        bnds = [-self.bioshield_radii[-1], self.bioshield_radii[-1],
                -self.bioshield_radii[-1], self.bioshield_radii[-1],
                min_z, max_z]
        bnds = [str(i) for i in bnds]

        # Get a list of template materials
        self._get_template_materials()

        # Write out the Omnibus excore file
        with open(self.outfile, 'w') as outfile:
            for line in template:
                if "OMN_BOUNDARY_BOX" in line:
                    line_filled = re.sub(r'OMN_BOUNDARY_BOX', ' '.join(bnds),
                            line)
                    outfile.write(line_filled)
                elif "OMN_BIOSHIELD_SHAPES" in line:
                    self._write_bioshield_shapes(outfile)
                elif "OMN_DETECTOR_SHAPES" in line:
                    det_outers = self._write_detector_shapes(outfile)
                elif "OMN_BIOSHIELD_CELLS" in line:
                    self._write_bioshield_cells(outfile,
                            det_outers)
                elif "OMN_DETECTOR_CELLS" in line:
                    self._write_detector_cells(outfile)
                elif "OMN_CORE_TRANSLATION" in line:
                    line_filled = re.sub(r'OMN_CORE_TRANSLATION',
                            ' '.join([str(i) for i in self.translate]), line)
                    outfile.write(line_filled)
                elif "OMN_" in line:
                    print("Error: unknown placeholder in template line:\n" +
                            line)
                    outfile.write(line)
                else:
                    outfile.write(line)

            # If we have detectors, we need to make tallies for them
            if len(self.tally_cells) > 0:
                self._write_detector_tallies(outfile)

    def _write_bioshield_shapes(self, outfile):
        # Determine bounds
        min_z = 0.0 - self.lower_refl - self.lower_plate
        max_z = self.height + self.upper_refl + self.upper_plate

        # Loop over bioshield radii
        for bio_num in range(len(self.bioshield_radii)):
            outfile.write("! Bioshield shape\n")
            with open(self.shape_file, 'r') as shape_file:
                for shape_line in shape_file:
                    if "OMN_SHAPE_ID" in shape_line:
                        line_filled = re.sub(r'OMN_SHAPE_ID',
                                'bioshield_' + str(bio_num),
                                shape_line)
                        outfile.write(line_filled)
                    elif "OMN_RADIUS" in shape_line:
                        line_filled = re.sub(r'OMN_RADIUS',
                                str(self.bioshield_radii[bio_num]),
                                shape_line)
                        outfile.write(line_filled)
                    elif "OMN_Z_LOWER" in shape_line:
                        line_filled = re.sub(
                                r'OMN_Z_LOWER',
                                str(min_z),
                                shape_line)
                        if not "OMN_Z_UPPER" in shape_line:
                            print("Template error: OMN_Z_UPPER")
                            exit()
                        line_filled = re.sub(
                                r'OMN_Z_UPPER',
                                str(max_z),
                                line_filled)
                        outfile.write(line_filled)
                    elif "OMN_ORIGIN" in shape_line:
                        line_filled = re.sub(r'OMN_ORIGIN', '0 0 0', shape_line)
                        outfile.write(line_filled)
                    else:
                        outfile.write(shape_line)

    def _write_bioshield_cells(self, outfile, det_outers):

        # Loop over the bioshield radii
        for bio_num in range(len(self.bioshield_radii)):
            outfile.write("! Bioshield cell\n")
            with open(self.cell_file, 'r') as cell_file:
                for cell_line in cell_file:
                    if "OMN_CELL_ID" in cell_line:
                        line_filled = re.sub(r'OMN_CELL_ID',
                                'bioshield_' + str(bio_num), cell_line)
                        outfile.write(line_filled)
                    elif "OMN_COMP" in cell_line:
                        if self.bioshield_mats[bio_num] in self.materials:
                            line_filled = re.sub(r'OMN_COMP',
                                    self.bioshield_mats[bio_num], cell_line)
                            outfile.write(line_filled)
                        else:
                            print("Error: material " +
                                    self.bioshield_mats[bio_num] +
                                    " not available.")
                            exit()
                    elif "OMN_DEFINE_CELL" in cell_line:
                        cell_def = ' +thecore'
                        #for c in range(bio_num):
                        #    cell_def += " +bioshield_" + str(c)
                        if bio_num > 0:
                            cell_def += " +bioshield_" + str(bio_num - 1)
                        cell_def += " -bioshield_" + str(bio_num)
                        line_filled = re.sub(r'OMN_DEFINE_CELL',
                                cell_def, cell_line)
                        outfile.write(line_filled)
                        det_num = 0
                        det_shape_str = '        '
                        for d in det_outers:
                            if det_num%4 == 0:
                                det_shape_str += '\n        '
                            det_shape_str += ' ' + d
                            det_num += 1
                        outfile.write(det_shape_str)
                    else:
                        outfile.write(cell_line)

        # Write the cell for outside the bioshield
        with open(self.cell_file, 'r') as cell_file:
            for cell_line in cell_file:
                if "OMN_CELL_ID" in cell_line:
                    line_filled = re.sub(r'OMN_CELL_ID',
                            'outside_bioshield', cell_line)
                    outfile.write(line_filled)
                elif "OMN_COMP" in cell_line:
                    line_filled = re.sub(r'OMN_COMP',
                            'void', cell_line)
                    outfile.write(line_filled)
                elif "OMN_DEFINE_CELL" in cell_line:
                    cell_def = ' +thecore'
                    cell_def += " +bioshield_" + \
                            str(len(self.bioshield_radii) - 1)
                    cell_def += " -box"
                    line_filled = re.sub(r'OMN_DEFINE_CELL',
                            cell_def, cell_line)
                    outfile.write(line_filled)


    def _write_detector_shapes(self, outfile):
        # Store the outermost detector shapes for defining bioshield cells
        det_outers = []

        # Loop over the detectors
        for d in range(len(self.det_label_locs)):
            # Get the position of the detector
            pos = [0, 0, 0]
            pos[0] = self.det_rad_locs[d] * \
                    np.cos(-self.det_azi_locs[d] * np.pi / 180.0)
            pos[1] = self.det_rad_locs[d] * \
                    np.sin(-self.det_azi_locs[d] * np.pi / 180.0)

            # Get the type for this detector
            for dt in self.det_type_list:
                if dt.label == self.det_label_locs[d]:
                    det_type = dt

            # Write out a shape for each radius and height
            shape_num = 0
            min_z     = self.det_elev_locs[d]
            for h in det_type.heights:
                for r in det_type.radii:
                    outfile.write("! Detector " + str(d) + " shape (" +
                            det_type.label  + ")\n")
                    shape_label = 'detector_' + str(d) + "_" + str(shape_num)
                    with open(self.shape_file, 'r') as shape_file:
                        for shape_line in shape_file:
                            if "OMN_SHAPE_ID" in shape_line:
                                line_filled = re.sub(r'OMN_SHAPE_ID',
                                        shape_label, shape_line)
                                outfile.write(line_filled)
                            elif "OMN_RADIUS" in shape_line:
                                line_filled = re.sub(r'OMN_RADIUS',
                                        str(r),
                                        shape_line)
                                outfile.write(line_filled)
                            elif "OMN_Z_LOWER" in shape_line:
                                line_filled = re.sub(
                                        r'OMN_Z_LOWER',
                                        str(min_z),
                                        shape_line)
                                if not "OMN_Z_UPPER" in shape_line:
                                    print("Template error: OMN_Z_UPPER")
                                    exit()
                                line_filled = re.sub(
                                        r'OMN_Z_UPPER',
                                        str(min_z + h),
                                        line_filled)
                                outfile.write(line_filled)
                            elif "OMN_ORIGIN" in shape_line:
                                line_filled = re.sub(r'OMN_ORIGIN',
                                        ' '.join([str(p) for p in pos]),
                                        shape_line)
                                outfile.write(line_filled)
                            else:
                                outfile.write(shape_line)
                    if r == det_type.radii[-1]:
                        det_outers.append("+" + shape_label)
                    shape_num += 1
                min_z += h
        return det_outers

    def _write_detector_cells(self, outfile):
        # Loop over the detectors
        for d in range(len(self.det_label_locs)):
            # Get the type for this detector
            for dt in self.det_type_list:
                if dt.label == self.det_label_locs[d]:
                    det_type = dt

            # Write out a cell for each radius and height
            label_num = 0
            for h in det_type.heights:
                for r,m in zip(det_type.radii,det_type.mats):
                    outfile.write("! Detector " + str(d) + " cell (" +
                            det_type.label  + ")\n")
                    cell_label = 'detector_' + str(d) + "_" + str(label_num)
                    with open(self.cell_file, 'r') as cell_file:
                        for cell_line in cell_file:
                            if "OMN_CELL_ID" in cell_line:
                                line_filled = re.sub(r'OMN_CELL_ID',
                                        cell_label, cell_line)
                                outfile.write(line_filled)
                            elif "OMN_COMP" in cell_line:
                                if m in self.materials:
                                    line_filled = re.sub(r'OMN_COMP',
                                            m, cell_line)
                                    outfile.write(line_filled)
                                else:
                                    print("Error: material " +
                                            m + " not available.")
                                    exit()
                            elif "OMN_DEFINE_CELL" in cell_line:
                                cell_def = " -detector_" + str(d) + \
                                        "_" + str(label_num)
                                if r > det_type.radii[0]:
                                    cell_def += " +detector_" + str(d) + \
                                            "_" + str(label_num - 1)
                                line_filled = re.sub(r'OMN_DEFINE_CELL',
                                        cell_def, cell_line)
                                outfile.write(line_filled)
                            else:
                                outfile.write(cell_line)
                    if r == det_type.radii[0]:
                        self.tally_cells.append([cell_label, det_type.response,
                            det_type.label])
                    label_num += 1

    def _write_detector_tallies(self, outfile):
        outfile.write(
                "! =========================================================\n")
        outfile.write(
                "!                      DEFINE THE TALLIES\n")
        outfile.write(
                "! =========================================================\n")
        outfile.write("[TALLY]\n")
        for t in self.tally_cells:
            outfile.write("\n")
            with open(self.tally_file, 'r') as tally_file:
                for tally_line in tally_file:
                    if "OMN_TALLY_ID" in tally_line:
                        line_filled = re.sub(r'OMN_TALLY_ID',
                                t[0], tally_line)
                        outfile.write(line_filled)
                    elif "OMN_TALLY_CELLS" in tally_line:
                        line_filled = re.sub(r'OMN_TALLY_CELLS',
                                t[0], tally_line)
                        outfile.write(line_filled)
                    elif "OMN_RESPONSE" in tally_line:
                        line_filled = re.sub(r'OMN_RESPONSE',
                                t[1], tally_line)
                        outfile.write(line_filled)

    def _get_template_materials(self):
        # Read in the Omnibus template file
        with open(self.template_file, 'r') as temp_file:
            self.materials = re.findall(r'^\[COMP\]\[MATERIAL\s+([\w.-]+)',
                    temp_file.read(), re.M)

    def update_vera_xml(self):
        if len(self.tally_cells) == 0:
            return

        # See if we have hybrid tally names and multipliers
        xml_hybrid_tally = None
        xml_hybrid_mult  = None
        for shift_child in self.xml_shift:
            if shift_child.attrib['name'] == 'hybrid_tally_names':
                xml_hybrid_tally = shift_child
            if shift_child.attrib['name'] == 'hybrid_multiplier_names':
                xml_hybrid_mult = shift_child

        # If the hybrid tally name(s) was not given in the VERA input,
        # we optimize for all tally cells
        if xml_hybrid_tally == None:
            tally_name_list = []
            tally_mult_list = []
            for t in self.tally_cells:
                tally_name_list.append(t[0])
                tally_mult_list.append('flux')
            tally_names = '{' + ','.join(tally_name_list) + '}'
            tally_mults = '{' + ','.join(tally_mult_list) + '}'

            tally_tag = etree.SubElement(self.xml_shift, 'Parameter')
            tally_tag.attrib['name'] = 'hybrid_tally_names'
            tally_tag.attrib['type'] = 'Array(string)'
            tally_tag.attrib['value'] = tally_names

            mult_tag = etree.SubElement(self.xml_shift, 'Parameter')
            mult_tag.attrib['name'] = 'hybrid_multiplier_names'
            mult_tag.attrib['type'] = 'Array(string)'
            mult_tag.attrib['value'] = tally_mults

        # If the hybrid tally names are given we need to see if we have
        # detector types or specific tallies. We also need to update
        # the tally multipliers to match.
        else:
            tally_name_list = []
            tally_mult_list = []
            tally_str = re.sub(r"[{}]", "",
                    xml_hybrid_tally.attrib['value'])
            tally_types = tally_str.strip().split(',')
            for t in self.tally_cells:
                if t[2] in tally_types:
                    tally_name_list.append(t[0])
                    tally_mult_list.append('flux')
            tally_names = '{' + ','.join(tally_name_list) + '}'
            tally_mults = '{' + ','.join(tally_mult_list) + '}'

            # If the specified tally name does not match any of the
            # detector types, leave it.
            if len(tally_name_list) == 0:
                return

            xml_hybrid_tally.set('value', tally_names)

            # If no multiplier tag was given, add it. Otherwise, replace the
            # values to match the number of tallies.
            if xml_hybrid_mult == None:
                mult_tag = etree.SubElement(self.xml_shift, 'Parameter')
                mult_tag.attrib['name'] = 'hybrid_multiplier_names'
                mult_tag.attrib['type'] = 'Array(string)'
                mult_tag.attrib['value'] = tally_mults
            else:
                xml_hybrid_mult.set('value', tally_mults)

        # Write back to file
        self.xml_data.write(self.infile)


###############################################################################
# main
###############################################################################

def main(argv=None):

    # Build the Omnibus input generator
    generator = VERAOmnibusGenerator(sys.argv[1], sys.argv[2])

    # Load the VERA xml file
    gen_omnibus = generator.load()

    # Exit if we don't have the correct input paramters
    # to generate an Omnibus file
    if gen_omnibus == False:
        exit()

    # Write the Omnibus excore file
    print("Writing Omnibus excore input file")
    generator.write()

    # Update VERA xml input file with tallies to optimize for
    generator.update_vera_xml()

#-----------------------------------------------------------------------------#
if __name__ == "__main__":
    main()

###############################################################################
# end of VERAInExt/verain/scripts/utils/vera2omn.py
###############################################################################
