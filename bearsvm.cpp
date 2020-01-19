// The contents of this file are licensed under the MIT license.
// See LICENSE.txt for more information.

/*
  This program will train a linear SVM to classify bears from bear face
  embeddings.
*/

#include <iostream>
#include <ctime>
#include <vector>
#include <dlib/svm_threaded.h>
#include <dlib/svm.h>
#include <dlib/image_io.h>
#include <boost/foreach.hpp>
#include <boost/algorithm/string.hpp>
#include <boost/property_tree/ptree.hpp>
#include <boost/property_tree/xml_parser.hpp>

using namespace std;
using namespace dlib;
using boost::property_tree::ptree;

// This function spiders the top level directory and obtains a list of all the
// files.
std::vector<std::vector<string>> load_objects_list (
  const string& dir
)
{
  std::vector<std::vector<string>> objects;
  for (auto subdir : directory(dir).get_dirs())
  {
    std::vector<string> imgs;
    for (auto img : subdir.get_files())
    imgs.push_back(img);

    if (imgs.size() != 0)
    objects.push_back(imgs);
  }
  return objects;
}


//-----------------------------------------------------------------
// Grab embeddings from xml and store each under its label.
//-----------------------------------------------------------------
std::vector<std::vector<string>> load_embeds_map (
  const std::string& xml_file, std::vector<std::string>& obj_labels)
{
  std::map<string,std::vector<std::string>> embeds_map;
  ptree tree;
  boost::property_tree::read_xml (xml_file, tree);

  std::vector<std::vector<string>> objects;		// return object

  // add all embedsfiles to map by bearID
  BOOST_FOREACH(ptree::value_type& child, tree.get_child("dataset.embeddings"))
  {
    std::string child_name = child.first;

    if (child_name == "embedding")
    {
      ptree embedding = child.second;
      std::string embedfile = child.second.get<std::string>("<xmlattr>.file");
      std::string bearID = child.second.get<std::string>("label");
      if (bearID.empty())
      {
        std::cout << "Error: embedfile " << embedfile << " has no bearID.\n" << endl;
        continue;
      }
      embeds_map[bearID].push_back (embedfile);
    }
  }
  // massage map of vector to return vector of vector
  std::string key;
  std::vector<std::string> value;

obj_labels.clear ();
  std::map<std::string, std::vector<std::string>>::iterator it;
  for ( it = embeds_map.begin(); it != embeds_map.end(); it++ )
  {
    objects.push_back (it->second);
    obj_labels.push_back (it->first);
  }
  return objects;
}

std::vector<std::vector<string>> load_embeds_xml (
  const std::string& xml_file, bool pair, std::vector<std::string>& obj_labels)
  {
    std::vector<std::vector<string>> objects;		// return object

    if (pair)
    {
      cout << "Pair file" << endl;
      // objects = load_pairs_map(xml_file);
    }
    else
    {
      cout << "Normal file" << endl;
      objects = load_embeds_map(xml_file, obj_labels);
    }
    return objects;
  }

// Set folds higer for cross validation
// However, any bears with less than folds number of embeddings will be skipped
int folds = 3;

int main(int argc, char** argv)
{
  if (argc != 2)
  {
      cout << "Give this program an embeddings file.\n" << endl;
      cout << "For example: " << endl;
      cout << "   ./bearsvm <embed_file>\n" << endl;
      return 1;
  }

  // Samples are embeddings, which ar 128D vector of floats
  typedef matrix<float,128,1> sample_type;
  std::vector<sample_type> samples;
  std::vector<double> labels;
  std::vector <string> fields;
  std::vector <string> ids;
  std::vector<sample_type> new_samples;
  std::vector<double> new_labels;
  std::vector <string> new_ids;

  // Onve vs One trainer
  typedef one_vs_one_trainer<any_trainer<sample_type> > ovo_trainer;
  ovo_trainer trainer;

  // Linear SVM
  typedef linear_kernel<sample_type> kernel_type;
  svm_c_linear_trainer<kernel_type> linear_trainer;
  linear_trainer.set_c(100);

  // Use the SVM classifier for the OVO trainer
  trainer.set_trainer(linear_trainer);

	//------------------------------------------------------------
	// generating 3 vectors:
	//   samples (list of embeddings. [b1.dat,b2-1.dat,b2-2.dat,b3.dat)
	//   labels (list of label indices of respective embedding. 0,1,1,2)
	//   ids (list of labels [b1, b2, b3])

	// NEW: get content from metadata file
	std::vector<std::vector<string>> emb_objs;
	emb_objs = load_embeds_map (argv[1], new_ids);
	// create flattened list of embeddings
	for (size_t i=0; i < emb_objs.size(); ++i)
	{
		cout << "ID: " << i << "\t: " << emb_objs[i].size() << " Files \t: ";
		cout << new_ids[i] << endl;
		for (size_t j = 0; j < emb_objs[i].size(); ++j)
		{
			sample_type embedded;
			deserialize(emb_objs[i][j]) >> embedded;
			new_samples.push_back(embedded);
			new_labels.push_back(i);
		}
	}

	//------------------------------------------------------------

  // Now let's do 5-fold cross-validation using the one_vs_one_trainer we just setup.
  // As an aside, always shuffle the order of the samples before doing cross validation.

	{
  ovo_trainer new_trainer;
  svm_c_linear_trainer<kernel_type> new_linear_trainer;
  new_linear_trainer.set_c(100);

  // Use the SVM classifier for the OVO trainer
  new_trainer.set_trainer(new_linear_trainer);


  randomize_samples(new_samples, new_labels);
  cout << "\ncross validation: \n" << cross_validate_multiclass_trainer(new_trainer, new_samples, new_labels, folds) << endl;

  // Create a decision function
  one_vs_one_decision_function<ovo_trainer> df = new_trainer.train(new_samples, new_labels);

  // Test one_vs_one_decision_function
  cout << "predicted label: "<< df(new_samples[0])  << ", true label: "<< new_labels[0] << endl;

  // Save SVM to disk
  one_vs_one_decision_function<ovo_trainer,
  decision_function<kernel_type>    // This is the output of the linear_trainer
  > df2, df3;
  df2 = df;
  serialize("bear_svm_new.dat") << df2;
  serialize("bear_svm_ids_new.dat") << new_ids;

  // Check serialization
  std::vector <string> ids2;
  deserialize("bear_svm_ids_new.dat") >> ids2;
  deserialize("bear_svm_new.dat") >> df3;
  cout << "predicted label: "<< df3(new_samples[0])  << ", true label: "<< new_labels[0] << " == " << ids2[new_labels[0]] << "\n" << endl;
	}
}
