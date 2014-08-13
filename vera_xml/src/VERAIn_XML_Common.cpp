#include <sys/stat.h>
#include <iomanip>

#include "VERAIn_XML_Common.hpp"

//#include "Teuchos_CommandLineProcessor.hpp"
#include "Teuchos_ParameterList.hpp"
#include "Teuchos_XMLParameterListHelpers.hpp"
#include "Teuchos_DefaultComm.hpp"


using namespace std;
using namespace Teuchos;


VERAIn_XML_Common::VERAIn_XML_Common( VERAIn_XML & vera_xml ) :
  vera_xml_(vera_xml)
{
  compute_active_fuel_specs();
}

// -------------------------------------------------------------

double
VERAIn_XML_Common::get_top_active_fuel_in_cm( const string & assembly_name ) const
{
  map<string, double>::const_iterator citer = top_active_fuel_.find(assembly_name);
  if( top_active_fuel_.end() == citer )
    throw runtime_error("Could not get top_active_fuel info for assembly \""+assembly_name+"\".");

  return citer->second;
}

// -------------------------------------------------------------

double
VERAIn_XML_Common::get_bottom_active_fuel_in_cm( const string & assembly_name ) const
{
  map<string, double>::const_iterator citer = bottom_active_fuel_.find(assembly_name);
  if( bottom_active_fuel_.end() == citer )
    throw runtime_error("Could not get bottom_active_fuel info for assembly \""+assembly_name+"\".");

  return citer->second;
}

// -------------------------------------------------------------

double
VERAIn_XML_Common::get_total_fuel_length_in_cm( const string & assembly_name ) const
{
  map<string, double>::const_iterator citer = total_fuel_length_.find(assembly_name);
  if( total_fuel_length_.end() == citer )
    throw runtime_error("Could not get total_fuel_length info for assembly \""+assembly_name+"\".");

  return citer->second;
}

// -------------------------------------------------------------

void
VERAIn_XML_Common::compute_active_fuel_specs()
{
  const ParameterList & assemblies = vera_xml_.get_sublist("ASSEMBLIES");

  // Get Assemblies
  ParameterList::ConstIterator citer = assemblies.begin(),
    c_end = assemblies.end();
  for( ; c_end != citer; ++citer )
  {
    const ParameterEntry & entry = assemblies.entry(citer);
    if( entry.isList() && (vera_xml_.downstring(assemblies.name(citer)).find("assembly_") == 0) )
    {
      string assembly_name = assemblies.name(citer);
      string assembly_ppath = "ASSEMBLIES." + assembly_name;

      // Determine TAF, BAF and active fuel height based on all "fuel" axial regions
      // To calculate the height of active fuel:
      // 1. Find the top and bottom axial levels that contain fuel (num_fuel_rods > 0)
      // 2. Read the array \"axial_elevations\"
      // 3. active fuel height = top elevation of top fuel level - bottom elevation of bottom fuel level

      bottom_active_fuel_[assembly_name] = 1.e20; // could use double traits here
      top_active_fuel_[assembly_name] = 0.0;
      total_fuel_length_[assembly_name] = 0.0;

      Array<string> axial_labels = vera_xml_.get_param_from_plist<Array<string> >(assembly_ppath+".axial_labels");
      Array<double> axial_elevations = vera_xml_.get_param_from_plist<Array<double> >( assembly_ppath+".axial_elevations");

      for( unsigned i = 0; i < axial_labels.size(); ++i )
      {
        double axial_level_length = axial_elevations[i+1] - axial_elevations[i];

        string PL_entry = "ASSEMBLIES." + assembly_name + ".CellMaps.CellMap_" + axial_labels[i] + ".cell_map";
        Array<string> cell_map = vera_xml_.get_param_from_plist<Array<string> >( PL_entry);
        // Look for the presence of fuel and stop if found - we just need to know if this axial level has fuel
        bool axial_level_has_fuel = false;
        double num_fuel_pins = 0;
        for( int j = 0; j < cell_map.size(); ++j )
        {
          string cell_name = "Cell_" + cell_map[j];
          string ppath_cell_type = assembly_ppath+".Cells."+cell_name+".type";
          string cell_type = vera_xml_.get_param_from_plist<string>( ppath_cell_type);
          if( "fuel" == cell_type )
          {
            axial_level_has_fuel = true;
            num_fuel_pins++;
          }
        }
        if( axial_level_has_fuel )
        {
          //cout << "Axial label \"" << axial_labels[i] << "\" has fuel." << endl;
          bottom_active_fuel_[assembly_name] = min(axial_elevations[i],   bottom_active_fuel_[assembly_name] );
          top_active_fuel_[assembly_name]    = max(axial_elevations[i+1], top_active_fuel_[assembly_name]    );

          total_fuel_length_[assembly_name] += axial_level_length;
        }
      }
    }
  }
}
