
#include <sys/stat.h>
#include <iomanip>

#include "VERAIn_XML_Utils.hpp"
#include "VERAIn_XML_Common.hpp"

#include "Teuchos_CommandLineProcessor.hpp"
#include "Teuchos_ParameterList.hpp"
#include "Teuchos_XMLParameterListHelpers.hpp"
#include "Teuchos_DefaultComm.hpp"


using namespace std;
using namespace Teuchos;




namespace
{

  // assembly data structure
  struct assem_struct{
     int     assemrods;
     int     nrodsrow;
     int     assemgt;
     double  activelen;
     double  active_start;
     double  bundlepitch;
     int     wallflag;
     int     heater_types;
     int     nc;
     double  *c_ptr_to_pelletd;
     int     pelletnodes;
     double  *c_ptr_to_cladid;
     double  *c_ptr_to_cladod;
     double  rodpitch;
     double  *c_ptr_to_thdensity;
     double  hgap;
     double  *c_ptr_to_gt_wr_di;
     double  *c_ptr_to_gt_wr_de;
     int     *c_ptr_to_gt_wr_posx;
     int     *c_ptr_to_gt_wr_posy;
     int     n_grids;
     double  *c_ptr_to_gridstart;
     double  *c_ptr_to_gridend;
     double  *c_ptr_to_gridloss;
  };

  // control data structure
  struct cntrl_struct{
     char   title[90];
     char   decktitle[90];
     bool   run_parallel;
     char   vtk_hdf5_titles[30];
     int    spec_titles;
     int    num_pf_files;
     int    icobra;
     double epso;
     int    oitmax;
     int    iitmax;
     double courant;
     int    rfmod;
     int    entmod;
     int    mixmod;
     int    solver;
     double ginit;
     double trinit;
     double pref;
     double hin;
     double hgin;
     double dhfrac;
     int    ibound;
     int    obound;
     double gtot;
     double enth_bound_1;
     double enth_bound_2;
     double p_bound_1;
     double p_bound_2;
     int    notrans;
     double dtmin;
     double dtmax;
     double tend;
     double rtwfp;
     int    maxits;
     double gmp;
     double gep;
     double fsp;
     double ssp;
     double msp;
     int    edit_channels;
     int    edit_gaps;
     int    edit_rods;
     int    edit_dnb;
     int    edit_hdf5;
     int    edit_convergence;
     int    restart;
     char   restart_name[90];
     int    boil_ht_cor;
     int    property_evaluations;
     double k_void_drift;
     double beta_sp;
     double *c_ptr_to_inlet_temp;
     double *c_ptr_to_inlet_flow;
  };

  // geo data structure
  struct geo_struct{
     int    nassem;
     int    tf;
     int    n_assem_col;
     int    n_assem_row;
     bool   model_shroud;
     double shroud_gap;
     int    sym_opt;
     int    *c_ptr_to_core_shape;
     int    ivar;
     double *c_ptr_to_ztop;
     int    *c_ptr_to_zondx;
     char   fname[50];
  };

  // power data structure
  struct power_struct{
     double *c_ptr_to_power_dat_time;
     double *c_ptr_to_corepower;
     int    mnxn;
     double *c_ptr_to_y;
     double *c_ptr_to_axialz;
     double *c_ptr_to_assempf;
     int    num_pf_maps;
     int    *c_ptr_to_assempf_map;
     double *c_ptr_to_local_pf;
  };

  // Some input file creation methods corresponding to current (10-3-2012) cobra preprocessor requirements
  assem_struct create_file_assembly_info(Array<double> & fuel_pin_map, VERAIn_XML_Common &);
  cntrl_struct create_file_control_inp(ParameterList &, int, string);
  geo_struct create_file_geo_inp(ParameterList &, int);
  power_struct create_file_power_inp(const Array<double> & fuel_pin_map, VERAIn_XML_Common &);


  // Pointers will be assigned to this data in sub-functions
  // The pointers are passed to preproc, so this data must be global
  // so when the pointers are passed CTF, the data is still valid
  double pelletd;
  double cladod;
  double cladid;
  double avg_thden = 0.0;
  vector<int> gt_wr_posx;
  vector<int> gt_wr_posy;
  double gt_wr_de;
  double gt_wr_di;
  vector<double> gridstart;
  vector<double> gridend;
  vector<double> gridloss;
  Array<int> core_shape;
  Array<double> geo_edit_bounds;
  Array<int> zondx;
  Array<double> power_dat_time;
  Array<double> corepower;
  Array<double> y;
  Array<double> axialz;
  Array<double> assempf;
  Array<int>    assempf_map;
  Array<double> local_pf;
  Array<double> inlet_f;
  Array<double> inlet_t;

}

// The interface routines for passing data into lib_ctf_pp
extern "C" {
   void run_ctf_preproc(geo_struct*,cntrl_struct*,assem_struct*,power_struct*);
}

// -------------------------------------------------------------
template< typename T> void GetOptional(const ParameterList & pList,
                                       const string        & name,
                                             T             & value,
                                             bool            print=true)
{
    if (pList.isParameter(name)) {
        value = pList.getEntry(name).getValue(&value);
        if(print) cout << setw(25) << name <<": (defined): "<<std::left << value <<std::right <<endl;
    } else {
        if(print) cout << setw(25) << name <<": (DEFAULT): "<<std::left << value <<std::right <<endl;
    }
}
// -------------------------------------------------------------
template< typename T> void GetRequired(const ParameterList & pList,
                                       const string        & block,
                                       const string        & name,
                                             T             & value,
                                             bool            print=true)
{
    if (pList.isParameter(name)) {
        value = pList.getEntry(name).getValue(&value);
        if(print) cout << setw(25) << name <<": (defined): "<<std::left << value <<std::right <<endl;
    } else {
        throw runtime_error("ERROR: the "+name+" parameter is required to be on the "+block+" block of the xml input.");
    }
}
// -------------------------------------------------------------

int main(int argc, char**argv)
{
  // Create Cobra preprocessor input files from scratch (not from tagged template files)

  CommandLineProcessor clp;

  string vera_xml_file     = "vera.xml";
  string inp_file          = "deck.inp";
  clp.setOption( "xmlfile", &vera_xml_file, "Filename for Master Reactor Aware XML file. Default is \"vera.xml\"" );
  clp.setOption( "inpfile", &inp_file, "Name of the CTF Input File produced by xml2ctf. Default is \"deck.inp\"" );
  CommandLineProcessor::EParseCommandLineReturn parse_return = clp.parse(argc,argv);
  if( parse_return != CommandLineProcessor::PARSE_SUCCESSFUL )
    return parse_return;

  VERAIn_XML vera_xml(vera_xml_file);
  VERAIn_XML_Common vera_common(vera_xml);
  ParameterList & pList = vera_common.get_vera_xml().get_pList();

  // print values used.
  cout << "\n\nParameters used :" << endl;

  assem_struct assem_data;
  geo_struct geo_data;
  power_struct power_data;
  cntrl_struct cntrl_data;

  // calculate number of assemblies in core
  // only count non-zero entries in core shape map
  const ParameterList & coreParams = pList.sublist("CORE");
  GetRequired(coreParams, "CORE", "shape", core_shape);
  int core_total_size = core_shape.size();   // NxN

  int num_assm = 0;
  for( int k = 0; k < core_total_size; ++k ){
     if( core_shape[k] == 1 ){
        num_assm++;
     }
  }

  // control.inp
  cntrl_data=create_file_control_inp(pList, num_assm, inp_file);

  // geo.inp
  geo_data=create_file_geo_inp(pList, num_assm);

  // Assembly spec file
  Array<double> fuel_pin_map;
  assem_data=create_file_assembly_info(fuel_pin_map, vera_common);

  //  power.inp
  power_data=create_file_power_inp(fuel_pin_map, vera_common);

  // Execute the lib_ctf_pp routines needed to build the maps and write the CTF deck
  run_ctf_preproc(&geo_data,&cntrl_data,&assem_data,&power_data);

  return 0;
}

// -------------------------------------------------------------
//     Produce the assembly file for the COBRA pre-processor
// -------------------------------------------------------------

namespace {

  assem_struct create_file_assembly_info(Array<double> & fuel_pin_map, VERAIn_XML_Common & vera_common)
  {
    VERAIn_XML vera_xml = vera_common.get_vera_xml();
    ParameterList & pList = vera_common.get_vera_xml().get_pList();
    const ParameterList & editsParams = pList.sublist("EDITS");
    const ParameterList & assembliesParams = pList.sublist("ASSEMBLIES");
    const ParameterList & coreParams = pList.sublist("CORE");
    const ParameterList & cobraParams = pList.sublist("COBRATF");

    Array<double> edit_bounds;
    GetRequired(editsParams, "EDITS", "axial_edit_bounds", edit_bounds, false);

    double apitch;
    GetRequired(coreParams,"CORE","apitch", apitch);

    double hgap=5678.3;
    GetOptional(cobraParams, "hgap", hgap);

    int nfuel=10;           // on 1/14/2015 - update default "nfuel" from 3 to 10 - see #3356
    GetOptional(cobraParams, "nfuel", nfuel);

    int ctf_debug=0;        // debut edits
    GetOptional(cobraParams, "debug", ctf_debug);

    int ctfnc=1;
    GetOptional(cobraParams, "nc", ctfnc);

    assem_struct assem_data;

    const double grid_geom_tol = 1.e-5; // hard-coded for now

    int     save_num_pins=-1;          // save values to check that all assemblies are consistent
    double  save_ppitch  =-1.0;
    double  save_fuel_od =-1.0;
    double  save_clad_od =-1.0;
    double  save_clad_id =-1.0;
    double  save_guide_od =-1.0;
    double  save_guide_id =-1.0;

    double conversion_cm2mm  = 10.0;  // convert cm to mm
    double tol_geom          = 0.001;  // geometry tolerance (cm)

    ParameterList * param_list = &pList;


  // Check that axial edit bounds are in increasing order
     size_t num_edit  = edit_bounds.size();
     for( size_t ii = 1; ii < num_edit; ++ii )
        if( edit_bounds[ii-1] >= edit_bounds[ii] )
          throw runtime_error("ERROR: Axial edit bounds are not in increasing order");

  // ---------------------------------------------------------------------------------------------------
  //    Loop over all assemblies
  //    fix - should loop over all assemblies in "assm_map" instead of assemblies found on file
  // ---------------------------------------------------------------------------------------------------
    
    // Get Assemblies
    ParameterList::ConstIterator citer = assembliesParams.begin(),
                                 c_end = assembliesParams.end();
    for( ; c_end != citer; ++citer )
    {
      const ParameterEntry & entry = assembliesParams.entry(citer);
      // Are there any other sublists under "ASSEMBLIES" besides Assemblies_XXX ? - RWH
      string data = assembliesParams.name(citer);
      std::transform(data.begin(), data.end(), data.begin(), ::tolower);
      if( entry.isList() && (data.find("assembly_") == 0) )
      {
        string assembly_name = assembliesParams.name(citer);
        string assembly_ppath = "ASSEMBLIES." + assembly_name;

        cout << "\n Reading assembly: " << assembly_name << endl;

    // -----------------------------------------------------------------
    //
    // Obtain cell attributes to be used later
    //
    // Assumptions:
    //   Clad OD is the outer radii
    //   Clad ID is the next to outer radii
    //   Fuel OD is the outermost radii with fuel material  
    //   (this logic will work with IFBA and annular fuel and addresses ticket #3578)
    //
    // Fuel cells:        (type "fuel")
    // Fuel cells are defined by the "type" on the XML file
    // Check all fuel cells to make sure they have consistent Clad_OD, Clad_ID, and Fuel_ID
    // Values for the fuel region are stored in save_fuel_od, save_clad_od, and save_clad_id
    //
    // Guide tube cells:  (type "tube")
    // Guide tube cells are defined if the inner region of the cell contains "mod"
    // Check all guide tube cells to make sure they have consistent Clad_OD, Clad_ID
    // But only perform this check in axial regions with fuel!
    // Note that some empty locations in the plenum will inadvertently be labeled as "tube"
    //
    // Other cells:       (type ("other)
    // These are defined as not fuel and not guide tubes.  They can be plenum, plug, BPR, etc.
    // Check that "other" cells have clad dimensions consistent with fuel
    // But only perform this check in axial regions with fuel!
    // No checks are performed on axial regions without fuel because we might have empty regions
    // and/or plugs
    //
    // Also collect values of "thden" by cell type for averaging later
    //
    // -----------------------------------------------------------------

        map<string, string> cell_types;
        map<string, Array<double> > cell_radii;
        map<string, Array<string> > cell_mats;
        map<string, int> cell_num_rings;
        map<string, double> cell_clad_od;
        map<string, double> cell_clad_id;
        map<string, double> cell_fuel_od;
        map<string, double> cell_thden;
        const ParameterList & assem_cells_plist = assembliesParams.sublist(assembly_name).sublist("Cells");
        ParameterList::ConstIterator assem_cell_citer = assem_cells_plist.begin(),
          assem_cell_cend  = assem_cells_plist.end();
        for( ; assem_cell_cend != assem_cell_citer; ++assem_cell_citer )
        {
          // Are there any other sublists besides "Cell_XXX" under "ASSEMBLIES.Assemblies_XXX.Cells" ? - RWH
          data = assem_cells_plist.name(assem_cell_citer);
          std::transform(data.begin(), data.end(), data.begin(), ::tolower);
          if( assem_cells_plist.entry(assem_cell_citer).isList() &&  // is it a sublist
              (data.find("cell_") == 0) ) // and is it named "Cell_XXX"
          {
            string cell_name = assem_cells_plist.name(assem_cell_citer);
            string ppath_cell_type = assembly_ppath+".Cells."+cell_name+".type";
            string cell_type = vera_xml.get_param_from_plist<string>( ppath_cell_type);
            cell_types[cell_name] = cell_type;
            ppath_cell_type = assembly_ppath+".Cells."+cell_name+".radii";
            cell_radii[cell_name] = vera_xml.get_param_from_plist<Array<double> >( ppath_cell_type);
            ppath_cell_type = assembly_ppath+".Cells."+cell_name+".mats";
            cell_mats[cell_name] = vera_xml.get_param_from_plist<Array<string> >( ppath_cell_type);
            ppath_cell_type = assembly_ppath+".Cells."+cell_name+".num_rings";
            cell_num_rings[cell_name] = vera_xml.get_param_from_plist<int>( ppath_cell_type);

            if ( cell_num_rings[cell_name] > 0 )
            {
              cell_clad_od[cell_name]=cell_radii[cell_name][cell_num_rings[cell_name]-1];
            }
            else
            {
              cell_clad_od[cell_name]=0.0;
            }

            if ( cell_num_rings[cell_name] > 1 )
            {
              cell_clad_id[cell_name]=cell_radii[cell_name][cell_num_rings[cell_name]-2];
            }
            else
            {
              cell_clad_id[cell_name]=0.0;
            }

    // check if this cell is a fuel cell

            cell_thden[cell_name]=0.0;   // initialize in case search doesn't work
            cell_fuel_od[cell_name]=0.0;
            if( "fuel" == cell_type )
            {
              int ifr=-2;
              // Now figure out which material is the fuel and get its thden value for averaging
              string cell_mats_path = assembly_ppath+".Cells."+cell_name+".mats";
              Array<string> cell_mats = vera_xml.get_param_from_plist<Array<string> >( cell_mats_path);
              for( unsigned m = 0; m < cell_mats.size(); ++m )    // loop over materials
              {
  // debug      cout << " cell mats: " << m << " " << cell_mats[m] << endl;
                string mats_path = assembly_ppath+".Fuels.Fuel_"+cell_mats[m];
                if( vera_xml.is_sublist(*param_list, mats_path) )
                {
                  ifr=m;      // save last ring number with fuel
                  cell_thden[cell_name] = vera_xml.get_param_from_plist<double>( mats_path+".thden");
                }
              }
              if (ifr < 0)
              {
                throw runtime_error("No fissionable material found in fuel cell");
              }
              else
              {
                cell_fuel_od[cell_name]=cell_radii[cell_name][ifr];
              }

              if (save_clad_od < 0.0 )
                 save_clad_od=cell_clad_od[cell_name];
              if (save_clad_id < 0.0 )
                 save_clad_id=cell_clad_id[cell_name];
              if (save_fuel_od < 0.0 )
                 save_fuel_od=cell_fuel_od[cell_name];

              if ( abs(save_fuel_od-cell_fuel_od[cell_name]) > tol_geom)
              {
                 cout << "ERROR: fuel outer radii is not consistent with other fuel cells" << endl;
                 cout << "   cell name       " << cell_name                   << endl;
                 cout << "   fuel_od in cell " << cell_fuel_od[cell_name]     << endl;
                 cout << "   expecting       " << save_fuel_od                << endl;
                 throw runtime_error("Invalid outer fuel radii");
              }

              if ( abs(save_clad_id-cell_clad_id[cell_name]) > tol_geom)
              {
                 cout << "ERROR: clad inner radii is not consistent with other fuel cells" << endl;
                 cout << "   cell name       " << cell_name                   << endl;
                 cout << "   clad_id in cell " << cell_clad_id[cell_name]     << endl;
                 cout << "   expecting       " << save_clad_id                << endl;
                 throw runtime_error("Invalid clad inner radii");
              }

              if ( abs(save_clad_od-cell_clad_od[cell_name]) > tol_geom)
              {
                 cout << "ERROR: clad Outer radii is not consistent with other fuel cells" << endl;
                 cout << "   cell name       " << cell_name                   << endl;
                 cout << "   clad_od in cell " << cell_clad_od[cell_name]     << endl;
                 cout << "   expecting       " << save_clad_od                << endl;
                 throw runtime_error("Invalid clad outer radii");
              }

            }  // end check on fuel cells

    // check if this cell is a guide tube  (has "mod" in the inner region)

            if( "other" == cell_type )
            {
              // figure out if inside material is "mod"
              string cell_mats_path = assembly_ppath+".Cells."+cell_name+".mats";
              Array<string> cell_mats = vera_xml.get_param_from_plist<Array<string> >( cell_mats_path);
              if ("mod" == cell_mats[0])
              {
            //  cout << "  cell guide tube " << cell_name << endl;
                cell_type="tube";
                cell_types[cell_name]=cell_type;

            // it would be nice to check all the guide tube dimensions here, but
            // we can't distinguish guide tubes from "missing" regions in the plenum

              }

            }  // end check for guide tube cells

    // edit cell debug information

            if (ctf_debug > 0)
            {
              cout << "  cell debug: Cell " << cell_name << " Type: " << cell_type << endl;
              cout << "  cell debug:    num rings   "<< cell_num_rings[cell_name] << endl;
              cout << "  cell debug:    radii       "<< cell_radii[cell_name]     << endl;
              cout << "  cell debug:    fuel/clad radii  " << cell_fuel_od[cell_name]
                                                    << " " << cell_clad_id[cell_name]
                                                    << " " << cell_clad_od[cell_name] << endl;
              cout << "  cell debug:    thden       "<< cell_thden[cell_name]     << endl;
            }
      
          }   // end loop over cells
        }

    // checks to make sure all assemblies are consistent

        int    num_pins= vera_xml.get_param_from_plist<int>( assembly_ppath+".num_pins");
        double ppitch = vera_xml.get_param_from_plist<double>( assembly_ppath+".ppitch");   // cm

        if ( save_num_pins < 0 )
        {
          save_num_pins=num_pins;    // save values for first assembly encountered
        }
        else if (save_num_pins != num_pins )
        {
          throw runtime_error("Number of fuel pins is not the same in every assembly");
        }

        if ( save_ppitch < 0.0 )
        {
          save_ppitch=ppitch;    // save values for first assembly encountered
        }
        else if ( abs(save_ppitch-ppitch) > tol_geom )
        {
          throw runtime_error("Pin Pitch is not the same in every assembly");
        }

    // ---------------------------------------------------------------------------------------------------
    //  Step 1. Loop over all axial levels (i.e. number of \"axial_labels\" in assembly)
    //          and determine if axial level has fuel or not
    //
    //          Average thden in this loop because we evaluate every level
    //          In the next step, we will skip duplicate levels
    // ---------------------------------------------------------------------------------------------------

        Array<string> axial_labels = vera_xml.get_param_from_plist<Array<string> >( assembly_ppath+".axial_labels");

        map<string, bool> axial_level_done;

        const double bottom_active_fuel = vera_common.get_bottom_active_fuel_in_cm(assembly_name);
        const double model_bottom = edit_bounds[0];
        avg_thden=0.0;


        Array<double> axial_elevations = vera_xml.get_param_from_plist<Array<double> >( assembly_ppath+".axial_elevations");
        map<string, bool> axial_levels_with_fuel;

        // Loop over axial levels
        // CTF requires one value of thden, so do a crude averaging
        // We could improve this by doing volume weighting

        for( unsigned i = 0; i < axial_labels.size(); ++i )
        {
          axial_level_done[axial_labels[i]] = false;
          double axial_level_length = axial_elevations[i+1] - axial_elevations[i];
          double axial_avg_thden = 0.0;

          // Loop over cell map at this axial level

          string PL_entry = "ASSEMBLIES." + assembly_name + ".CellMaps.CellMap_" + axial_labels[i] + ".cell_map";
          Array<string> cell_map = vera_xml.get_param_from_plist<Array<string> >( PL_entry);
          bool axial_level_has_fuel = false;
          double num_fuel_pins = 0;
          for( int j = 0; j < cell_map.size(); ++j )
          {
            string cell_name = "Cell_" + cell_map[j];
            string cell_type = cell_types[cell_name];
            if( "fuel" == cell_type )
            {
              axial_level_has_fuel = true;
              num_fuel_pins++;
              axial_avg_thden += cell_thden[cell_name];
            }
          }
          if( axial_level_has_fuel )
          {
            //cout << "Axial label \"" << axial_labels[i] << "\" has fuel." << endl;
            axial_levels_with_fuel[axial_labels[i]] = true;
            axial_avg_thden /= (double) num_fuel_pins;
            avg_thden += axial_avg_thden*axial_level_length;
            //cout << "... including " << axial_avg_thden << " in running thden average." << endl;
          }
          else
          {
            axial_levels_with_fuel[axial_labels[i]] = false;
            //cout << "Axial label \"" << axial_labels[i] << "\" DOES NOT have fuel." << endl;
          }
        }

        double active_fuel_length = vera_common.get_total_fuel_length_in_cm(assembly_name);
        avg_thden /= active_fuel_length;


    // ---------------------------------------------------------------------------------------------------
    //  Step 2. Loop over all axial levels (i.e. number of \"axial_labels\" in assembly)
    //          and for each axial label, loop over npin x npin \"cell_map\"
    //
    //          Skip duplicate levels and non-fueled levels
    //
    //  Notes on error checking:
    //
    //    Rod dimensions have already been checked for "fuel" and "tube" cells
    //    Rod dimensions for "other" cells are only checked in axial levels with fuel.
    //
    //    We cannot check Non-fueled axial levels because the non-fuel cells might be plenums or empty location.
    //    (The only way to improve this is to do an axial sweep of each rod, which we may have to implement)
    //
    //    Note that this logic will not work for BWR's with part length fuel, but
    //    our current CTF input processor can't handle this anyway
    //
    // ---------------------------------------------------------------------------------------------------

        int num_axial_levels = axial_labels.size();
        set<string> fuel_type_ids;                        // save locations for guide tube search
        vector<int> num_fuel_rods(num_axial_levels);
        vector<int> num_non_fuel_rods(num_axial_levels);
        int heated_elements_type;

        // For multiple axial fuels, we need to output only a single set of information to cobra.
        // For now, we use to first pass through.  We should allow additional passes to happen for the
        // purpose of verifying consistency among values that should agree.
        bool first_level = true;
        bool first_assm  = true;

        vector<string> fuels_material_ids;

        for( unsigned i = 0; i < axial_labels.size(); ++i )
        {
          cout << "  axial level: " << i << " " << axial_labels[i] << endl;

          if( !axial_levels_with_fuel[axial_labels[i]] )
          {
            cout << "    non-fuel lattice" << endl;
            continue;     // skip this axial level
          }

          if( axial_level_done[axial_labels[i]] )
          {
            // Do consistency checks ...
            cout << "    duplicate lattice" << endl;
            continue;     // skip this axial level
          }

          string PL_entry = "ASSEMBLIES." + assembly_name + ".CellMaps.CellMap_" + axial_labels[i] + ".cell_map";
          Array<string> cell_map = vera_xml.get_param_from_plist<Array<string> >( PL_entry);

          // Sanity check
          if( num_pins*num_pins != cell_map.size() )
            throw runtime_error("Cell Map for Assembly \""+assembly_name+" does not have correct number of pins.");

          map<string, int> rod_type_counts;

          for( int j = 0; j < cell_map.size(); ++j ){
             rod_type_counts[cell_map[j]]++;
          }

          // Obtain fuel pin tally
          // There are three types of cell at this point - "fuel", "tube", or "other"
          map<string, int>::const_iterator citer = rod_type_counts.begin();
          for( size_t j = 0; j < rod_type_counts.size(); ++j, ++citer )
          {
            string cell_name = "Cell_" + citer->first;
            string cell_type = cell_types[cell_name];
            if( "tube" == cell_type )
            {
              num_non_fuel_rods[i] += citer->second;
            }
            else     // either "fuel" or "other".  ("other" could be BPR)
            {
              num_fuel_rods[i] += citer->second;
              fuel_type_ids.insert(citer->first);
              cout << "    found fuel cell \"" << cell_name << "\"" << endl;
            }

           // check dimensions of guide tubes to make sure they are consistent
           // We only perform this check in axial levels that have fuel because
           // there might be plugs and/or empty regions.

            if( "tube" == cell_type )
            {
               if (save_guide_od < 0.0 )
                   save_guide_od=cell_clad_od[cell_name];    // save dimensions for first guide tube found
                if (save_guide_id < 0.0 )
                   save_guide_id=cell_clad_id[cell_name];

                if ( abs(save_guide_id-cell_clad_id[cell_name]) > tol_geom)
                {
                   cout << "ERROR: guide tube inner clad radii is not consistent with other guide tube cells" << endl;
                   cout << "   cell name       " << cell_name                   << endl;
                   cout << "   clad_id in cell " << cell_clad_id[cell_name]     << endl;
                   cout << "   expecting       " << save_guide_id               << endl;
                   throw runtime_error("Invalid guide tube inner clad radii");
                }

                if ( abs(save_guide_od-cell_clad_od[cell_name]) > tol_geom)
                {
                   cout << "ERROR: guide tube outer clad radii is not consistent with other guide tube cells" << endl;
                   cout << "   cell name       " << cell_name                   << endl;
                   cout << "   clad_od in cell " << cell_clad_od[cell_name]     << endl;
                   cout << "   expecting       " << save_guide_od               << endl;
                   throw runtime_error("Invalid guide tube outer clad radii");
                }
            }

           // check dimensions of "other" rods to make sure they match fuel
           // We only perform this check in axial levels that have fuel because
           // there might be plugs and/or empty regions.

            if( "other" == cell_type )
            {
              if ( abs(save_clad_od-cell_clad_od[cell_name]) > tol_geom)
              {
                 cout << "ERROR: Outer radii of cell is not consistent with other fuel cells" << endl;
                 cout << "   cell name       " << cell_name                   << endl;
                 cout << "   clad_od in cell " << cell_clad_od[cell_name]     << endl;
                 cout << "   expecting       " << save_clad_od                << endl;
                 throw runtime_error("Invalid clad outer radii in fuel region");
              }
            }

          }

          if( num_pins*num_pins != (num_fuel_rods[i]+num_non_fuel_rods[i]) )
            throw runtime_error("Num fuel rods ("+vera_xml.convert_value_to_string(num_fuel_rods[i])+") "
                + "+ Num non-fuel rods (" + vera_xml.convert_value_to_string(num_non_fuel_rods[i])+") "
                + "!= Num pins for Assembly \""+assembly_name+"\" ("+ vera_xml.convert_value_to_string(num_pins*num_pins) + ").");

          cout << "    number of fuel rods and guide tubes " << num_fuel_rods[i] <<" " << num_non_fuel_rods[i] << endl;

          if( first_level && first_assm )
          {
            assem_data.assemrods = num_fuel_rods[i];
            assem_data.nrodsrow = num_pins;
            assem_data.assemgt = num_non_fuel_rods[i];
            assem_data.activelen = active_fuel_length*conversion_cm2mm;
            assem_data.active_start = (bottom_active_fuel-model_bottom)*conversion_cm2mm;
            assem_data.bundlepitch = apitch*conversion_cm2mm;

            assem_data.wallflag = 0;
            heated_elements_type = vera_xml.get_param_from_plist<int>( "COBRATF.heated_elements_type", 0, false);
            assem_data.heater_types = heated_elements_type;
            assem_data.nc = ctfnc;

          }
          else
          {
            // fix - add checks to make sure all assemblies are the same
            //   * same number of fuel rods
            //   * same size of fuel array
            //   * same number of guide tubes
            //   * same clad od, clad id, fuel pellet diameters
            // Not all assemblies have the same number of fuel rods
            // This will throw an error for B&W/SMR case with BP rods in fuel locations
            //
            if( num_fuel_rods[i] != assem_data.assemrods )
                throw runtime_error("Num fuel rods is not consistent among all axial levels of Assembly \""+assembly_name+"\".");
            if( num_non_fuel_rods[i] != assem_data.assemgt )
                throw runtime_error("Num non-fuel rods is not consistent among all axial levels of Assembly \""+assembly_name+"\".");
            continue;
          }

    //----------------------------------------------------------------------------------------
    //  The following will only be run for first_level and first_assm because of the continue statement in the else clause
    //----------------------------------------------------------------------------------------

          if( first_level && first_assm )
          {

            if( 1 == heated_elements_type ) // 0=Nuclear Fuel Rods, 1=Electric Heater Tubes
            {
               cladid = vera_xml.get_param_from_plist<double>("COBRATF.heater_tube_id")*conversion_cm2mm;
               assem_data.c_ptr_to_cladid = &cladid;
               cladod = vera_xml.get_param_from_plist<double>("COBRATF.heater_tube_od")*conversion_cm2mm;
               assem_data.c_ptr_to_cladod = &cladod;
               assem_data.rodpitch =vera_xml.get_param_from_plist<double>("COBRATF.heater_tube_pitch")*conversion_cm2mm;
            }
            else
            {

      // Note that it is possible to define multiple fuel rod types
      // If this is the case, enter the following block for each fuel rod type
      // and precede each block with a number in brackets, e.g.  {1}, {2}, etc.

               pelletd=2.0*save_fuel_od * conversion_cm2mm;
               assem_data.c_ptr_to_pelletd = &pelletd;
               assem_data.pelletnodes = nfuel;
               cladid = 2.0*save_clad_id * conversion_cm2mm;
               cladod = 2.0*save_clad_od * conversion_cm2mm;
               assem_data.c_ptr_to_cladid = &cladid;
               assem_data.c_ptr_to_cladod = &cladod;
               assem_data.rodpitch = ppitch*conversion_cm2mm;
               assem_data.c_ptr_to_thdensity = &avg_thden;
               assem_data.hgap = hgap;

            }

       // The previous section collected radii, etc. for fuel pins
       // Do the same thing for non-fuel pins (i.e. guide tubes)
       // Again, it is possible to define multiple guide tube types here, but we don't do it

            fuel_pin_map.resize(num_pins*num_pins);
            if( num_non_fuel_rods[i] == 0 )
            {
              // All pins are fuel pins
              for( int k = 0; k < num_pins; ++k )
                for( int m = 0; m < num_pins; ++m )
                  fuel_pin_map[k*num_pins+m] = 1.0;

              gt_wr_di=0.0;
              gt_wr_de=0.0;
              assem_data.c_ptr_to_gt_wr_di=&gt_wr_di;
              assem_data.c_ptr_to_gt_wr_de=&gt_wr_de;
            }
            else
            {

              gt_wr_di = 2.0*save_guide_id * conversion_cm2mm;
              gt_wr_de = 2.0*save_guide_od * conversion_cm2mm;

              assem_data.c_ptr_to_gt_wr_di = &gt_wr_di;
              assem_data.c_ptr_to_gt_wr_de = &gt_wr_de;

              // I'll simply sweep over all pin cells and assume non-fuel entries are guide tubes... - RWH
              // Also, I'll assume we start in the bottom-left and sweep up first then right.

              gt_wr_posx.resize(assem_data.assemgt);
              gt_wr_posy.resize(assem_data.assemgt);
              int gt = 0;
              for( int k = 0; k < num_pins; ++k ){
                 for( int m = 0; m < num_pins; ++m ){
                    string cell_name = "Cell_" + cell_map[k*num_pins+m];
                    string cell_type = cell_types[cell_name];
                    if ("tube" == cell_type)
                    {
                       gt_wr_posx.at(gt) = k+1;
                       gt_wr_posy.at(gt) = m+1;
                       gt = gt + 1;
                       fuel_pin_map[k*num_pins+m] = 0.0;
                    }
                    else
                    {
                       fuel_pin_map[k*num_pins+m] = 1.0;
                    }
                 }
              }

              //cout << gt_wr_posx << endl;
              //cout << gt_wr_posy << endl;
              //for(vector<int>::const_iterator z=gt_wr_posx.begin(); z!=gt_wr_posx.end(); z++)
              //   cout << *z << " " << endl;
              assem_data.c_ptr_to_gt_wr_posx = &gt_wr_posx[0];
              assem_data.c_ptr_to_gt_wr_posy = &gt_wr_posy[0];

            }
          }

          axial_level_done[axial_labels[i]] = true;
          first_level = false;
        }   // END LOOP OVER AXIAL LEVELS

   // print final assembly dimensions

        cout << "  Assembly fuel radii " << save_fuel_od << " " << save_clad_id << " " << save_clad_od << " cm" << endl;
        cout << "  Assembly guide tube radii " << save_guide_id << " " << save_guide_od << " cm" << endl;
        cout << "  Assembly lower inactive region " << assem_data.active_start*10.0 << " cm" << endl;
        cout << "  Assembly theoretical density (thden) " << avg_thden << " %" << endl;

   //--------------------------------------------------------------------------------------------
   //
   //  Start Grid Processing
   //
   //  The grid elevations (grid_elev) in the PL are for the midpoints of the grids
   //  In our example, we have two grid types, \"END\" and \"MID\"
   //  Each one has a different height, given in the \"SpacerGrids\" sublist
   //  Use the midpoints and heights to calculate the initial and final heights below.
   //
   //  Remember to convert the heights from cm to mm
   //
   //  Important: In CTF, spacer heights are relative to bottom of active fuel
   //             In PL, elevations are relative to bottom core plate
   //             To convert, subtract the elevation of the bottom of the active fuel (calculated above)
   //                from the grid elevations in the PL
   //--------------------------------------------------------------------------------------------

        Array<double> grid_elev; // default to empty
        Array<string> grid_map; // default to empty
        grid_elev = vera_xml.get_param_from_plist<Array<double> >( assembly_ppath+".grid_elev", grid_elev);
        grid_map = vera_xml.get_param_from_plist<Array<string> >( assembly_ppath+".grid_map", grid_map);
        if( grid_elev.size() != grid_map.size() )
          throw runtime_error("ERROR: Inconsistent number of entries for \"grid_elev\" and \"grid_map\"");

        size_t ngrid_orig = grid_elev.size(); // original number of grids, actual may be lower
        size_t ngrid      = ngrid_orig;       // actual may decrease

        // Check that grids are in increasing order
        for( size_t ii = 1; ii < ngrid; ++ii )
          if( grid_elev[ii-1] > grid_elev[ii] )
            throw runtime_error("ERROR: Grid elevations are not in increasing order");

        // If the grid is above the top axial edit bounds or below the bottom axial edit bounds,
        // just ignore it in the CTF model.
        size_t ng0=0;       // starting grid number
        size_t ng1=ngrid_orig;   // ending grid number
        for( size_t ii = 0; ii < ngrid_orig; ++ii )
        {
          if (grid_elev[ii] < edit_bounds[0])     // both grid and edit_bounds are "unshifted"
          {
            cout << "  grid " << ii+1 << " is less than bottom axial edit bound... ignoring it in CTF model." << endl;
            ng0 = ii+1;
          }
          if (grid_elev[ii] > edit_bounds[num_edit-1])
          {
            cout << "  grid " << ii+1 << " is greater than top axial edit bound... ignoring it in CTF model." << endl;
            ng1 = min(ii,ng1);
          }
        }
        ngrid=ng1-ng0;
        if (ctf_debug > 0)
        {
          cout << " ngrid original value           " << ngrid_orig << endl;
          cout << " ngrid in calculated geometry   " << ngrid << endl;
          cout << " grid starting number           " << ng0 << endl;
          cout << " grid ending number             " << ng1 << endl;
        }

        if ( first_assm )
        {
          assem_data.n_grids = ngrid;     // actual number of grids in geometry
        }
        // else
        //  fix: check grid data for consistency between assemblies

        // --------------------------------------
        // Obtain SpacerGrid types and attributes
        // --------------------------------------
        // We will use the label as the keyname and store the plist name for future reference (may not be needed)
        size_t num_grid_types = 0;
        map<string, string> spacer_grid_plist_name;
        map<string, double> spacer_grid_masses;
        map<string, double> spacer_grid_heights;
        map<string, string> spacer_grid_materials;
        const ParameterList & spacer_grid_plist = pList.sublist("ASSEMBLIES").sublist(assembly_name).sublist("SpacerGrids");
        ParameterList::ConstIterator spacer_grid_citer = spacer_grid_plist.begin(),
          spacer_grid_cend  = spacer_grid_plist.end();
        for( ; spacer_grid_cend != spacer_grid_citer; ++spacer_grid_citer )
        {
          // fix - loop over all defined grid types, not grid types in XML file
          // Are there any other sublists besides "Grid_XXX" under "ASSEMBLIES.Assemblies_XXX.SpacerGrids" ? - RWH
          data = spacer_grid_plist.name(spacer_grid_citer);
          std::transform(data.begin(), data.end(), data.begin(), ::tolower);
          if( spacer_grid_plist.entry(spacer_grid_citer).isList() &&  // is it a sublist
              (data.find("grid_") == 0) ) // and is it named "Grid_XXX"
          {
            num_grid_types++;
            string grid_plist_name = spacer_grid_plist.name(spacer_grid_citer);
            string ppath_spacer_grid = assembly_ppath+".SpacerGrids."+grid_plist_name+".label";
            string spacer_grid_label = vera_xml.get_param_from_plist<string>( ppath_spacer_grid);
            spacer_grid_plist_name[spacer_grid_label] = grid_plist_name;
            ppath_spacer_grid = assembly_ppath+".SpacerGrids."+grid_plist_name+".mass";
            spacer_grid_masses[spacer_grid_label] = vera_xml.get_param_from_plist<double>( ppath_spacer_grid);
            ppath_spacer_grid = assembly_ppath+".SpacerGrids."+grid_plist_name+".height";
            spacer_grid_heights[spacer_grid_label] = vera_xml.get_param_from_plist<double>( ppath_spacer_grid);
            ppath_spacer_grid = assembly_ppath+".SpacerGrids."+grid_plist_name+".material";
            spacer_grid_materials[spacer_grid_label] = vera_xml.get_param_from_plist<string>( ppath_spacer_grid);

            cout << "  grid type " << num_grid_types << " " << spacer_grid_label << endl;
          }
        }

        // Get grid loss info from cobra block; these will be applied to each spacer grid
        Array<string> grid_types;
        grid_types.push_back("MID");
        grid_types.push_back("END");
        Array<double> grid_losses;  // default to empty
        grid_losses.push_back(0.9065);
        grid_losses.push_back(0.9070);
        grid_types = vera_xml.get_param_from_plist<Array<string> >( "COBRATF.gridlabel", grid_types);
        grid_losses = vera_xml.get_param_from_plist<Array<double> >( "COBRATF.gridloss", grid_losses);
        map<string, double> grid_loss_coeffs;
        for( int ii = 0; ii < grid_types.size(); ++ii )
          grid_loss_coeffs[grid_types[ii]] = grid_losses[ii];

        // Sanity check that all grid_map types have a specified loss coefficient
        for( size_t n = 0; n < ngrid_orig; ++n )
          if( grid_loss_coeffs.end() == grid_loss_coeffs.find(grid_map[n]) )
            throw runtime_error("Could not find a loss coefficient spec (in [COBRATF] block) for grid_map type \""+grid_map[n]+"\"");

        int ifgrd1;
        int ifgrd2;
        double half_height;
        double grid1;
        double grid2;
        gridstart.resize(ngrid);
        gridend.resize(ngrid);
        gridloss.resize(ngrid);
        size_t ng=-1;
        for( size_t n=ng0; n<ng1; ++n )    // only loop over grids in actual geometry
        {
          map<string, double>::const_iterator grid_height_citer = spacer_grid_heights.find(grid_map[n]);
          if( grid_height_citer == spacer_grid_heights.end() )
            throw runtime_error("Could not find a height for spacer grid of type \""+grid_map[n]+"\"");
          half_height = grid_height_citer->second * 0.5;
          grid1 = grid_elev[n] - half_height;
          grid2 = grid_elev[n] + half_height;

          // Fix small round-off - grid can't extend below zero
          if(abs(grid1) < grid_geom_tol )
            grid1 = 0.0;

          // check to make sure the grid boundaries are included in the edit bounds
          ifgrd1=-2;
          ifgrd2=-2;
          for( size_t j=0; j< num_edit; ++j )
          {
            if(abs(grid1-edit_bounds[j]) < grid_geom_tol)
              ifgrd1=j;
            if(abs(grid2-edit_bounds[j]) < grid_geom_tol)
              ifgrd2=j;
          }

          if (ctf_debug > 0)
          {
            cout << "  grid level " << n << " " << grid_map[n] << " " << grid_elev[n] << endl;
         // cout << "   ifgrd1    " << ifgrd1 << endl;
         // cout << "   ifgrd2    " << ifgrd2 << endl;
          }

          if (ifgrd1 < 0)
          {
            printf(" Need grid lower elevation %12.6f\n", grid1);
            printf(" Need grid upper elevation %12.6f\n", grid2);
            throw runtime_error("Lower Grid elevation is not found in axial_edit_bounds list");
          }
          if (ifgrd2 < 0)
          {
            printf(" Need grid lower elevation %12.6f\n", grid1);
            printf(" Need grid upper elevation %12.6f\n", grid2);
            throw runtime_error("Upper Grid elevation is not found in axial_edit_bounds list");
          }

          if ( first_assm )
          {
            // Need to format this in order to get perfect textual agreement (for diff comparisons)
            ostringstream oss1, oss2, oss3;
            ng++;
            gridstart.at(ng) = (grid1-model_bottom)*conversion_cm2mm;   // save shifted values
            gridend.at(ng)   = (grid2-model_bottom)*conversion_cm2mm ;
            gridloss.at(ng)  = grid_loss_coeffs[grid_map[n]];

          }
        }
        if (ng+1 != ngrid)
          cout << "debug error ng ngrid " << ng+1 << " " << ngrid << endl;

        first_assm = false;
      }
    }    // END LOOP OVER ASSEMBLIES

    assem_data.c_ptr_to_gridstart = &gridstart[0];
    assem_data.c_ptr_to_gridend   = &gridend[0];
    assem_data.c_ptr_to_gridloss  = &gridloss[0];

    return assem_data;

  }

// -------------------------------------------------------------
//     Produce the control file for the COBRA pre-processor
// -------------------------------------------------------------

  cntrl_struct create_file_control_inp(ParameterList & pList, int num_assm, string inp_file)
  {
    ParameterList cobraParams = pList.sublist("COBRATF");
    ParameterList coreParams = pList.sublist("CORE");
    ParameterList couplingParams = pList.sublist("COUPLING");
    ParameterList stateParams;
    if( pList.isSublist("STATE") ) {
      stateParams = pList.sublist("STATE");
    } else if( pList.isSublist("STATES") ) {
      stateParams = pList.sublist("STATES").sublist("State_1");
    }

    cntrl_struct cntrl_data;

    // title
    string title = "ERROR:  undefined title";
    GetOptional(pList, "case_id", title);
    strcpy(cntrl_data.title,title.c_str());

    int parallel = 0;
    GetOptional(cobraParams, "parallel", parallel);
    cntrl_data.run_parallel = parallel;

    string decktitle = inp_file.erase(inp_file.size()-4); // remove .xml to get base filename
    strcpy(cntrl_data.decktitle,decktitle.c_str());

    string maps_filename = "";
    GetOptional(cobraParams, "maps_filename", maps_filename);
    if (maps_filename.size()>0){
       cntrl_data.spec_titles=1;
    }
    else{
       cntrl_data.spec_titles=0;
    }
    strcpy(cntrl_data.vtk_hdf5_titles,maps_filename.c_str());

    // Read in the inlet flow and temperature maps
    GetOptional(stateParams,"inlet_temp",inlet_t);
    if (inlet_t.size()==0){
       // Map not found, make it all zeros
       inlet_t.resize(num_assm,0.0);
    }
    // Convert inlet temp deltas from F to C
    for(int k=0;k<inlet_t.size();k++){
       inlet_t[k]=inlet_t[k]/1.8;
    }
    cntrl_data.c_ptr_to_inlet_temp=&inlet_t[0];
    GetOptional(stateParams,"inlet_flow",inlet_f);
    if (inlet_f.size()==0){
       // Map not found, make it all ones
       inlet_f.resize(num_assm,1.0);
    }
    cntrl_data.c_ptr_to_inlet_flow=&inlet_f[0];


    // stacked case option
    Array<double> stacked_case_times; // default to empty
    GetOptional(stateParams, "deplete", stacked_case_times);
    int num_pf_files = 1;
    if (stacked_case_times.size()>0) num_pf_files = stacked_case_times.size();
    cntrl_data.num_pf_files = num_pf_files;

    cntrl_data.icobra = 1;
    //defaults:
    cntrl_data.epso    = 0.001;
    cntrl_data.oitmax  = 5;
    cntrl_data.iitmax  = 40;
    cntrl_data.courant = 0.8;
    cntrl_data.rfmod   = 2;
    GetOptional(cobraParams, "epso", cntrl_data.epso);
    GetOptional(cobraParams, "oitmax", cntrl_data.oitmax);
    GetOptional(cobraParams, "iitmax", cntrl_data.iitmax);
    GetOptional(cobraParams, "courant", cntrl_data.courant);
    GetOptional(cobraParams, "irfc", cntrl_data.rfmod);
    cntrl_data.entmod = 0;
    cntrl_data.mixmod = 1;

    cntrl_data.solver = 3;
    if (cntrl_data.run_parallel) cntrl_data.solver = 5;
    GetOptional(cobraParams, "solver", cntrl_data.solver);

    double tinlet;
    GetRequired(stateParams,"STATE", "tinlet", tinlet);
    double flowfrac=100.;
    GetOptional(stateParams, "flow", flowfrac);
    flowfrac *= 0.01;   // convert from % to fraction
    double bypass=0.0;
    GetOptional(stateParams, "bypass", bypass);
    bypass *= 0.01;   // convert from % to fraction

    double flowrate;
    GetRequired(coreParams, "CORE", "rated_flow", flowrate);
    double tot_inlet_mass_flow_rate = flowfrac*flowrate;         // no unit conversion necessary
    double active_inlet_mass_flow_rate = tot_inlet_mass_flow_rate*(1.0-bypass);

    cntrl_data.ginit = active_inlet_mass_flow_rate;
    cntrl_data.trinit = tinlet;

    // Reference pressure
    double conversion_factor = 10.0; // MPa --> bar
    double reference_pressure;
    GetRequired(stateParams, "STATE", "pressure", reference_pressure);
    reference_pressure *= conversion_factor;

    cntrl_data.pref = reference_pressure;
    cntrl_data.enth_bound_1 = -tinlet;
    cntrl_data.enth_bound_2 = 1496.80;
    cntrl_data.dhfrac = 0.02;
    GetOptional(cobraParams, "dhfrac", cntrl_data.dhfrac);
    cntrl_data.ibound = 2;
    cntrl_data.obound = 1;
    cntrl_data.gtot = active_inlet_mass_flow_rate;
    cntrl_data.hin = -tinlet;
    cntrl_data.hgin = 288.42;
    cntrl_data.p_bound_1 = 0.0;
    cntrl_data.p_bound_2 = reference_pressure;
    cntrl_data.notrans = 1;

    // Get Time Domain Data
    cntrl_data.dtmin = 0.000001;
    cntrl_data.dtmax = 0.1;
    cntrl_data.tend = 0.1;
    cntrl_data.rtwfp = 1000.0;
    cntrl_data.maxits = 10000;
    cntrl_data.gmp = 0.01;
    cntrl_data.gep = 0.01;
    cntrl_data.fsp = 0.5;
    cntrl_data.ssp = 0.5;
    cntrl_data.msp = 0.5;
    cntrl_data.edit_gaps= 0;
    cntrl_data.edit_channels= 0;
    cntrl_data.edit_rods= 0;
    cntrl_data.edit_dnb= 0;
    cntrl_data.edit_hdf5= 1;
    cntrl_data.edit_convergence= 1;
    GetOptional(cobraParams, "dtmin", cntrl_data.dtmin);
    GetOptional(cobraParams, "dtmax", cntrl_data.dtmax);
    GetOptional(cobraParams, "tend", cntrl_data.tend);
    GetOptional(cobraParams, "rtwfp", cntrl_data.rtwfp);
    GetOptional(cobraParams, "maxits", cntrl_data.maxits);
    GetOptional(cobraParams, "global_mass_balance", cntrl_data.gmp);
    GetOptional(cobraParams, "global_energy_balance", cntrl_data.gep);
    GetOptional(cobraParams, "fluid_energy_storage", cntrl_data.fsp);
    GetOptional(cobraParams, "solid_energy_storage", cntrl_data.ssp);
    GetOptional(cobraParams, "mass_storage", cntrl_data.msp);
    GetOptional(cobraParams, "edit_gaps", cntrl_data.edit_gaps);
    GetOptional(cobraParams, "edit_channels", cntrl_data.edit_channels);
    GetOptional(cobraParams, "edit_rods", cntrl_data.edit_rods);
    GetOptional(cobraParams, "edit_dnb", cntrl_data.edit_dnb);
    GetOptional(cobraParams, "edit_hdf5", cntrl_data.edit_hdf5);
    GetOptional(cobraParams, "edit_convergence", cntrl_data.edit_convergence);

    string restart_name="NONE";
    GetOptional(couplingParams, "read_restart", restart_name);
    strcpy(cntrl_data.restart_name,restart_name.c_str());
    cntrl_data.restart=1;
    if (restart_name=="NONE") {
       cntrl_data.restart=0;
    }

    string ht_correlation="thom";
    GetOptional(cobraParams, "boil_ht_cor", ht_correlation);
    if(ht_correlation=="thom"){
       cntrl_data.boil_ht_cor=1;
    }else{
       cntrl_data.boil_ht_cor=0;
    }

    string property_evals="asme";
    GetOptional(cobraParams, "property_evaluations", property_evals);
    if(property_evals=="asme"){
       cntrl_data.property_evaluations=0;
    }else{
       cntrl_data.property_evaluations=1;
    }

    cntrl_data.k_void_drift = 1.4;
    cntrl_data.beta_sp = 0.05;
    GetOptional(cobraParams, "k_void_drift", cntrl_data.k_void_drift);
    GetOptional(cobraParams, "beta_sp", cntrl_data.beta_sp);

    // Hand off the control data to lib_ctf_pp
    cout<<"\n A number printed in CTF's contrl_data_xfer is:"<<endl;

    return cntrl_data;

  }

// -------------------------------------------------------------
//     Produce the geometry file for the COBRA pre-processor
// -------------------------------------------------------------

  geo_struct create_file_geo_inp(ParameterList & pList, int num_assm) {
    const ParameterList & coreParams = pList.sublist("CORE");
    const ParameterList & editsParams = pList.sublist("EDITS");
    const ParameterList & assembliesParams = pList.sublist("ASSEMBLIES");
    ParameterList stateParams;
    if( pList.isSublist("STATE") ) {
      stateParams = pList.sublist("STATE");
    } else if( pList.isSublist("STATES") ) {
      stateParams = pList.sublist("STATES").sublist("State_1");
    }

    Array<double> edit_bounds;
    GetRequired(editsParams, "EDITS", "axial_edit_bounds", edit_bounds);

    const double conversion_factor = 10.0; // cm to mm

    geo_struct geo_data;


    int map_size;
    GetRequired(coreParams, "CORE", "core_size", map_size);

 // The input file may have multiple assembly types, but we only support one "thermal-hydraulic type"
 // in the problem.  In the assembly file we must loop through each assembly and make sure each
 // assembly has the same number of pins, pin layout, clad dimensions, etc.
 //
 // The pre-processor does support multiple pin types, but this would take quite a bit of work to implement.
 // We would have to loop over the entire problem and identify the different pin types in the problem.

 // Removed following check to allow multiple assembly types in the input
 //    Array<string> assm_map = vera_xml.get_param_from_plist<Array<string> >( "CORE.assm_map");
 //    for( int k = 0; k < assm_map.size(); ++k )
 //      if( assm_map[k] != assm_map[0] )
 //        throw runtime_error("assm_map contains more than one unique assembly type");

    int num_assm_type =1;    // *** hardwire for now

    cout << endl;
    cout << "debug: map  size = " << map_size  << endl;
    cout << "debug: num_assm  = " << num_assm  << endl;
    int core_total_size=core_shape.size();
    cout << "debug: core size = " << core_total_size << endl;
    cout << endl;

    geo_data.nassem = num_assm;
    geo_data.tf     = num_assm_type;
    geo_data.n_assem_col = map_size;
    geo_data.n_assem_row = map_size;

    geo_data.shroud_gap = -1.0;
    GetOptional(coreParams, "baffle_gap", geo_data.shroud_gap);
    geo_data.model_shroud = ( geo_data.shroud_gap > 0.0 );

  // symmetry options

    string symopt = "full";
    GetOptional(stateParams, "sym", symopt);

    if ( symopt == "full" ){
       geo_data.sym_opt = 1;
    }else if ( symopt == "qtr" ){
       string bc_symopt="rot";
       GetOptional(coreParams, "bc_sym", bc_symopt);
       if(bc_symopt=="rot"){
          geo_data.sym_opt=5;
       }else{
          geo_data.sym_opt = 4;
       }
    }else{
      throw runtime_error("invalid STATE.sym value - must be full or qtr");
    }

  // print core map

    geo_data.c_ptr_to_core_shape= &core_shape[0];

  // print axial mesh

    size_t num_edit = edit_bounds.size();

    // Find the bottom of active fuel for the first assembly
    ParameterList::ConstIterator citer = assembliesParams.begin(),
                                 c_end = assembliesParams.end();
    const double model_bottom = edit_bounds.at(0);
    for( ; c_end != citer; ++citer )
    {
       string assembly_name = assembliesParams.name(citer);
       break;
    }

    // Convert the bounds to mm, which is what lib_ctf_pp is expecting, and subtract
    // off the inactive portion of the fuel
    geo_edit_bounds.resize(num_edit);
    for (unsigned bound=0;bound<num_edit;bound++){
       geo_edit_bounds.at(bound)=(edit_bounds.at(bound)-model_bottom)*conversion_factor;
    }

    geo_data.ivar = num_edit-1;

    geo_data.c_ptr_to_ztop = &geo_edit_bounds.at(1);

    strcpy(geo_data.fname, "17x17_VERA.inp");

    zondx.resize(num_edit);
    for(size_t i=0; i<num_edit; ++i)
       zondx.at(i) = 1;

    geo_data.c_ptr_to_zondx = &zondx.at(0);

    return geo_data;

  }

// -------------------------------------------------------------
//     Produce the power file for the COBRA pre-processor
// -------------------------------------------------------------

  power_struct create_file_power_inp(const Array<double> & fuel_pin_map, VERAIn_XML_Common & vera_common)
  {
    ParameterList pList = vera_common.get_vera_xml().get_pList();
    const ParameterList & coreParams = pList.sublist("CORE");
    const ParameterList & assembliesParams = pList.sublist("ASSEMBLIES");
    ParameterList stateParams;
    if( pList.isSublist("STATE") ) {
      stateParams = pList.sublist("STATE");
    } else if( pList.isSublist("STATES") ) {
      stateParams = pList.sublist("STATES").sublist("State_1");
    }

    power_struct power_data;

    double cm2mm = 10.0; // cm to mm

    // If num_pf_files is greater than 1, then we need to
    // set the transient time for each step 1000 seconds longer
    // than the previous
    Array<double> stacked_case_times; // default to empty
    cout<<endl;
    GetOptional(stateParams, "deplete", stacked_case_times, false);
    cout<<endl;
    int num_pf_files = 1;
    if (stacked_case_times.size()>0) num_pf_files = stacked_case_times.size();

    power_dat_time.resize(num_pf_files);
    for(int time=0; time<num_pf_files; time++){
       power_dat_time.at(time) = 1000.0*time;
    }
    power_data.c_ptr_to_power_dat_time = &power_dat_time.at(0);

  // Removed check below to allow multiple assembly types in the input

  // Make sure we have only one assembly type
    string assembly_name = "";
    ParameterList::ConstIterator citer = assembliesParams.begin(),
                                 c_end = assembliesParams.end();
    for( ; c_end != citer; ++citer )
    {
      const ParameterEntry & entry = assembliesParams.entry(citer);
      if( entry.isList() )
      {
        string data = assembliesParams.name(citer);
        std::transform(data.begin(), data.end(), data.begin(), ::tolower);
        if( (data.find("assembly_")==0) && assembly_name.empty() )
          assembly_name = assembliesParams.name(citer);
      }
    }

    double statepow;
    GetRequired(stateParams, "STATE", "power", statepow);  // percent of rated power.
    double power;
    GetRequired(coreParams, "CORE", "rated_power", power);
    power *= statepow * 0.01;  // convert from percent
    // If running stacked case, set the power for each state point
    // Note that all powers are set to the same value
    corepower.resize(num_pf_files,power);
    power_data.c_ptr_to_corepower = &corepower.at(0);

    // The power profiles provide the starting guess for the powers in a coupled DENOVO calculation.
    // The last entry in the table is the active core height
    // The top of the table must be slightly taller than the active fuel height
    // Heights correspond to the beginning of active fuel (BAF)

    double active_fuel_length = vera_common.get_total_fuel_length_in_cm(assembly_name);
    cout << "  active_fuel_length = " << active_fuel_length << " cm" << endl;

    y.resize(2*num_pf_files);
    axialz.resize(2*num_pf_files,1.0);
    for(int pf_file=0;pf_file<2*num_pf_files;pf_file++){
       if (pf_file%2==0){
          y.at(pf_file)=0.0;
       }
       else{
          y.at(pf_file)=active_fuel_length*cm2mm;
       }
    }

    power_data.mnxn = 2;
    power_data.c_ptr_to_y = &y.at(0);
    power_data.c_ptr_to_axialz = &axialz.at(0);

    int map_size;
    GetRequired(coreParams, "CORE", "core_size", map_size, false);

    // Set the power factor of each assembly... always 1.0, 0.0 for blank areas
    // Set the assembly power factor map that each assembly should use... always 1 since we use
    // the same power factor map for every assembly.
    assempf.resize(map_size*map_size*num_pf_files);
    assempf_map.resize(map_size*map_size*num_pf_files);
    int assem_counter=0;

    // Note that for stacked cases, the power factor maps will always
    // look the same
    Array<int> core_shape;
    GetRequired(coreParams, "CORE", "shape", core_shape, false);
    for (int pf_file=0;pf_file<num_pf_files;pf_file++){
       if ( map_size == 1){     // preserve old edit format
          assempf.at(assem_counter) = 1.0;
          assempf_map.at(assem_counter) = 1;
          assem_counter = assem_counter+1;
       }
       else{
         for( int j = 0; j < map_size; ++j )
         {
           for( int i = 0; i < map_size; ++i ){
             if ( core_shape[j*map_size+i] == 0 ){
                assempf.at(assem_counter) = 0.0;
                assempf_map.at(assem_counter) = 0;
             }
             else
             {
                assempf.at(assem_counter) = 1.0;
                assempf_map.at(assem_counter) = 1;
             }
             assem_counter=assem_counter+1;
           }
         }
       }
    }


    power_data.c_ptr_to_assempf = &assempf.at(0);
    power_data.c_ptr_to_assempf_map = &assempf_map.at(0);


    int num_pins = sqrt(fuel_pin_map.size());
    local_pf.resize(num_pins*num_pins*num_pf_files);

    int map_count=0;
    power_data.num_pf_maps = 1;

    for( int pf_file=0;pf_file<num_pf_files;pf_file++){
       for( int k = 0; k < num_pins; ++k )
       {
         for( int m = 0; m < num_pins; ++m )
         {
           local_pf.at(map_count) = fuel_pin_map[k*num_pins+m];
           map_count = map_count+1;
         }
       }
    }

    power_data.c_ptr_to_local_pf = &local_pf.at(0);

    return power_data;

  }

}
