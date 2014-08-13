#ifndef VRIPSS_VERAIN_XML_COMMON_HPP
#define VRIPSS_VERAIN_XML_COMMON_HPP

#include <sys/stat.h>
#include <iomanip>

#include "VERAIn_XML_Utils.hpp"

#include "Teuchos_CommandLineProcessor.hpp"
#include "Teuchos_ParameterList.hpp"
#include "Teuchos_XMLParameterListHelpers.hpp"
#include "Teuchos_DefaultComm.hpp"


using namespace std;
using namespace Teuchos;

class VERAIn_XML_Common
{

  public:

    VERAIn_XML_Common(VERAIn_XML &);

    ~VERAIn_XML_Common() { }

    VERAIn_XML & get_vera_xml()
      { return vera_xml_; }

    double get_top_active_fuel_in_cm(const string &) const;
    double get_bottom_active_fuel_in_cm(const string &) const;
    double get_total_fuel_length_in_cm(const string &) const;


  private: // methods

    void compute_active_fuel_specs();

  private: // data

    VERAIn_XML & vera_xml_;

    map<string, double> top_active_fuel_;
    map<string, double> bottom_active_fuel_;
    map<string, double> total_fuel_length_;
};

#endif
