// The contents of this file are licensed under the MIT license.
// See LICENSE.txt for more information.

/*
This program takes a set of face chips and trains a network for face
embedding.

This program is based on the following example from dlib:

https://github.com/davisking/dlib/blob/master/examples/dnn_metric_learning_ex.cpp

The program had 3 usage modes:
1. train: using a set of face chips, train an embedding network
2. test:  using a set of face chips, test the network for accuracy
3. embed: use the trained network to create embeddings fro each provided
face chip.
*/

#include <iostream>
#include <ctime>
#include <dlib/dnn.h>
#include <dlib/image_io.h>
#include <dlib/misc_api.h>
#include <dlib/cmd_line_parser.h>
#include <dlib/matrix.h>
#include <boost/filesystem.hpp>
#include <boost/foreach.hpp>
#include <boost/algorithm/string.hpp>
#include <boost/property_tree/ptree.hpp>
#include <boost/property_tree/xml_parser.hpp>
#include <boost/date_time/posix_time/posix_time.hpp>
#include <boost/date_time/posix_time/posix_time_io.hpp>
#include "boost/date_time/local_time_adjustor.hpp"
#include "boost/date_time/c_local_time_adjustor.hpp"
#include <map>

using namespace dlib;
using namespace std;
using namespace boost::posix_time;
using namespace boost::gregorian;
using namespace boost::algorithm;
using boost::property_tree::ptree;

// ----------------------------------------------------------------------------------------
//  program functionality:
//		list of training set & test set
//     	network produced
//     	results
//		any parameters used as input (size of vector)
//
// log error rate(s) through iterations.
// ----------------------------------------------------------------------------------------

// We will need to create some functions for loading data.  This program will
// expect to be given a directory structured as follows:
//    top_level_directory/
//        person1/
//            image1.jpg
//            image2.jpg
//            image3.jpg
//        person2/
//            image4.jpg
//            image5.jpg
//            image6.jpg
//        person3/
//            image7.jpg
//            image8.jpg
//            image9.jpg
//
// The specific folder and image names don't matter, nor does the number of folders or
// images.  What does matter is that there is a top level folder, which contains
// subfolders, and each subfolder contains images of a single person.

ptree g_xml_tree;
std::string g_mode; // one of {train,test,embed}
std::vector <ptree> g_chips;

//--------------------------------------------------
// initialize xml
//--------------------------------------------------
int xml_add_headers ()
{
  g_xml_tree.add("dataset.name", "bearid dataset");
  g_xml_tree.add("dataset.comment", "Created by bearembed");
  return 0;
}

//--------------------------------------------------
// This function spiders the top level directory and obtains a list of all the
// image files.
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

/*!
    jitter image for augmentation.

    requires
        - image_type == an image object that implements the interface defined in
          dlib/image_processing/generic_image.h
        - pixel_traits<typename image_traits<image_type>::pixel_type>::has_alpha == false
        - img.size() > 0
        - img.nr() == img.nc()
    ensures
        - Randomly jitters the image a little bit and returns this new jittered image.
          To be specific, the returned image has the same size as img and will look
          generally similar.  The difference is that the returned image will have been
          slightly rotated, zoomed, and translated.  There is also a 50% chance it will
          be mirrored left to right.
!*/
template <
    typename image_type
    >
image_type my_jitter_image(
    const image_type& img,
    dlib::rand& rnd
)
{
    DLIB_CASSERT(num_rows(img)*num_columns(img) != 0);
    DLIB_CASSERT(num_rows(img)==num_columns(img));

    const double max_rotation_degrees = 3;
    const double min_object_height = 0.97;
    const double max_object_height = 0.99999;
    const double translate_amount = 0.02;


    const auto rect = shrink_rect(get_rect(img),3);

    // perturb the location of the crop by a small fraction of the object's size.
    const point rand_translate = dpoint(rnd.get_double_in_range(-translate_amount,translate_amount)*rect.width(),
        rnd.get_double_in_range(-translate_amount,translate_amount)*rect.height());

    // perturb the scale of the crop by a fraction of the object's size
    const double rand_scale_perturb = rnd.get_double_in_range(min_object_height, max_object_height);

    const long box_size = rect.height()/rand_scale_perturb;
    const auto crop_rect = centered_rect(center(rect)+rand_translate, box_size, box_size);
    const double angle = rnd.get_double_in_range(-max_rotation_degrees, max_rotation_degrees)*pi/180;
    image_type crop;
    extract_image_chip(img, chip_details(crop_rect, chip_dims(num_rows(img),num_columns(img)), angle), crop);
    if (rnd.get_random_double() > 0.5)
        flip_image_left_right(crop);

    return crop;
}


//-----------------------------------------------------------------
// Grab matched and unmatched pairs of chip files and labels
//-----------------------------------------------------------------
std::vector<std::vector<string>> load_pairs_map (
  const std::string& xml_file)
  {
    //std::map<string,std::vector<std::string>> chips_map;
    ptree tree;
    boost::property_tree::read_xml (xml_file, tree,
			boost::property_tree::xml_parser::trim_whitespace);

    cout << "load_pairs_map" << endl;

    std::vector<std::vector<string>> objects;		// return object
    std::vector<string> matched_chips;
    std::vector<string> unmatched_chips;
    std::vector<string> matched_labels;
    std::vector<string> unmatched_labels;
    int count = 0;

    BOOST_FOREACH(ptree::value_type& child, tree.get_child("dataset.pairs"))
    {
      std::string child_name = child.first;
      std::vector<string> pairFiles;
      std::vector<string> pairLabels;

      //cout << child_name << " " << count << endl;

      if ((child_name == "pair_matched") || (child_name == "pair_unmatched"))
      {
        ptree pairtree = (ptree) child.second;
        int ccount = 0;

        BOOST_FOREACH(ptree::value_type& pchild, pairtree)
        {
          //cout << pchild.first << endl;
          ccount += 1;
          std::string chipfile = pchild.second.get<std::string>("<xmlattr>.file");
          pairFiles.push_back (chipfile);
          std::string bearID = pchild.second.get<std::string>("label");
          pairLabels.push_back (bearID);
          //cout << "ID: " << bearID << " File: " << chipfile << endl;
        }
        if (ccount == 2)
        {
          // Add pair to map
          if (child_name == "pair_matched")
          {
            matched_chips.push_back (pairFiles[0]);
            matched_chips.push_back (pairFiles[1]);
            matched_labels.push_back (pairLabels[0]);
            matched_labels.push_back (pairLabels[1]);
          }
          else{
            unmatched_chips.push_back (pairFiles[0]);
            unmatched_chips.push_back (pairFiles[1]);
            unmatched_labels.push_back (pairLabels[0]);
            unmatched_labels.push_back (pairLabels[1]);
          }
        }
        else
        {
          cout << "BAD PAIR: " << child_name << " " << count << " has " << ccount << " chip(s)" << endl;
        }
      }

      count += 1;
      //if (count >= 3) break;  //TODO Remove ME
    }

    objects.push_back (matched_chips);
    objects.push_back (unmatched_chips);
    objects.push_back (matched_labels);
    objects.push_back (unmatched_labels);

    return objects;
}

//-----------------------------------------------------------------
// Grab all the chip files from xml and store each under its label.
// When doing infer/embed, chips will not have label so return
//   vector of 1 list and empty string.
//   Generate warning for chips with no label when test and train.
//-----------------------------------------------------------------
std::vector<std::vector<string>> load_chips_map (
  const std::string& xml_file, std::vector<std::string>& obj_labels)
  {
    std::map<string,std::vector<std::string>> chips_map;
    ptree tree;
    boost::property_tree::read_xml (xml_file, tree,
			boost::property_tree::xml_parser::trim_whitespace);
		std::string mode = g_mode;

    std::vector<std::vector<string>> objects;		// return object

    // for traing and test, add all chip filenames to map by bearID
    BOOST_FOREACH(ptree::value_type& child, tree.get_child("dataset.chips"))
    {
      std::string child_name = child.first;

      if (child_name == "chip")
      {
        ptree chip = child.second;
        std::string chipfile = child.second.get<std::string>("<xmlattr>.file");
        std::string bearID = child.second.get<std::string>("label");
        if (bearID.empty() && g_mode != "embed")
        {
			std::cout << "Error: ignoring chipfile " << chipfile << " wwith no bearID.\n" << endl;
			continue;
        }
		if (bearID.empty())
		{
			bearID = " ";
			// TODO:  need to support for unknown images
		}
		g_chips.push_back (chip);
        chips_map[bearID].push_back (chipfile);
      }
    }
    // massage map of vector to return vector of vector
    std::string key;
    std::vector<std::string> value;

	obj_labels.clear ();
    std::map<std::string, std::vector<std::string>>::iterator it;
    for ( it = chips_map.begin(); it != chips_map.end(); it++ )
    {
      objects.push_back (it->second);
      obj_labels.push_back (it->first);
    }
    return objects;
  }

//-----------------------------------------------------------------
//-----------------------------------------------------------------
std::vector<std::vector<string>> load_chips_xml (
  const std::string& xml_file, bool pair, std::vector<std::string>& obj_labels)
  {
    std::vector<std::vector<string>> objects;		// return object

    if (pair)
    {
      cout << "Pair file" << endl;
      objects = load_pairs_map(xml_file);
    }
    else
    {
      cout << "Normal file" << endl;
      objects = load_chips_map(xml_file, obj_labels);
    }
    return objects;
  }


//-----------------------------------------------------------------

  // This function takes the output of load_objects_list() as input and randomly
  // selects images for training.  It should also be pointed out that it's really
  // important that each mini-batch contain multiple images of each person.  This
  // is because the metric learning algorithm needs to consider pairs of images
  // that should be close (i.e. images of the same person) as well as pairs of
  // images that should be far apart (i.e. images of different people) during each
  // training step.
  void load_mini_batch (
    const size_t num_people,     // how many different people to include
    const size_t samples_per_id, // how many images per person to select.
    dlib::rand& rnd,
    const std::vector<std::vector<string>>& objs,
    std::vector<matrix<rgb_pixel>>& images,
    std::vector<unsigned long>& labels
  )
  {
    images.clear();
    labels.clear();
    DLIB_CASSERT(num_people <= objs.size(), "The dataset doesn't have that many people in it.");

    std::vector<bool> already_selected(objs.size(), false);
    matrix<rgb_pixel> image;
    for (size_t i = 0; i < num_people; ++i)
    {
      size_t id = rnd.get_random_32bit_number()%objs.size();
      // don't pick a person we already added to the mini-batch
      while(already_selected[id])
      id = rnd.get_random_32bit_number()%objs.size();
      already_selected[id] = true;
      //cout << "Rnd ID: " << id << endl;

      for (size_t j = 0; j < samples_per_id; ++j)
      {
        const auto& obj = objs[id][rnd.get_random_32bit_number()%objs[id].size()];
        load_image(image, obj);
        images.push_back(std::move(image));
        labels.push_back(id);
      }
    }

    // You might want to do some data augmentation at this point.  Here we do some simple
    // color augmentation.
    for (auto&& crop : images)
    {
        disturb_colors(crop,rnd);
        // Jitter most crops
        if (rnd.get_random_double() > 0.1)
            crop = my_jitter_image(crop,rnd);
    }


    // All the images going into a mini-batch have to be the same size.  And really, all
    // the images in your entire training dataset should be the same size for what we are
    // doing to make the most sense.
    DLIB_CASSERT(images.size() > 0);
    for (auto&& img : images)
    {
      DLIB_CASSERT(img.nr() == images[0].nr() && img.nc() == images[0].nc(),
      "All the images in a single mini-batch must be the same size.");
    }
  }

  // ----------------------------------------------------------------------------------------

  // The next page of code defines a ResNet network.  It's basically copied
  // and pasted from the dnn_imagenet_ex.cpp example, except we replaced the loss
  // layer with loss_metric and make the network somewhat smaller.

  template <template <int,template<typename>class,int,typename> class block, int N, template<typename>class BN, typename SUBNET>
  using residual = add_prev1<block<N,BN,1,tag1<SUBNET>>>;

  template <template <int,template<typename>class,int,typename> class block, int N, template<typename>class BN, typename SUBNET>
  using residual_down = add_prev2<avg_pool<2,2,2,2,skip1<tag2<block<N,BN,2,tag1<SUBNET>>>>>>;

  template <int N, template <typename> class BN, int stride, typename SUBNET>
  using block  = BN<con<N,3,3,1,1,relu<BN<con<N,3,3,stride,stride,SUBNET>>>>>;


  template <int N, typename SUBNET> using res       = relu<residual<block,N,bn_con,SUBNET>>;
  template <int N, typename SUBNET> using ares      = relu<residual<block,N,affine,SUBNET>>;
  template <int N, typename SUBNET> using res_down  = relu<residual_down<block,N,bn_con,SUBNET>>;
  template <int N, typename SUBNET> using ares_down = relu<residual_down<block,N,affine,SUBNET>>;

  // ----------------------------------------------------------------------------------------

  template <typename SUBNET> using level0 = res_down<256,SUBNET>;
  template <typename SUBNET> using level1 = res<256,res<256,res_down<256,SUBNET>>>;
  template <typename SUBNET> using level2 = res<128,res<128,res_down<128,SUBNET>>>;
  template <typename SUBNET> using level3 = res<64,res<64,res<64,res_down<64,SUBNET>>>>;
  template <typename SUBNET> using level4 = res<32,res<32,res<32,SUBNET>>>;

  template <typename SUBNET> using alevel0 = ares_down<256,SUBNET>;
  template <typename SUBNET> using alevel1 = ares<256,ares<256,ares_down<256,SUBNET>>>;
  template <typename SUBNET> using alevel2 = ares<128,ares<128,ares_down<128,SUBNET>>>;
  template <typename SUBNET> using alevel3 = ares<64,ares<64,ares<64,ares_down<64,SUBNET>>>>;
  template <typename SUBNET> using alevel4 = ares<32,ares<32,ares<32,SUBNET>>>;


  // training network type
  using net_type = loss_metric<fc_no_bias<128,avg_pool_everything<
  level0<
  level1<
  level2<
  level3<
  level4<
  max_pool<3,3,2,2,relu<bn_con<con<32,7,7,2,2,
  input_rgb_image
  >>>>>>>>>>>>;

  // training network type of size 150
  using net_type_150 = loss_metric<fc_no_bias<128,avg_pool_everything<
  level0<
  level1<
  level2<
  level3<
  level4<
  max_pool<3,3,2,2,relu<bn_con<con<32,7,7,2,2,
  input_rgb_image_sized<150>
  >>>>>>>>>>>>;

  // testing network type (replaced batch normalization with fixed affine transforms)
  using anet_type = loss_metric<fc_no_bias<128,avg_pool_everything<
  alevel0<
  alevel1<
  alevel2<
  alevel3<
  alevel4<
  max_pool<3,3,2,2,relu<affine<con<32,7,7,2,2,
  input_rgb_image
  >>>>>>>>>>>>;

  // testing network type of size 150
  using anet_type_150 = loss_metric<fc_no_bias<128,avg_pool_everything<
  alevel0<
  alevel1<
  alevel2<
  alevel3<
  alevel4<
  max_pool<3,3,2,2,relu<affine<con<32,7,7,2,2,
  input_rgb_image_sized<150>
  >>>>>>>>>>>>;



int find_chip_index (
std::vector <ptree> chips, std::string chip_name)
{
	for (int i=0 ; i < chips.size (); ++i)
	{
        std::string chipfile = chips[i].get<std::string>("<xmlattr>.file");
		if (chip_name == chipfile)
			return i;
	}
	return -1;
}


  // ----------------------------------------------------------------------------------------

  int main(int argc, char** argv)
  {
    try
    {
      time_t timeStart = time(NULL);
      command_line_parser parser;

      cout << "Start time: " << timeStart << endl;

      parser.add_option("h","Display this help message.");
      parser.add_option("train","Train the face embedding network. Writes to network file.");
      // --test <network>
      parser.add_option("test","Test the face embedding network. Takes trained network", 1);
      parser.add_option("pair","Interpret xml_file as a pair file, used for testing");
      // --embed <network>
      parser.add_option("embed","Create the face embedding for each image.", 1);
      // --pretrain only used with --train
      parser.add_option("pretrain","Specifies data to initialize the network.",1);
      // --output: <trained_network> with --train; <embed_directory> with --embed
      parser.add_option("output","Used with train, specifies trained weights file.  Use with -embed, specifies directory to put embeddings. Defaults to local.",1);
      // --bn not used with --pretrain
      parser.add_option("bn","Use batch norm, not affine net");
      // --network_steps  <num_iterations>.  defaults to 2000
      parser.add_option("network_steps","Steps before writing to new network file [default = 2000]",1);
      // --threshold <num_iterations>.  defaults to 10000
      parser.add_option("threshold","Iterations without progess before stopping [default = 10000]",1);
      // --numid <count_per_minibatch> . defaults to 5
      parser.add_option("numid","Number if IDs used per mini batch [default = 5]",1);
      parser.add_option("numface","Number of face images used per ID [default = 5]",1);
	  // --root <chip_root_path> . defaults to /home/data/bears/faceDogHip
      parser.add_option("root","Root of chip files, used in extracting embed file path.", 1);
      parser.add_option("roc","Generate ROC Curve data");

      parser.parse(argc, argv);

      // Now we do a little command line validation.  Each of the following functions
      // checks something and throws an exception if the test fails.
      const char* one_time_opts[] = {"h", "train", "test", "embed"};
      parser.check_one_time_options(one_time_opts); // Can't give an option more than once

      if (parser.option("h"))
      {
        cout << "Usage: bearembed [options] <xml_file>\n";
        parser.print_options();

        return EXIT_SUCCESS;
      }

      if (parser.number_of_arguments() == 0)
      {
        cout << "Give a xml chip file  as input.  It should list chips and labels to be" << endl;
        cout << "used to learn to distinguish between these labels with metric learning.  " << endl;
        cout << "For example:" << endl;
        cout << "   ./bearembed <xml_file>" << endl;
        return 1;
      }

      cout << "\nXML chip file.... : " << parser[0] << endl;


      std::vector<string> obj_labels;

			// if train or test, load chips with labels
			// if infer, has no labels, load list of chips
			if (parser.option ("embed"))
				g_mode = "embed";
			else if (parser.option ("test"))
				g_mode = "test";
			else if (parser.option ("train"))
				g_mode = "train";
      auto objs = load_chips_xml (parser[0], parser.option("pair"), obj_labels);
      cout << "objs.size(): "<< objs.size() << endl;

      // auto objs = load_objects_list(parser[0]);
      // cout << "objs.size(): "<< objs.size() << endl;

      // Id x Face parameters: example 5x5, face recognition 35x15
      int numid = get_option (parser, "numid", 5);     // how many different people to include
      int numface = get_option (parser, "numface", 5); // how many images per person to select
      cout << "numid: " << numid << endl;
      cout << "numface: " << numface << endl;

      std::vector<matrix<rgb_pixel>> images;
      std::vector<unsigned long> labels;

      // Training
      if (parser.option("train"))
      {
        anet_type_150 anet_150;
        net_type_150 net_150;
        net_type net;
        cout << "Start training..." << endl;
        std::string sync_file;
        std::string trained_network;
        if (parser.option ("output"))
        {
          trained_network = parser.option("output").argument();
        }
        else
        {
          trained_network = "bears.dat";
        }
        cout << "Output: " << trained_network << endl;

        int threshold = get_option (parser, "threshold", 10000);
        cout << "Threshold: " << threshold << endl;

        if (parser.option("pretrain")) // assumes size 150
        {
          cout << ".. using pretrain weights ..." << endl;
          std::string pretrained_file = parser.option("pretrain").argument();
          cout << "Load network: " << pretrained_file << endl;
          if (parser.option("bn"))
          {     // ------- BATCHNORM, NO -ANET ---------------
            deserialize(pretrained_file) >> net_150;
            dnn_trainer<net_type_150> trainer(net_150, sgd(0.0001, 0.9));
            cout << "...... no anet ......." << endl;
            trainer.set_learning_rate(0.001);
            sync_file= "pretrained_no_anet_sync";
            trainer.be_verbose();
            trainer.set_synchronization_file(sync_file, std::chrono::minutes(5));
            trainer.set_iterations_without_progress_threshold(threshold);
            dlib::pipe<std::vector<matrix<rgb_pixel>>> qimages(4);
            dlib::pipe<std::vector<unsigned long>> qlabels(4);
            auto data_loader = [&numid, &numface, &qimages, &qlabels, &objs](time_t seed)
            {
              dlib::rand rnd(time(0)+seed);
              std::vector<matrix<rgb_pixel>> images;
              std::vector<unsigned long> labels;
              while(qimages.is_enabled())
              {
                try
                {
                  load_mini_batch(numid, numface, rnd, objs, images, labels);
                  qimages.enqueue(images);
                  qlabels.enqueue(labels);
                }
                catch(std::exception& e)
                {
                  cout << "EXCEPTION IN LOADING DATA" << endl;
                  cout << e.what() << endl;
                }
              }
            };
            std::thread data_loader1([data_loader](){ data_loader(1); });
            std::thread data_loader2([data_loader](){ data_loader(2); });
            std::thread data_loader3([data_loader](){ data_loader(3); });
            std::thread data_loader4([data_loader](){ data_loader(4); });
            std::thread data_loader5([data_loader](){ data_loader(5); });
            while(trainer.get_learning_rate() >= 1e-4)
            {
              qimages.dequeue(images);
              qlabels.dequeue(labels);
              trainer.train_one_step(images, labels);
              cout << "Step: " << trainer.get_train_one_step_calls() << " Loss: " << trainer.get_average_loss() << endl;
            }
            trainer.get_net();
            cout << "done training" << endl;
            net_150.clean();
            anet_150 = net_150;
            serialize(trained_network) << anet_150;
            qimages.disable();
            qlabels.disable();
            data_loader1.join();
            data_loader2.join();
            data_loader3.join();
            data_loader4.join();
            data_loader5.join();
          }   // ------- BATCHNORM, NO -ANET ---------------
          else
          {     // ------- ANET ---------------
            cout << "...... using anet ......." << endl;
            deserialize(pretrained_file) >> anet_150;
            dnn_trainer<anet_type_150> trainer(anet_150, sgd(0.0001, 0.9));
            trainer.set_learning_rate(0.001);
            sync_file= "pretrained_anet_sync";
            trainer.be_verbose();
            trainer.set_synchronization_file(sync_file, std::chrono::minutes(5));
            trainer.set_iterations_without_progress_threshold(threshold);
            dlib::pipe<std::vector<matrix<rgb_pixel>>> qimages(4);
            dlib::pipe<std::vector<unsigned long>> qlabels(4);
            auto data_loader = [&numid, &numface, &qimages, &qlabels, &objs](time_t seed)
            {
              dlib::rand rnd(time(0)+seed);
              std::vector<matrix<rgb_pixel>> images;
              std::vector<unsigned long> labels;
              while(qimages.is_enabled())
              {
                try
                {
                  load_mini_batch(numid, numface, rnd, objs, images, labels);
                  qimages.enqueue(images);
                  qlabels.enqueue(labels);
                }
                catch(std::exception& e)
                {
                  cout << "EXCEPTION IN LOADING DATA" << endl;
                  cout << e.what() << endl;
                }
              }
            };
            std::thread data_loader1([data_loader](){ data_loader(1); });
            std::thread data_loader2([data_loader](){ data_loader(2); });
            std::thread data_loader3([data_loader](){ data_loader(3); });
            std::thread data_loader4([data_loader](){ data_loader(4); });
            std::thread data_loader5([data_loader](){ data_loader(5); });
						int step_count=1;
						int network_count=1;
						int network_step_size = 2000;
						if (parser.option("network_steps"))
							network_step_size = std::stoi (parser.option("network_steps").argument());
            while(trainer.get_learning_rate() >= 1e-4)
            {
              qimages.dequeue(images);
              qlabels.dequeue(labels);
              trainer.train_one_step(images, labels);
              cout << "Step: " << trainer.get_train_one_step_calls() << " Loss: " << trainer.get_average_loss() << endl;
							// generating occasional networks to create learning curve
							if (parser.option("network_steps"))
							{
								if (step_count % network_step_size == 0)
								{
									trainer.get_net();
									std::string intermediate_network = trained_network+std::to_string(network_count);
									cout << "writing network " << intermediate_network << endl;
									anet_150.clean();
									serialize(intermediate_network) << anet_150;
									network_count++;
								}
							}
							step_count++;
            }
            trainer.get_net();
            cout << "done training" << endl;
            anet_150.clean();
            serialize(trained_network) << anet_150;
            qimages.disable();
            qlabels.disable();
            data_loader1.join();
            data_loader2.join();
            data_loader3.join();
            data_loader4.join();
            data_loader5.join();
          }     // ------- ANET ---------------
        }
        else   //------------  NO PRETRAINED DATA ------
        {
          cout << "... using random weights ....." << endl;
          dnn_trainer<net_type> trainer(net, sgd(0.0001, 0.9));
          trainer.set_learning_rate(0.1);
          sync_file= "rand_sync";
          trainer.be_verbose();
          trainer.set_synchronization_file(sync_file, std::chrono::minutes(5));
          trainer.set_iterations_without_progress_threshold(threshold);
          dlib::pipe<std::vector<matrix<rgb_pixel>>> qimages(4);
          dlib::pipe<std::vector<unsigned long>> qlabels(4);
          auto data_loader = [&numid, &numface, &qimages, &qlabels, &objs](time_t seed)
          {
            dlib::rand rnd(time(0)+seed);
            std::vector<matrix<rgb_pixel>> images;
            std::vector<unsigned long> labels;
            while(qimages.is_enabled())
            {
              try
              {
                load_mini_batch(numid, numface, rnd, objs, images, labels);
                qimages.enqueue(images);
                qlabels.enqueue(labels);
              }
              catch(std::exception& e)
              {
                cout << "EXCEPTION IN LOADING DATA" << endl;
                cout << e.what() << endl;
              }
            }
          };
          std::thread data_loader1([data_loader](){ data_loader(1); });
          std::thread data_loader2([data_loader](){ data_loader(2); });
          std::thread data_loader3([data_loader](){ data_loader(3); });
          std::thread data_loader4([data_loader](){ data_loader(4); });
          std::thread data_loader5([data_loader](){ data_loader(5); });
          while(trainer.get_learning_rate() >= 1e-4)
          {
            qimages.dequeue(images);
            qlabels.dequeue(labels);
            trainer.train_one_step(images, labels);
            cout << "Step: " << trainer.get_train_one_step_calls() << " Loss: " << trainer.get_average_loss() << endl;
          }
          trainer.get_net();
          cout << "done training" << endl;
          net.clean();
          serialize(trained_network) << net;
          qimages.disable();
          qlabels.disable();
          data_loader1.join();
          data_loader2.join();
          data_loader3.join();
          data_loader4.join();
          data_loader5.join();
        }
        /*
        // ----------- START SECTION REPLICATED 3X ABOVE --------------------
        // I've set this to something really small to make the example terminate
        // sooner.  But when you really want to train a good model you should set
        // this to something like 10000 so training doesn't terminate too early.
        //trainer.set_iterations_without_progress_threshold(300);
        // -- trainer.set_iterations_without_progress_threshold(10000);

        // If you have a lot of data then it might not be reasonable to load it all
        // into RAM.  So you will need to be sure you are decompressing your images
        // and loading them fast enough to keep the GPU occupied.  I like to do this
        // using the following coding pattern: create a bunch of threads that dump
        // mini-batches into dlib::pipes.
        dlib::pipe<std::vector<matrix<rgb_pixel>>> qimages(4);
        dlib::pipe<std::vector<unsigned long>> qlabels(4);
        auto data_loader = [&qimages, &qlabels, &objs](time_t seed)
        {
        dlib::rand rnd(time(0)+seed);
        std::vector<matrix<rgb_pixel>> images;
        std::vector<unsigned long> labels;
        while(qimages.is_enabled())
        {
        try
        {
        load_mini_batch(numid, numface, rnd, objs, images, labels);
        // Tried 35x10, trained much slower and did worse on test (86%; training was 100%)
        qimages.enqueue(images);
        qlabels.enqueue(labels);
      }
      catch(std::exception& e)
      {
      cout << "EXCEPTION IN LOADING DATA" << endl;
      cout << e.what() << endl;
    }
  }
};
// Run the data_loader from 5 threads.  You should set the number of threads
// relative to the number of CPU cores you have.
std::thread data_loader1([data_loader](){ data_loader(1); });
std::thread data_loader2([data_loader](){ data_loader(2); });
std::thread data_loader3([data_loader](){ data_loader(3); });
std::thread data_loader4([data_loader](){ data_loader(4); });
std::thread data_loader5([data_loader](){ data_loader(5); });


// Here we do the training.  We keep passing mini-batches to the trainer until the
// learning rate has dropped low enough.
while(trainer.get_learning_rate() >= 1e-4)
{
qimages.dequeue(images);
qlabels.dequeue(labels);
trainer.train_one_step(images, labels);
cout << "Step: " << trainer.get_train_one_step_calls() << " Loss: " << trainer.get_average_loss() << endl;
}

// Wait for training threads to stop
trainer.get_net();
cout << "done training" << endl;

// Save the network to disk
if (parser.option("pretrained_file"))
{
if (parser.option("anet"))
{
anet_150.clean();
serialize(trained_network) << anet_150;
}
else
{
net_150.clean();
serialize(trained_network) << net_150;
}
}
else
{
net.clean();
serialize(trained_network) << net;
}

// stop all the data loading threads and wait for them to terminate.
qimages.disable();
qlabels.disable();
data_loader1.join();
data_loader2.join();
data_loader3.join();
data_loader4.join();
data_loader5.join();
// ----------- END SECTION REPLICATED 3X ABOVE --------------------
*/
}

// Testing pairs
else if (parser.option("test") && parser.option("pair"))
{
  anet_type_150 anet_150;
  anet_type_150 testing_net;

  net_type net;
  // anet_type testing_net;

  std::string test_network = (parser.option("test").argument());

  // boost::filesystem::path test_network(parser.option("train").argument());

  if (parser.option("bn"))
  {  // ------- BATCHNORM, NOT ANET ----------
    cout << "... not anet ..." << endl;
    deserialize(test_network) >> net;
    testing_net = net;
  }  // ------- BATCHNORM, NOT ANET ----------
  else
  {  // ------- ANET ----------
    cout << "... using anet ..." << endl;
    deserialize(test_network) >> testing_net;
  }  // ------- ANET ----------

  cout << "Start testing pairs..." << endl;
  std::vector<string> matchedPairs = objs[0];
  std::vector<string> unmatchedPairs = objs[1];
  std::vector<string> matchedLabels = objs[2];
  std::vector<string> unmatchedLabels = objs[3];

  std::vector<double> true_dets, false_dets;

  int num_right = 0;
  int num_wrong = 0;
  int num_true_pos = 0;
  int num_true_neg = 0;
  int num_false_pos = 0;
  int num_false_neg = 0;

  matrix<rgb_pixel> image;
  std::vector<matrix<rgb_pixel>> images;
  // set up file name for result file
  time_t rawtime;
  struct tm * timeinfo;
  char time_buffer[80];
  time (&rawtime);
  timeinfo = localtime(&rawtime);
  strftime(time_buffer,sizeof(time_buffer),"%Y%m%d%I%M",timeinfo);
  std::string result_filename = "test_result_";
  result_filename.append (time_buffer);
  ofstream result_file;
  result_file.open (result_filename);

  // Matching Pairs

  double dist_max = testing_net.loss_details().get_distance_threshold();
  for (size_t i = 0; i < matchedPairs.size(); i+=2)
  {
	result_file << matchedLabels[i] << "," << matchedLabels[i+1];
    images.clear();
    //cout << "Matched Pair " << i/2 << endl;
    //cout << matchedPairs[i] << endl;
    load_image(image, matchedPairs[i]);
    images.push_back(std::move(image));
    //cout << matchedPairs[i+1] << endl;
    load_image(image, matchedPairs[i+1]);
    images.push_back(std::move(image));

    std::vector<matrix<float,0,1>> matchedEmbedded = testing_net(images);
    double images_dist = length(matchedEmbedded[0]-matchedEmbedded[1]);
    true_dets.push_back(images_dist);

    if (images_dist < dist_max)
    {
      ++num_right;
      ++num_true_pos;
	  result_file << ",1,1,";
      //cout << "RIGHT (same) " << matchedPairs[i] << " to " << matchedPairs[i+1] << " distance is " << to_string(length(matchedEmbedded[0]-matchedEmbedded[1])) << endl;
    }
    else
    {
      ++num_wrong;
      ++num_false_neg;
	  result_file << ",0,1,";
      //cout << "WRONG (same) " << matchedPairs[i] << " to " << matchedPairs[i+1] << " distance is " << to_string(length(matchedEmbedded[0]-matchedEmbedded[1])) << endl;
    }
	result_file << matchedPairs[i] << "," << matchedPairs[i+1];
	result_file << "," << images_dist << "," << dist_max << endl;
  }

  // Unmatching Pairs
  for (size_t i = 0; i < unmatchedPairs.size(); i+=2)
  {
	result_file << unmatchedLabels[i] << "," << unmatchedLabels[i+1];
    images.clear();
    //cout << "Unmatched Pair " << i/2 << endl;
    //cout << unmatchedPairs[i] << endl;
    load_image(image, unmatchedPairs[i]);
    images.push_back(std::move(image));
    //cout << unmatchedPairs[i+1] << endl;
    load_image(image, unmatchedPairs[i+1]);
    images.push_back(std::move(image));

    std::vector<matrix<float,0,1>> unmatchedEmbedded = testing_net(images);
    double images_dist = length(unmatchedEmbedded[0]-unmatchedEmbedded[1]);
    false_dets.push_back(images_dist);

    if (images_dist >= dist_max)
    {
      ++num_right;
      ++num_true_neg;
	  result_file << ",0,0,";
      //cout << "RIGHT (same) " << unmatchedPairs[i] << " to " << unmatchedPairs[i+1] << " distance is " << to_string(length(unmatchedEmbedded[0]-unmatchedEmbedded[1])) << endl;
    }
    else
    {
      ++num_wrong;
      ++num_false_pos;
	  result_file << ",1,0,";
      //cout << "WRONG (same) " << unmatchedPairs[i] << " to " << unmatchedPairs[i+1] << " distance is " << to_string(length(unmatchedEmbedded[0]-unmatchedEmbedded[1])) << endl;
    }
	result_file << unmatchedPairs[i] << "," << unmatchedPairs[i+1];
	result_file << "," << images_dist << "," << dist_max << endl;
  }
  result_file.close ();

  cout << "num_right: "<< num_right << endl;
  cout << "num_wrong: "<< num_wrong << endl;
  cout << "num_true_pos: "<< num_true_pos << endl;
  cout << "num_true_neg: "<< num_true_neg << endl;
  cout << "num_false_pos: "<< num_false_pos << endl;
  cout << "num_false_neg: "<< num_false_neg << endl;

  double accuracy = ((double)num_right / ((double)num_right + (double)num_wrong));
  double tpr = ((double)num_true_pos / ((double)num_true_pos + (double)num_false_neg));
  double fpr = ((double)num_false_pos / ((double)num_false_pos + (double)num_true_neg));
  double tnr = ((double)num_true_neg / ((double)num_true_neg + (double)num_false_pos));
  double fnr = ((double)num_false_neg / ((double)num_true_pos + (double)num_false_neg));
  double f1 = (((double)2 * (double)num_true_pos) / (((double)2 * (double)num_true_pos) + (double)num_false_pos + (double)num_false_neg));
  cout << "Accuracy: " << fixed << accuracy << endl;
  cout << "True positive rate: " << fixed << tpr << endl;
  cout << "False negative rate: " << fixed << fnr << endl;
  cout << "True negative rate: " << fixed << tnr << endl;
  cout << "False positive rate: " << fixed << fpr << endl;
  cout << "F1 score: " << fixed << f1 << endl;

  if (parser.option("roc"))
  {
    ofstream poc_file;
    poc_file.open ("roc_curve.csv");
    // ROC Curve
    cout << "\nGenerate ROC Curve data" << endl;
    //cout << "TD: " << true_dets[0] << " FD: " << false_dets[0] << endl;
    std::vector<roc_point> ROC = compute_roc_curve (true_dets, false_dets);
    cout << "ROC size: " << ROC.size() << endl;

    // compute_roc_curve expects positive scores to be higher than negative scores
    // For the bearembed distance metric, lower is better
    // So compute_roc_curve is actually returning FNR and TNR
    // To get TPR and FPR, we need to invert (1-TPR and 1-FPR)
    poc_file << "Detection Threshold" << ", " << "True Positive Rate" << ", " << "False Positive Rate" << endl;
    for (size_t i = 0; i < ROC.size(); i+=1)
    {
      // Note TPR and FPR are inverted as descibed above
      poc_file << ROC[i].detection_threshold << ", " << (1-ROC[i].true_positive_rate) << ", " << (1-ROC[i].false_positive_rate) << endl;
    }
    poc_file.close();
  }
}

// Testing OLD
else if (parser.option("test") && !parser.option("pair"))
{
  int num_folds = 100;
  double accuracy_arr[num_folds];
  double f1_arr[num_folds];

  anet_type_150 anet_150;
  anet_type_150 testing_net;

  net_type net;
  // anet_type testing_net;

  std::string test_network = (parser.option("test").argument());

  // boost::filesystem::path test_network(parser.option("train").argument());

  if (parser.option("bn"))
  {  // ------- BATCHNORM, NOT ANET ----------
    cout << "... not anet ..." << endl;
    deserialize(test_network) >> net;
    testing_net = net;
  }  // ------- BATCHNORM, NOT ANET ----------
  else
  {  // ------- ANET ----------
    cout << "... using anet ..." << endl;
    deserialize(test_network) >> testing_net;
  }  // ------- ANET ----------

  cout << "Start testing..." << endl;
  // Normally you would use the non-batch-normalized version of the network to do
  // testing, which is what we do here.

	time_t rawtime;
	struct tm * timeinfo;
	char time_buffer[80];
  std::string result_filename;
  std::string result_filename_fold;

	time (&rawtime);
	timeinfo = localtime(&rawtime);
	strftime(time_buffer,sizeof(time_buffer),"%Y%m%d%I%M",timeinfo);
	result_filename = "test_result_";
	result_filename.append (time_buffer);

  for (int folds = 0; folds < num_folds; ++folds)
  {
		ofstream result_file;
		result_filename_fold = result_filename + "_" + to_string (folds);
		result_file.open (result_filename_fold);
    cout << endl;
    cout << "fold: "<< folds << endl;

    // Now, just to show an example of how you would use the network, let's check how well
    // it performs on the training data.
    dlib::rand rnd(time(0)+folds);
    load_mini_batch(numid, numface, rnd, objs, images, labels);

    // Run all the images through the network to get their vector embeddings.
    std::vector<matrix<float,0,1>> embedded = testing_net(images);

    // Now, check if the embedding puts images with the same labels near each other and
    // images with different labels far apart.
    int num_right = 0;
    int num_wrong = 0;
    int num_true_pos = 0;
    int num_true_neg = 0;
    int num_false_pos = 0;
    int num_false_neg = 0;
    for (size_t i = 0; i < embedded.size(); ++i)
    {
      for (size_t j = i+1; j < embedded.size(); ++j)
      {
        if (labels[i] == labels[j])
        {
          // The loss_metric layer will cause images with the same label to be less
          // than net.loss_details().get_distance_threshold() distance from each
          // other.  So we can use that distance value as our testing threshold.
		  result_file << labels[i] << "," << labels[j];
          if (length(embedded[i]-embedded[j]) < testing_net.loss_details().get_distance_threshold())
          {
            ++num_right;
            ++num_true_pos;
            //cout << "RIGHT (same) " << labels[i] << " to " << labels[j] << " distance is " << to_string(length(embedded[i]-embedded[j])) << endl;
			result_file << ",1,1" << endl;
          }
          else
          {
            ++num_wrong;
            ++num_false_neg;
			result_file << ",0,1" << endl;
            //cout << "WRONG (same) " << labels[i] << " to " << labels[j] << " distance is " << to_string(length(embedded[i]-embedded[j])) << endl;
          }
        }
        else
        {
          if (length(embedded[i]-embedded[j]) >= testing_net.loss_details().get_distance_threshold())
          {
            ++num_right;
            ++num_true_neg;
			result_file << ",0,0" << endl;
            //cout << "RIGHT (diff) " << labels[i] << " to " << labels[j] << " distance is " << to_string(length(embedded[i]-embedded[j])) << endl;
          }
          else
          {
            ++num_wrong;
            ++num_false_pos;
			result_file << ",1,0" << endl;
            //cout << "WRONG (diff) " << labels[i] << " to " << labels[j] << " distance is " << to_string(length(embedded[i]-embedded[j])) << endl;
          }
        }
      }
    }
		result_file.close ();

    cout << "num_right: "<< num_right << endl;
    cout << "num_wrong: "<< num_wrong << endl;
    cout << "num_true_pos: "<< num_true_pos << endl;
    cout << "num_true_neg: "<< num_true_neg << endl;
    cout << "num_false_pos: "<< num_false_pos << endl;
    cout << "num_false_neg: "<< num_false_neg << endl;

    double accuracy = ((double)num_right / ((double)num_right + (double)num_wrong));
    double tpr = ((double)num_true_pos / ((double)num_true_pos + (double)num_false_neg));
    double fpr = ((double)num_false_pos / ((double)num_false_pos + (double)num_true_neg));
    double tnr = ((double)num_true_neg / ((double)num_true_neg + (double)num_false_pos));
    double fnr = ((double)num_false_neg / ((double)num_true_pos + (double)num_false_neg));
    double f1 = (((double)2 * (double)num_true_pos) / (((double)2 * (double)num_true_pos) + (double)num_false_pos + (double)num_false_neg));
    cout << "Accuracy: " << fixed << accuracy << endl;
    cout << "True positive rate: " << fixed << tpr << endl;
    cout << "False negative rate: " << fixed << fnr << endl;
    cout << "True negative rate: " << fixed << tnr << endl;
    cout << "False positive rate: " << fixed << fpr << endl;
    cout << "F1 score: " << fixed << f1 << endl;

    accuracy_arr[folds] = accuracy;
    f1_arr[folds] = f1;
  }

  // Calculate the mean accuracy and f1 score
  double accuracy_sum = 0;
  double f1_sum = 0;
  for (int folds = 0; folds < num_folds; ++folds)
  {
    accuracy_sum += accuracy_arr[folds];
    f1_sum += f1_arr[folds];
  }
  double accuracy_mean = accuracy_sum / num_folds;
  double f1_mean = f1_sum / num_folds;

  // Calculate the standard error of the mean
  double deviation_sum = 0;
  for (int folds = 0; folds < num_folds; ++folds)
  {
    deviation_sum += pow((accuracy_arr[folds] - accuracy_mean), 2);
  }
  double se_of_mean = sqrt(deviation_sum / (num_folds-1));
  cout << endl;
  cout << "Accuracy Mean: " << fixed << accuracy_mean << endl;
  cout << "Standard Error of the Mean: " << fixed << se_of_mean << endl;
  cout << "F1 Mean: " << fixed << f1_mean << endl;
}
else if (parser.option("embed"))
{
  // Generate embeddings in a directory
  //   use optional --output, else create dir in current directory
  boost::filesystem::path src_path(parser[0]);
  std::string chip_root = "/home/data/bears/faceDogHip/dhTreeChip/";
  cout << "Generating embeddings..." << endl;
  std::string dst_path;
  if (parser.option ("output"))
  {
    dst_path = parser.option("output").argument();
    if (!boost::filesystem::exists(dst_path)) // create new directory
    {
	  boost::filesystem::create_directories(dst_path);
    }
  }
  if (dst_path.empty())
  {
    time_t rawtime;
    struct tm * timeinfo;
    char buffer[80];

    time (&rawtime);
    timeinfo = localtime(&rawtime);

    strftime(buffer,sizeof(buffer),"%Y%m%d%I%M",timeinfo);
    dst_path = "embed_";
    dst_path.append (buffer);
	boost::filesystem::create_directories(dst_path);
  }
  if (parser.option ("root"))
  {
  	chip_root = parser.option ("root").argument();
  }

  // create XML content file
  std::string cmd;
  for (int m = 0; m < argc; m++) {
  	cmd.append (argv[m]);
	cmd.append (" ");
  }
  boost::filesystem::path current_dir (boost::filesystem::current_path());
  g_xml_tree.add ("dataset.command", cmd);
  g_xml_tree.add ("dataset.cwd", current_dir);
  g_xml_tree.add ("dataset.filetype", "embeddings");
  ptree &embeds = g_xml_tree.add ("dataset.embeddings", "");

  /*
  src_path = boost::filesystem::canonical(src_path);
  dst_path = boost::filesystem::canonical(dst_path);
  cout << "Source path: " << src_path.string() << endl;
  cout << "Destination path: " << dst_path.string() << endl;
  cout << "Destination path: " << dst_path << endl;
  */

  anet_type_150 anet_150;
  anet_type_150 embedding_anet_150;
  net_type net;
  anet_type embedding_anet;
  std::string embed_network = (parser.option("embed").argument());
  if (parser.option("bn"))
  {  // ------- BATCHNORM, NOT ANET ----------
    deserialize(embed_network) >> net;
    embedding_anet = net;
  }  // ------- BATCHNORM, NOT ANET ----------
  else
  {  // ------- ANET ----------
    deserialize(embed_network) >> anet_150;
    embedding_anet_150 = anet_150;
  }  // ------- ANET ----------

  // Normally you would use the non-batch-normalized version of the network to do
  // testing, which is what we do here.
  matrix<rgb_pixel> image;

  int embeddings_count = 0;
  boost::filesystem::path emb_dir = boost::filesystem::canonical(dst_path);
  // go through each chip
  for (size_t i = 0; i < objs.size(); ++i)
  {
    // cout << "ID: " << i << " - label: " << obj_labels[i] << " - Files: " << objs[i].size() << endl;

    embeddings_count += objs[i].size();
    for (size_t j = 0; j < objs[i].size(); ++j)
    {
      string img_str = objs[i][j];
      string emb_str = objs[i][j];
      matrix<float,0,1> embedded;
      //cout << "Image: " << img_str << endl;
      load_image(image, img_str);
      // get embedding
      // TODO add jitter (see dnn_face_recognition_ex.cpp)
      if (parser.option("bn"))
	  {  // ------- BATCHNORM, NOT ANET ----------
        embedded = embedding_anet(image);
	  }  // ------- BATCHNORM, NOT ANET ----------
	  else
	  {  // ------- ANET ----------
        embedded = embedding_anet_150(image);
	  }  // ------- ANET ----------
	  // extract subdir path of file.  if nothing matched, the result
	  //   is the orig path.
      std::string chip_subdir_file = erase_first_copy (emb_str, chip_root); // -> bf/fitz/bf480/IMG123.JPG

      boost::filesystem::path emb_subdir_file (chip_subdir_file);
      boost::filesystem::path emb_path = emb_dir / emb_subdir_file;
      emb_path.replace_extension("dat");
      boost::filesystem::create_directories(emb_path.parent_path());
      /*
      if (!boost::filesystem::exists(emb_path.parent_path()))
      {
      //cout << "mkdir " << emb_path.parent_path() << endl;
      boost::filesystem::create_directories(emb_path.parent_path());
		}
		*/
		ptree &xml_embed = embeds.add ("embedding", "");
		char embed_str[2048]={0};
		float embed_val;
		std::string s, embed_stdstr;

		//  write embedding string to xml
		for (long r = 0; r < embedded.nr(); ++r)
		{
			// loop over all the columns
			for (long c = 0; c < embedded.nc(); ++c)
			{
				embed_val = embedded (r,c);
				s = boost::lexical_cast<std::string>(embed_val);
				embed_stdstr.append (" ");
				embed_stdstr.append (s);
				// sprintf (embed_str + strlen (embed_str), " %a", embed_val);
			}
		}
		std::vector <ptree> chips = g_chips;
		xml_embed.add ("embed_val", embed_stdstr);
		xml_embed.add ("<xmlattr>.file", emb_path.string());
		xml_embed.add ("label", obj_labels[i]);
		xml_embed.add ("chip_source", img_str);
		int chip_index = find_chip_index (chips, img_str);
		if (chip_index >= 0)
			xml_embed.add_child ("chip", chips[chip_index]);

		serialize(emb_path.string()) << embedded;
		//cout << "Embedded: " << emb_path.string() << endl;
		if (0) //((i==0) && (j==0))
		{
		  cout << "Check embedding for " << img_str << endl;
		  matrix<float,0,1> new_embedded;
		  deserialize(emb_path.string()) >> new_embedded;
		  cout << "embedded: " << endl;
		  cout << csv << embedded << endl;
		  cout << "new embedded: " << endl;
		  cout << csv << new_embedded << endl;
		  if (embedded == new_embedded)
		  {
			cout << "YAY!" << endl;
		  } else
		  {
			cout << "BOO!" << endl;
		  }
		}
	}
  }

  boost::filesystem::path xml_file (parser[0]);
  std::string embed_xml_file;
  if (xml_file.has_parent_path ())
	  embed_xml_file = xml_file.parent_path().string() + "/";
  embed_xml_file += xml_file.filename().stem().string() + "_embeds.xml";

  xml_add_headers (); // put at end since writing reverse order added
  // boost::property_tree::xml_writer_settings<char> settings ('\t', 1);
  boost::property_tree::xml_writer_settings<std::string> settings (' ', 4);
  write_xml(embed_xml_file, g_xml_tree,std::locale(),settings);
	/*
  write_xml(embed_xml_file, g_xml_tree,std::locale(),
  boost::property_tree::xml_writer_make_settings<std::string>(' ', 4, "utf-8"));
	*/
  cout << "\ngenerated: \n\t-- " << embed_xml_file << endl;
  cout << "\n\t-- " << embeddings_count << " embedding files under " << dst_path << "\n" << endl;
  }
  else
  {
	cout << "Need one of <train|test|embed> to run bearembed." << endl;
  }
  time_t timeEnd = time(NULL);

  cout << "End time: " << timeStart << endl;
  cout << "Elapsed time (s): " << difftime(timeEnd, timeStart) << endl;
  }

  catch (exception& e)
  {
	// Note that this will catch any cmd_line_parse_error exceptions and print
	// the default message.
	cout << e.what() << endl;
  }

}
