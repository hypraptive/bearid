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
#include <dlib/cmd_line_parser.h>
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
//   populate obj_labels and returns vector of embeddings.
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
//-----------------------------------------------------------------
// get content from metadata file and generating 3 vectors:
//   samples (list of embeddings. [b1.dat,b2-1.dat,b2-2.dat,b3.dat)
//   labels_idx (list of label indices of respective embedding. 0,1,1,2)
//   ids (list of labels [b1, b2, b3])
//   create flattened list of embeddings
//   if label_map exists, use exsisting mapping instead of new one.
//-----------------------------------------------------------------
void extract_embeds (std::string embed_file, 
		std::vector<matrix<float,128,1>> &samples, 
		std::vector<double> & labels_idx, 
		std::vector <std::string> & ids, 
		std::map<std::string,int> label_map)
{
		std::vector<std::vector<string>> emb_objs;
		// gets ids from metadata file 
		emb_objs = load_embeds_map (embed_file, ids);
		double label_idx;
		for (size_t i=0; i < emb_objs.size(); ++i)
		{
			label_idx = i;
			if (label_map.size () > 0) // use existing mapping
			{
				if (label_map.count (ids[i]) > 0) // label exists
				{
					label_idx = label_map[ids[i]];
					// cout << "index: " << label_idx << " : " << ids[i] << endl;
				}
				else		// unknown label, skip to next label
				{
					cout << "Ignoring unrecognized label: " << ids[i] << endl;
					continue;
				}
			}
			for (size_t j = 0; j < emb_objs[i].size(); ++j)
			{
				matrix<float,128,1> embedded;
				deserialize(emb_objs[i][j]) >> embedded;
				samples.push_back(embedded);
				labels_idx.push_back(label_idx);
			}
		}
}
//-----------------------------------------------------------------

// Set folds higer for cross validation
// However, any bears with less than folds number of embeddings will be skipped
int folds = 3;

//-----------------------------------------------------------------
//   main function
//-----------------------------------------------------------------
int main(int argc, char** argv)
{
	try
	{
		time_t timeStart = time(NULL);
		command_line_parser parser;

		parser.add_option("h","Display this help message.");
		parser.add_option("train","Train the svm. Takes embedding xml, Writes a svm file and ids file.", 1);
		// --test <network>
		parser.add_option("test","Test the svm. Takes embedding xml.", 1);
		parser.add_option("infer","Infer the IDs of embeddings. Takes an embedding xml", 1);
		// --output: <trained_network> with --train; <embed_directory> with --embed
		parser.add_option("output","Used with train, specifies trained weights file.  Use with -embed, specifies directory to put embeddings. Defaults to local.",1);
		parser.parse(argc, argv);

		// Now we do a little command line validation.  Each of the following functions
		// checks something and throws an exception if the test fails.
		const char* one_time_opts[] = {"h", "train", "test", "infer"};
		parser.check_one_time_options(one_time_opts); // Can't give an option more than once

		if (parser.option("h"))
		{
			cout << "Usage: bearsvm [options] <embed_file>\n";
			parser.print_options();

			return EXIT_SUCCESS;
		}

		// Samples are embeddings, which ar 128D vector of floats
		typedef matrix<float,128,1> sample_type;
		typedef one_vs_one_trainer<any_trainer<sample_type> > ovo_trainer;
		typedef linear_kernel<sample_type> kernel_type;
		std::vector<sample_type> samples;
		std::vector<double> label_indices;
		std::vector <std::string> ids; 
		std::map<std::string,int> label_map;
		std::string embed_file;

		// -----  Training ------------
		if (parser.option("train"))
		{
			embed_file = parser.option("train").argument();
		  cout << "\nTraining with embed file.... : " << embed_file << endl;

			extract_embeds (embed_file, samples, label_indices, ids, label_map);
			// Onve vs One trainer
			ovo_trainer trainer;

			// Linear SVM
			svm_c_linear_trainer<kernel_type> linear_trainer;
			linear_trainer.set_c(100);

			// Use the SVM classifier for the OVO trainer
			trainer.set_trainer(linear_trainer);

			//------------------------------------------------------------

			// Now let's do 5-fold cross-validation using the one_vs_one_trainer we just setup.
			// As an aside, always shuffle the order of the samples before doing cross validation.

			randomize_samples(samples, label_indices);

			// Create a decision function
			one_vs_one_decision_function<ovo_trainer> df = trainer.train(samples, label_indices);

			// Test one_vs_one_decision_function
			// cout << "predicted label: "<< df(samples[0])  << ", true label: "<< label_indices[0] << endl;

			// Save SVM to disk
			one_vs_one_decision_function<ovo_trainer,
			decision_function<kernel_type>    // This is the output of the linear_trainer
			> df2, df3;
			df2 = df;
			serialize("bear_svm.dat") << df2;
			serialize("bear_svm_ids.dat") << ids;
			cout << "\nWrote bear_svm.dat and bear_svm_ids.dat\n" << endl;
		}
		else if (parser.option("test"))
		{
			embed_file = parser.option("test").argument();
			one_vs_one_decision_function<ovo_trainer,
				decision_function<kernel_type> > df3;
			// Check serialization
			std::vector <string> ids2;
			deserialize("bear_svm_ids.dat") >> ids2;
			deserialize("bear_svm.dat") >> df3;
			// recreate label:index map from training run 
			for (int i = 0; i < ids2.size (); ++i) 
			{
				// cout << "ID: " << i << "\t: " << ids2[i] << endl;
				label_map [ids2[i]] = i;
			}

		  cout << "\nTesting with embed file.... : " << embed_file << endl;
			extract_embeds (embed_file, samples, label_indices, ids, label_map);
			matrix<double> cm = test_multiclass_decision_function(df3, samples, label_indices);
			// cout << "test df: \n" << cm << endl;
			cout << "correct: "  << sum(diag(cm)) << " : total : " << sum(cm) << endl;
			cout << "accuracy: "  << sum(diag(cm))/sum(cm) << endl;
		}
		else if (parser.option("infer"))
		{
			embed_file = parser.option("infer").argument();
			one_vs_one_decision_function<ovo_trainer,
				decision_function<kernel_type> > df3;
			// Check serialization
			std::vector <string> ids2;
			int idx;
			deserialize("bear_svm_ids.dat") >> ids2;
			deserialize("bear_svm.dat") >> df3;
		  cout << "\nInferring with embed file.... : " << embed_file << endl;
			extract_embeds (embed_file, samples, label_indices, ids, label_map);
			for (int i = 0 ; i < samples.size (); ++i)
			{
				idx = df3 (samples[i]);
				cout << "ID: " << ids2[idx] << endl;
			}
		}
		else
		{
			cout << "Need one of <train|test> to run bearsvm." << endl;
		}
  }
  catch (exception& e)
  {
	// Note that this will catch any cmd_line_parse_error exceptions and print
	// the default message.
		cout << e.what() << endl;
  }
}
