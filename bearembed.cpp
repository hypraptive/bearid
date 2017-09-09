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
#include <map>

using namespace dlib;
using namespace std;
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


//-----------------------------------------------------------------
// Grab all the chip files from xml and store each under its label.
// Generate warning for chips with no label.
//-----------------------------------------------------------------
std::vector<std::vector<string>> load_chips_map (
  const std::string& xml_file)
{
  std::map<string,std::vector<std::string>> chips_map;
  ptree tree;
  boost::property_tree::read_xml (xml_file, tree);

  //std::cout << "Filling in chips map...  " << endl;
  std::vector<std::vector<string>> objects;		// return object

  // add all chip files to map by bearID
  BOOST_FOREACH(ptree::value_type& child, tree.get_child("dataset.chips"))
  {
    std::string child_name = child.first;

	//std::cout << "dataset.chips -- child first : " << child_name << endl;
    if (child_name == "chip")
    {
		ptree chip = child.second;
		//std::cout << "child of dataset.chips " << child_name << std::endl;
		std::string chipfile = child.second.get<std::string>("<xmlattr>.file");
		//std::cout << "dataset.chips.chip.second.<xmlattr>.file .....\n\t" << chipfile << std::endl;
		std::string bearID = child.second.get<std::string>("label");
		//std::cout << "label : " << bearID << endl;
		if (bearID.empty())
		{
			std::cout << "Error: chipfile " << chipfile << " has no bearID.\n" << endl;
			continue;
		}
		chips_map[bearID].push_back (chipfile);
    }
  }
  // massage map of vector to return vector of vector
  std::string key;
  std::vector<std::string> value;


  std::map<std::string, std::vector<std::string>>::iterator it;
  for ( it = chips_map.begin(); it != chips_map.end(); it++ )
  {
	objects.push_back (it->second);
  }

  /*
  for (auto const& [key, val] : chips_map)
  {
	  objects.push_back (val);
  }
  */

  return objects;
}


/*
  for (auto subdir : directory(dir).get_dirs())
  {
    std::vector<string> imgs;
    for (auto img : subdir.get_files())
    imgs.push_back(img);

    if (imgs.size() != 0)
    objects.push_back(imgs);
  }
  return objects;

*/


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
  disturb_colors(crop,rnd);


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

// ----------------------------------------------------------------------------------------

int main(int argc, char** argv)
{
  try
  {
    command_line_parser parser;

    parser.add_option("h","Display this help message.");
    parser.add_option("train","Train the face embedding network.");
    parser.add_option("test","Test the face embedding network.");
    parser.add_option("embed","Create the face embedding for each image and write csv to <arg>.",1);

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

    auto objs = load_chips_map (parser[0]);
    cout << "objs.size(): "<< objs.size() << endl;

    // auto objs = load_objects_list(parser[0]);
    // cout << "objs.size(): "<< objs.size() << endl;

    std::vector<matrix<rgb_pixel>> images;
    std::vector<unsigned long> labels;

    //------------------------------------------------------------
    //------------------------------------------------------------
	std::map <std::string,std::vector<std::string>> chips;
    //------------------------------------------------------------


	//return 0;

    // Training
    if (parser.option("train"))
    {
      cout << "Start training..." << endl;
      net_type net;

      dnn_trainer<net_type> trainer(net, sgd(0.0001, 0.9));
      trainer.set_learning_rate(0.1);
      trainer.be_verbose();
      trainer.set_synchronization_file("bearembed_metric_sync", std::chrono::minutes(5));
      // I've set this to something really small to make the example terminate
      // sooner.  But when you really want to train a good model you should set
      // this to something like 10000 so training doesn't terminate too early.
      //trainer.set_iterations_without_progress_threshold(300);
      trainer.set_iterations_without_progress_threshold(10000);

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
            load_mini_batch(5, 5, rnd, objs, images, labels); // TODO 35x15 instead of 5x5
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
      net.clean();
      serialize("bearembed_metric_resnet.dat") << net;

      // stop all the data loading threads and wait for them to terminate.
      qimages.disable();
      qlabels.disable();
      data_loader1.join();
      data_loader2.join();
      data_loader3.join();
      data_loader4.join();
      data_loader5.join();
    }

    // Testing
    if (parser.option("test"))
    {
      int num_folds = 100;
      double accuracy_arr[num_folds];
      net_type net;

      cout << "Start testing..." << endl;

      deserialize("bearembed_metric_resnet.dat") >> net;
      // Normally you would use the non-batch-normalized version of the network to do
      // testing, which is what we do here.
      anet_type testing_net = net;

      for (int folds = 0; folds < num_folds; ++folds)
      {

        cout << endl;
        cout << "fold: "<< folds << endl;

        // Now, just to show an example of how you would use the network, let's check how well
        // it performs on the training data.
        dlib::rand rnd(time(0)+folds);
        load_mini_batch(5, 5, rnd, objs, images, labels);

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
              if (length(embedded[i]-embedded[j]) < testing_net.loss_details().get_distance_threshold())
              {
                ++num_right;
                ++num_true_pos;
                //cout << "RIGHT (same) " << labels[i] << " to " << labels[j] << " distance is " << to_string(length(embedded[i]-embedded[j])) << endl;
              }
              else
              {
                ++num_wrong;
                ++num_false_neg;
                //cout << "WRONG (same) " << labels[i] << " to " << labels[j] << " distance is " << to_string(length(embedded[i]-embedded[j])) << endl;
              }
            }
            else
            {
              if (length(embedded[i]-embedded[j]) >= testing_net.loss_details().get_distance_threshold())
              {
                ++num_right;
                ++num_true_neg;
                //cout << "RIGHT (diff) " << labels[i] << " to " << labels[j] << " distance is " << to_string(length(embedded[i]-embedded[j])) << endl;
              }
              else
              {
                ++num_wrong;
                ++num_false_pos;
                //cout << "WRONG (diff) " << labels[i] << " to " << labels[j] << " distance is " << to_string(length(embedded[i]-embedded[j])) << endl;
              }
            }
          }
        }

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
        cout << "Accuracy: " << fixed << accuracy << endl;
        cout << "True positive rate: " << fixed << tpr << endl;
        cout << "False positive rate: " << fixed << fpr << endl;
        cout << "True negative rate: " << fixed << tnr << endl;
        accuracy_arr[folds] = accuracy;
      }

      // Calculate the mean accuracy
      double accuracy_sum = 0;
      for (int folds = 0; folds < num_folds; ++folds)
      {
        accuracy_sum += accuracy_arr[folds];
      }
      double accuracy_mean = accuracy_sum / num_folds;

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
    }

    if (parser.option("embed"))
    {
      // Generate embeddings
      boost::filesystem::path src_path(parser[0]);
      boost::filesystem::path dst_path(parser.option("embed").argument());

      cout << "Generating embeddings..." << endl;

      if (boost::filesystem::exists(dst_path))
      {
        cout << "Destination directory already exists." << endl;
        return 1;
      } else
      {
        boost::filesystem::create_directories(dst_path);
      }

      src_path = boost::filesystem::canonical(src_path);
      dst_path = boost::filesystem::canonical(dst_path);
      cout << "Source path: " << src_path.string() << endl;
      cout << "Destination path: " << dst_path.string() << endl;

      net_type net;
      deserialize("bearembed_metric_resnet.dat") >> net;
      // Normally you would use the non-batch-normalized version of the network to do
      // testing, which is what we do here.
      anet_type embedding_net = net;
      matrix<rgb_pixel> image;

      for (size_t i = 0; i < objs.size(); ++i)
      {
        cout << "ID: " << i << " Files: " << objs[i].size() << endl;

        for (size_t j = 0; j < objs[i].size(); ++j)
        {
          string img_str = objs[i][j];
          string emb_str = objs[i][j];
          //cout << "Image: " << img_str << endl;
          load_image(image, img_str);
          // get embedding
          // TODO add jitter (see dnn_face_recognition_ex.cpp)
          matrix<float,0,1> embedded = embedding_net(image);
          boost::replace_first(emb_str, src_path.string(), dst_path.string());
          boost::filesystem::path emb_path(emb_str);
          emb_path.replace_extension("dat");
          if (!boost::filesystem::exists(emb_path.parent_path()))
          {
            //cout << "mkdir " << emb_path.parent_path() << endl;
            boost::filesystem::create_directories(emb_path.parent_path());
          }
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
    }
  }

  catch (exception& e)
  {
    // Note that this will catch any cmd_line_parse_error exceptions and print
    // the default message.
    cout << e.what() << endl;
  }

}
