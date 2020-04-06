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
#include <boost/filesystem.hpp>
#include <boost/foreach.hpp>
#include <boost/algorithm/string.hpp>
#include <boost/property_tree/ptree.hpp>
#include <boost/property_tree/xml_parser.hpp>

using namespace std;
using namespace dlib;
using boost::property_tree::ptree;

std::string g_mode = "none";

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
// get content from metadata file and generating 4 vectors:
//   embeddings (list of face embeddings. [b1.dat,b2-1.dat,b2-2.dat,b3.dat)
//   labels_idx (list of label indices of respective embedding. 0,1,1,2)
//   ids (list of labels ["b1", "b2", "b3"])
//	 embed_filenames (list of embeding files)
//	 label_id_map (map of label to id)
//   create flattened list of embeddings
//   if label_id_map exists (?), use exsisting mapping instead of new one.
//-----------------------------------------------------------------
void extract_embeds (std::string embed_xml, 
		std::vector<matrix<float,128,1>> &embeddings, 
		std::vector<double> & labels_idx, 
		std::vector <std::string> & ids, 
		std::vector <std::string> & embed_filenames, 
		std::map<std::string,int> label_id_map)
{
		std::vector<std::vector<string>> emb_objs;
		// gets ids from metadata file 
		emb_objs = load_embeds_map (embed_xml, ids);
		double label_idx;
		std::string embed_filename;
		std::string mode = g_mode;
		for (size_t i=0; i < emb_objs.size(); ++i)
		{
			label_idx = i;
			if (label_id_map.size () > 0) // use existing mapping
			{
				if (label_id_map.count (ids[i]) > 0) // label exists
				{
					label_idx = label_id_map[ids[i]];
					// cout << "index: " << label_idx << " : " << ids[i] << endl;
				}
				else if (g_mode != "infer")   // unknown label, skip to next label
				{
					cout << "Ignoring unrecognized label: " << ids[i] << endl;
					continue;
				}
			}
			for (size_t j = 0; j < emb_objs[i].size(); ++j)
			{
				matrix<float,128,1> embedding;
				embed_filename = emb_objs[i][j];
				embed_filenames.push_back (embed_filename);

				deserialize(embed_filename) >> embedding;
				embeddings.push_back(embedding);
				labels_idx.push_back(label_idx);
			}
		}
}
//-----------------------------------------------------------------
//  returns network_ids.dat  from network.dat
//-----------------------------------------------------------------
std::string get_network_id_name (std::string network_str)
{
	boost::filesystem::path network_path (network_str);
	std::string ids_str = network_path.parent_path().c_str();
	if (!ids_str.empty())
		ids_str += "/";
	ids_str += network_path.stem().c_str();
	ids_str += "_ids";
	ids_str += network_path.extension().c_str();
	return ids_str;
}

// ----------------------------------------------------------------------------
//  Copy of test_multiclass_decision_function from dlib/svm.
//    Added source_files and lookup map to identify images with wrong answers.
// ----------------------------------------------------------------------------

    template <
        typename dec_funct_type,
        typename sample_type,
        typename label_type
        >
    const matrix<double> bearid_test_multiclass_decision_function (
        const dec_funct_type& dec_funct,
        const std::vector<sample_type>& x_test,
        const std::vector<label_type>& y_test,
        const std::vector<std::string>& source_files,
		const std::map<int, std::string>& id_label_map
    )
    {
        const std::vector<label_type> all_labels = dec_funct.get_labels();

        // make a lookup table that maps from labels to their index in all_labels
        std::map<label_type,unsigned long> label_to_int;
        for (unsigned long i = 0; i < all_labels.size(); ++i)
            label_to_int[all_labels[i]] = i;

        matrix<double, 0, 0, typename dec_funct_type::mem_manager_type> res;
        res.set_size(all_labels.size(), all_labels.size());

        res = 0;

        typename std::map<label_type,unsigned long>::const_iterator iter;

        // now test this trained object 
        for (unsigned long i = 0; i < x_test.size(); ++i)
        {
            iter = label_to_int.find(y_test[i]);
            // ignore samples with labels that the decision function doesn't know about.
            if (iter == label_to_int.end())
                continue;

            const unsigned long truth = iter->second;
			int label_id = dec_funct(x_test[i]);
            const unsigned long pred  = label_to_int[dec_funct(x_test[i])];
			std::string label = id_label_map.find (label_id)->second;
			boost::filesystem::path path_full_imgfile (source_files[i]);
			boost::filesystem::path path_imgfile = path_full_imgfile.filename ();
			boost::filesystem::path path_parent_path = path_full_imgfile.parent_path ();
			boost::filesystem::path path_parent = path_parent_path.filename ();
			boost::filesystem::path path_source_path = path_parent / path_imgfile;

            res(truth,pred) += 1;
			// cout << "Matched " << path_source_path.string() << " to " <<  label << endl;
			if (truth != pred)
			{
				cout << "Matched " << path_source_path.string() << " to " <<  label << endl;
			}
        }

        return res;
    }

// ----------------------------------------------------------------------------------------
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
		parser.add_option("train","Train the svm and write to network file.  Also write an ids file.", 1);
		// --test <network>
		parser.add_option("test","Test the svm using the network file.", 1);
		parser.add_option("infer","Infer the IDs of embeddings using network file.", 1);
		// --output: <trained_network> with --train; <embed_directory> with --embed
		parser.parse(argc, argv);

		// Now we do a little command line validation.  Each of the following functions
		// checks something and throws an exception if the test fails.
		const char* one_time_opts[] = {"h", "train", "test", "infer"};
		parser.check_one_time_options(one_time_opts); // Can't give an option more than once

		if (parser.option("h") || parser.number_of_arguments () != 1)
		{
			cout << "\nUsage  : bearsvm <option network_file> <embed_xml>\n";
			cout << "\nExample: bearsvm -test bearsvm_network.dat val_embeds.xml\n\n";
			parser.print_options();

			return EXIT_SUCCESS;
		}

		if (parser.option("train"))
			g_mode = "train";
		else if (parser.option("test"))
			g_mode = "test";
		else if (parser.option("infer"))
			g_mode = "infer";

		// Samples are embeddings, which ar 128D vector of floats
		typedef matrix<float,128,1> sample_type;
		typedef one_vs_one_trainer<any_trainer<sample_type> > ovo_trainer;
		typedef linear_kernel<sample_type> kernel_type;
		std::vector<sample_type> samples;
		std::vector<double> label_indices;
		std::vector <std::string> ids; 
		std::vector <std::string> embed_files; 
		std::map<std::string,int> label_id_map;
		std::map<int, std::string> id_label_map;
		std::string embed_xml = parser[0];
		std::string svm_network_name, svm_network_ids_name;

		// -----  Training ------------
		if (parser.option("train"))
		{
			svm_network_name = parser.option("train").argument();
			svm_network_ids_name = get_network_id_name (svm_network_name);
		  cout << "\nTraining with embed file.... : " << embed_xml << endl;

			extract_embeds (embed_xml, samples, label_indices, ids, embed_files, label_id_map);
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
			serialize(svm_network_name) << df2;
			serialize(svm_network_ids_name) << ids;
			cout << "\nWrote " << svm_network_name << " and " << svm_network_ids_name << ".\n" << endl;
		}
		else if (parser.option("test"))
		{
			svm_network_name = parser.option("test").argument();
			svm_network_ids_name = get_network_id_name (svm_network_name);
			one_vs_one_decision_function<ovo_trainer,
				decision_function<kernel_type> > df3;
			// Check serialization
			std::vector <string> ids2;
			deserialize(svm_network_ids_name) >> ids2;
			deserialize(svm_network_name) >> df3;
			// recreate label:index map from training run 
			for (int i = 0; i < ids2.size (); ++i) 
			{
				// cout << "ID: " << i << "\t: " << ids2[i] << endl;
				label_id_map [ids2[i]] = i;
				id_label_map [i] = ids2[i];
			}

		  cout << "\nTesting with embed file.... : " << embed_xml << endl;
			extract_embeds (embed_xml, samples, label_indices, ids, embed_files, label_id_map);


			// call copy of test_multiclass_decision_function.  Add embed_files 
			//       to identify images with wrong answers.
			matrix<double> cm = bearid_test_multiclass_decision_function(df3, samples, label_indices, embed_files, id_label_map);
			// cout << "test df: \n" << cm << endl;
			cout << "correct: "  << sum(diag(cm)) << " : total : " << sum(cm) << endl;
			cout << "accuracy: "  << sum(diag(cm))/sum(cm) << endl;
		}
		else if (parser.option("infer"))
		{
			svm_network_name = parser.option("infer").argument();
			svm_network_ids_name = get_network_id_name (svm_network_name);
			one_vs_one_decision_function<ovo_trainer,
				decision_function<kernel_type> > df3;
			// Check serialization
			std::vector <string> ids2;
			int idx;
			deserialize(svm_network_ids_name) >> ids2;
			deserialize(svm_network_name) >> df3;
		  cout << "\nInferring with embed file.... : " << embed_xml << endl;
			extract_embeds (embed_xml, samples, label_indices, ids, embed_files, label_id_map);
			for (int i = 0 ; i < samples.size (); ++i)
			{
				idx = df3 (samples[i]);
				boost::filesystem::path path_emd_file (embed_files[i]);
				cout << path_emd_file.stem().string() << " : " << ids2[idx] << endl;
			}
		}
		else
		{
			cout << "Need one of <train|test|infer> to run bearsvm." << endl;
		}
  }
  catch (exception& e)
  {
	// Note that this will catch any cmd_line_parse_error exceptions and print
	// the default message.
		cout << e.what() << endl;
  }
}
