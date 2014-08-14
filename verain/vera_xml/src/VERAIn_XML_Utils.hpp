#ifndef VRIPSS_VERAIN_XML_UTILS_HPP
#define VRIPSS_VERAIN_XML_UTILS_HPP

#include <sys/stat.h>
#include <iomanip>

#include "Teuchos_CommandLineProcessor.hpp"
#include "Teuchos_ParameterList.hpp"
#include "Teuchos_XMLParameterListHelpers.hpp"
#include "Teuchos_DefaultComm.hpp"


using namespace std;
using namespace Teuchos;

class VERAIn_XML
{

  public:

    VERAIn_XML( const string & xml_file);

    ~VERAIn_XML();

    // A collection of utility methods to get parameter values from a Teuchos::ParameterList
    template< typename T>
      T get_param_from_plist(Teuchos::ParameterList & PList, const string & param_path_and_name, bool verbose = false)
      {
        vector<string> tokens = tokenize_string(param_path_and_name);
        string p_name = tokens[tokens.size()-1];
        T p_value;
        if( 1 == tokens.size() )
          p_value = PList.get<T>(p_name);
        else
        {
          ParameterList & p_list = get_sublist(param_path_and_name, PList);
          p_value = p_list.get<T>(p_name);
        }

        if( verbose )
          cout << "I found " << param_path_and_name << " = " << p_value << endl;

        return p_value;
      }

    template< typename T>
      T get_param_from_plist(Teuchos::ParameterList & PList, const string & param_path_and_name, T default_value, bool verbose = false)
      {
        vector<string> tokens = tokenize_string(param_path_and_name);
        string p_name = tokens[tokens.size()-1];
        T p_value;
        if( 1 == tokens.size() )
        {
          p_value = PList.get<T>(p_name, default_value);
          if( PList.getEntry(p_name).isDefault() )
          {
            ostringstream oss;
            oss << "\"" << p_name << "\" = " << p_value;
            default_parameters.push_back(oss.str());
          }
        }
        else
        {
          ParameterList & p_list = get_sublist(param_path_and_name, PList);
          p_value = p_list.get<T>(p_name, default_value);
          if( p_list.getEntry(p_name).isDefault() )
          {
            ostringstream oss;
            oss << "\"" << p_name << "\" = " << p_value;
            default_parameters.push_back(oss.str());
          }
        }

        if( verbose )
          cout << "I found " << param_path_and_name << " = " << p_value << endl;

        return p_value;
      }

    template< typename T>
      T get_param_from_plist(const string & param_path_and_name, bool verbose = false)
      {
        //return get_param_from_plist(*param_list_, param_path_and_name, verbose);
        vector<string> tokens = tokenize_string(param_path_and_name);
        string p_name = tokens[tokens.size()-1];
        T p_value;
        if( 1 == tokens.size() )
          p_value = param_list_->get<T>(p_name);
        else
        {
          ParameterList & p_list = get_sublist(param_path_and_name, *param_list_);
          p_value = p_list.get<T>(p_name);
        }

        if( verbose )
          cout << "I found " << param_path_and_name << " = " << p_value << endl;

        return p_value;
      }

    template< typename T>
      T get_param_from_plist(const string & param_path_and_name, T default_value, bool verbose = false)
      {
        return get_param_from_plist(*param_list_, param_path_and_name, default_value, verbose);
      }


    template< typename T>
      string convert_value_to_string( T value )
      {
        std::ostringstream val_str_name;
        val_str_name << value << std::flush;
        return val_str_name.str();
      }

    string downstring(const string & s);

    string trim_string(const string& input);

    vector<string> tokenize_string(const string & s, const char delim = '.') const;

    string get_string_between_delims(
        const string & line,
        const char & begintag,
        const char & endtag);

    string replace_delim_tag_with_value(
        const string & line,
        const char & begintag,
        const char & endtag,
        const map<string,double> & values_map
        );

    ParameterList & get_sublist(const string & ppath, ParameterList & plist);
    ParameterList & get_sublist(const string & ppath);

    ParameterList & get_pList()
      { return *param_list_; }

    bool is_sublist(const ParameterList & plist, const string & ppath ) const;

    const vector<string> & get_default_parameters()
    { return default_parameters; }


  private:

    RCP<SerialComm<int> > comm_;
    RCP<ParameterList> param_list_;
    vector<string> default_parameters;
};

#endif
