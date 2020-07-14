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
        self.well_type = 'none'

###############################################################################

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
                self.well_type = re.sub(r"[{}]", "", child.attrib["value"])

###############################################################################
# VERAOmnibusGenerator
###############################################################################

class VERAOmnibusGenerator(object):

    def __init__(self, basename, script_dir):
        self.infile           = basename + ".xml"
        self.outfile          = basename + ".omn"
        self.xml_excore_file  = basename + ".excore.xml"
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
        self.translate        = None
        self.materials        = []
        self.tally_cells      = []
        self.vera_pv          = None

###############################################################################

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

                    # Get the lower plate thickness
                    if core_child.attrib['name'] == 'lower_thick':
                        self.lower_plate = float(core_child.attrib['value'].strip())

                    # Get the upper plate thickness
                    if core_child.attrib['name'] == 'upper_thick':
                        self.upper_plate = float(core_child.attrib['value'].strip())

                    # Get the lower reflector thickness
                    if core_child.attrib['name'] == 'lower_refl_thicks':
                        refl_str = re.sub(r"[{}]", "",
                                core_child.attrib['value'])
                        refl_thicks = refl_str.strip().split(',')
                        refl_thicks = [float(i) for i in refl_thicks]
                        self.lower_refl = sum(refl_thicks)

                    # Get the upper reflector thickness
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
                    if shift_child.attrib['name'] == 'vera_pressure_vessel':
                        self.vera_pv = shift_child.attrib['value'].strip()

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
            exit(1)

        if self.bioshield_radii[0] < self.vessel_rads[-1]:
            print("Error: bioshield radii must be larger than vessel")
            exit(1)

        # The pressure vessel from the VERA input should be pulled in
        translate_ref = [-self.vessel_rads[-1], -self.vessel_rads[-1], 0]
        if self.vera_pv is None:
            print("Warning: setting vera_pressure_vessel to True.")
            self.vera_pv = "true"
        if self.vera_pv.lower() == "true":
            if self.translate is None:
                self.translate = translate_ref
                print("Setting core_translate in Shift block using outer" + \
                        " vessel radius.")
            else:
                if (self.translate[0] != translate_ref[0] or
                        self.translate[1] != translate_ref[1] or
                        self.translate[2] != translate_ref[2]):
                    print("Error: core_translate parameter should match " + \
                            "outer vessel radius.")
        else:
            print("Error: vera_pressure_vessel is False but automated excore " +
                  "generator will only define the geometry beyond the vessel.")
            exit(1)

        return True

###############################################################################

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
                    self._write_bioshield_cells(outfile, det_outers)
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

###############################################################################

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
                            exit(1)
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

###############################################################################

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
                            exit(1)
                    elif "OMN_DEFINE_CELL" in cell_line:
                        cell_def = ' +thecore'
                        if bio_num > 0:
                            cell_def += " +bioshield_" + str(bio_num - 1)
                        cell_def += " -bioshield_" + str(bio_num)
                        line_filled = re.sub(r'OMN_DEFINE_CELL',
                                cell_def, cell_line)
                        outfile.write(line_filled)
                        det_num = 1
                        det_shape_str = '       '
                        for d in det_outers:
                            det_shape_str += ' ' + d
                            if det_num%4 == 0:
                                det_shape_str += '\n        '
                            det_num += 1
                        outfile.write(det_shape_str)
                        outfile.write("\n")
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
                    outfile.write(line_filled + "\n")

###############################################################################

    def _write_detector_shapes(self, outfile):
        # Store the outermost detector shapes for defining bioshield cells
        # and wells
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

            # Check if parameters are valid
            if (self.bioshield_radii[-1] <
                    self.det_rad_locs[d] + det_type.radii[-1]):
                print("Error: detector cannot extend beyond bioshield")
                exit(1)

            if (self.det_rad_locs[d] - det_type.radii[-1] <
                    self.vessel_rads[-1]):
                print("Error: detector cannot extend into vessel")
                exit(1)

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
                                        '{:f}'.format(r),
                                        shape_line)
                                outfile.write(line_filled)
                            elif "OMN_Z_LOWER" in shape_line:
                                line_filled = re.sub(
                                        r'OMN_Z_LOWER',
                                        '{:f}'.format(min_z),
                                        shape_line)
                                if not "OMN_Z_UPPER" in shape_line:
                                    print("Template error: OMN_Z_UPPER")
                                    exit(1)
                                line_filled = re.sub(
                                        r'OMN_Z_UPPER',
                                        '{:f}'.format(min_z + h),
                                        line_filled)
                                outfile.write(line_filled)
                            elif "OMN_ORIGIN" in shape_line:
                                # line_filled = re.sub(r'OMN_ORIGIN',
                                #         ' '.join([str(p) for p in pos]),
                                #         shape_line)
                                line_filled = re.sub(r'OMN_ORIGIN',
                                        ' '.join(['{:f}'.format(p) for p in pos]),
                                        shape_line)
                                outfile.write(line_filled)
                            else:
                                outfile.write(shape_line)
                    if r == det_type.radii[-1]:
                        det_outers.append("+" + shape_label)
                    shape_num += 1
                min_z += h

            # Write out the well shape, if applicable
            if det_type.well_type == "wedge":
                # Check for valid parameters
                if (self.bioshield_radii[-1] < self.det_rad_locs[d] +
                        np.sqrt(2.0) * det_type.radii[-1]):
                    print("Error: detector well cannot extend beyond bioshield")
                    exit(1)

                if (self.det_rad_locs[d] + np.sqrt(2.0) * det_type.radii[-1] <
                        self.bioshield_radii[0]):
                    print("Error: detector well will not intersect bioshield")
                    exit(1)

                # Calculate well dimensions
                azi = self.det_azi_locs[d]
                bio_r = self.bioshield_radii[0]
                c = self.det_rad_locs[d] + (det_type.radii[-1] * np.sqrt(2.0))
                xo = 0.5 * (c + np.sqrt(2.0 * bio_r * bio_r - c * c))
                yo = xo - self.det_rad_locs[d] - det_type.radii[-1] * np.sqrt(2.0)
                a = 2.0 * np.abs(yo) / np.sqrt(2.0)
                height = min_z - self.det_elev_locs[d]

                # Rotate the well to the detector location
                well_pos = [xo * np.cos(np.deg2rad(-azi)) -
                            yo * np.sin(np.deg2rad(-azi)),
                            xo * np.sin(np.deg2rad(-azi)) +
                            yo * np.cos(np.deg2rad(-azi)),
                            self.det_elev_locs[d]]
                rot = 0.125 - (azi / 360.0)
                if rot < 0.0:
                    rot = rot + 1.0

                # Write out the well shape
                outfile.write("! Detector " + str(d) + " well\n")
                outfile.write("[UNIVERSE][SHAPE=" + det_type.well_type +
                        " well_" + str(d) + "]\n")
                outfile.write("corner_pt " + '{:f}'.format(a) + " " +
                                             '{:f}'.format(a) + "\n")
                outfile.write("height " + '{:f}'.format(height) + "\n")
                outfile.write("origin " + '{:f}'.format(well_pos[0]) + " " +
                                          '{:f}'.format(well_pos[1]) + " " +
                                          '{:f}'.format(well_pos[2]) + "\n")
                outfile.write("xbase " + '{:f}'.format(a) + "\n")
                outfile.write("euler " + '{:f}'.format(rot) + " 0.0 0.0\n\n")

                # Append the well shape to use with bioshield cell definitions
                det_outers.append("+well_" + str(d))

            elif det_type.well_type != "none":
                print("Warning: well type must be wedge or none." +
                      " Assuming no detector well.")

        return det_outers

###############################################################################

    def _write_detector_cells(self, outfile):
        # Loop over the detectors
        for d in range(len(self.det_label_locs)):
            # Get the type for this detector
            for dt in self.det_type_list:
                if dt.label == self.det_label_locs[d]:
                    det_type = dt

            # Write out a cell for each radius and height
            label_num = 0
            det_outer = ""
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
                                    exit(1)
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
                    elif r == det_type.radii[-1]:
                        det_outer += \
                            " +detector_" + str(d) + "_" + str(label_num)
                    label_num += 1
            # Write out the cell for each detector well
            if det_type.well_type == "wedge":
                # Write out the well cell
                outfile.write("! Detector " + str(d) + " well shape\n")
                outfile.write("[UNIVERSE][CELL " + " well_" + str(d) + "]\n")
                outfile.write("comp void\n")
                outfile.write("shapes " + "-well_" + str(d) + det_outer + " \n\n")

            elif det_type.well_type != "none":
                print("Warning: well type must be wedge or none." +
                      " Assuming no detector well.")


###############################################################################

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

###############################################################################

    def _get_template_materials(self):
        # Read in the Omnibus template file
        with open(self.template_file, 'r') as temp_file:
            self.materials = re.findall(r'^\[COMP\]\[MATERIAL\s+([\w.-]+)',
                    temp_file.read(), re.M)

###############################################################################

    def update_vera_xml(self):
        if len(self.tally_cells) == 0:
            return

        # See if we have hybrid tally names and multipliers, core translate,
        # and the excore filename
        xml_hybrid_tally = None
        xml_hybrid_mult  = None
        xml_translate    = None
        xml_excore_file  = None
        xml_vera_pv      = None
        for shift_child in self.xml_shift:
            if shift_child.attrib['name'] == 'hybrid_tally_names':
                xml_hybrid_tally = shift_child
            if shift_child.attrib['name'] == 'hybrid_multiplier_names':
                xml_hybrid_mult = shift_child
            if shift_child.attrib['name'] == 'core_translate':
                xml_translate = shift_child
            if shift_child.attrib['name'] == 'excore_filename':
                xml_excore_file = shift_child
            if shift_child.attrib['name'] == 'vera_pressure_vessel':
                xml_vera_pv = shift_child

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

            etree.SubElement(
                    self.xml_shift,  'Parameter',
                    attrib={'name':  'hybrid_multiplier_names',
                            'type':  'Array(string)',
                            'value': tally_mults})

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
                etree.SubElement(
                        self.xml_shift,  'Parameter',
                        attrib={'name':  'hybrid_multiplier_names',
                                'type':  'Array(string)',
                                'value': tally_mults})
            else:
                xml_hybrid_mult.set('value', tally_mults)

        # If core_translate was not given in the VERA input,
        # we need to add it.
        if xml_translate == None:
            translate_string = '{' + ','.join(map(str, self.translate)) + '}'
            etree.SubElement(
                    self.xml_shift, 'Parameter',
                    attrib={'name':  'core_translate',
                            'type':  'Array(double)',
                            'value': translate_string})

        # If excore_filename was not given in the VERA input,
        # we need to add it.
        if xml_excore_file == None:
            etree.SubElement(
                    self.xml_shift,  'Parameter',
                    attrib={'name':  'excore_filename',
                            'type':  'string',
                            'value': self.xml_excore_file})
        if xml_vera_pv == None:
            etree.SubElement(
                    self.xml_shift, 'Parameter',
                    attrib={'name':  'vera_pressure_vessel',
                            'type':  'bool',
                            'value': self.vera_pv})
        for hybrid_db in self.xml_shift:
            if hybrid_db.attrib['name'] == 'hybrid_db':
                if xml_excore_file == None:
                    etree.SubElement(
                            hybrid_db, 'Parameter',
                            attrib={'name':  'excore_filename',
                                    'type':  'string',
                                    'value': self.xml_excore_file})
                if xml_vera_pv == None:
                    etree.SubElement(
                            hybrid_db, 'Parameter',
                            attrib={'name':  'vera_pressure_vessel',
                                    'type':  'bool',
                                    'value': self.vera_pv})

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
