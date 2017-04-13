// The contents of this file are licensed under the MIT license.
// See LICENSE.txt for more information.

/*
  This program will attempt to identify any bears in the input image
  from the database of know bears.

  It makes extensive use of dlib (http://dlib.net).
*/

#include <boost/filesystem.hpp>
#include <iostream>
#include <dlib/dnn.h>
#include <dlib/data_io.h>
#include <dlib/image_processing.h>
#include <dlib/gui_widgets.h>
#include <dlib/svm_threaded.h>
#include <dlib/svm.h>


using namespace std;
using namespace dlib;

// ----------------------------------------------------------------------------------------
// Face detection network (fd_net)
template <long num_filters, typename SUBNET> using con5d = con<num_filters,5,5,2,2,SUBNET>;
template <long num_filters, typename SUBNET> using con5  = con<num_filters,5,5,1,1,SUBNET>;

template <typename SUBNET> using downsampler  = relu<affine<con5d<32, relu<affine<con5d<32, relu<affine<con5d<16,SUBNET>>>>>>>>>;
template <typename SUBNET> using rcon5  = relu<affine<con5<45,SUBNET>>>;

using fd_net_type = loss_mmod<con<1,9,9,1,1,rcon5<rcon5<rcon5<downsampler<input_rgb_image_pyramid<pyramid_down<6>>>>>>>>;

// ----------------------------------------------------------------------------------------
// Embedding Network

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
// SVM Classifier

// ----------------------------------------------------------------------------------------

const unsigned MAX_SIZE = 5000*3500;

int main(int argc, char** argv) try
{
  if (argc < 2)
  {
    cout << "Call this program like this:" << endl;
    cout << "./bearid <image_file>" << endl;
    return 0;
  }

  // FACE DETECTION
  // load the models as well as glasses and mustache.
  fd_net_type fd_net;
  shape_predictor sp;
  matrix<rgb_alpha_pixel> glasses, mustache;
  deserialize("mmod_dog_hipsterizer.dat") >> fd_net >> sp >> glasses >> mustache;

  std::vector<matrix<rgb_pixel>> face_chips;

  // Now process the image, find bear, and extract a face chip
  std::string upscaled = "";
  matrix<rgb_pixel> img;
  load_image(img, argv[1]);

  if (img.size() > (MAX_SIZE))
  {
    cout << argv[1] << ": TOO BIG" << endl;
    return 0;
  }

  auto dets = fd_net(img);

  // if no faces, try with upscaling
  if (dets.size() == 0)
  {
    if (img.size() > (MAX_SIZE/4))
    {
      cout << argv[1] << ": TOO BIG to UPSCALE" << endl;
      return 0;
    }

    pyramid_up(img);
    upscaled = " UPSCALED";
    dets = fd_net(img);

    if (dets.size() == 0)
    {
      cout << "No bear faces were found" << endl;
      return 0;
    }
  }

  unsigned chipcount = 0;
  for (auto&& d : dets)
  {
    // get the landmarks for this face
    auto shape = sp(img, d.rect);

    const rgb_pixel color(0,255,0);
    auto top  = shape.part(0);
    auto lear = shape.part(1);
    auto leye = shape.part(2);
    auto nose = shape.part(3);
    auto rear = shape.part(4);
    auto reye = shape.part(5);

    // chip_details based on get_face_chip_details
    const double mean_face_shape_x[] = { 0, 0, 0.62, 0.50, 0, 0.38 };
    const double mean_face_shape_y[] = { 0, 0, 0.48, 0.70, 0, 0.48 };
    const unsigned long size = 150;
    const double padding = 0.0;
    chip_details face_chip_details;

    std::vector<dlib::vector<double,2> > from_points, to_points;
    for (unsigned long i : {3, 5, 2})  // follow the order from face pose (nose, reye, leye)
    {
      dlib::vector<double,2> p;
      p.x() = (padding+mean_face_shape_x[i])/(2*padding+1);
      p.y() = (padding+mean_face_shape_y[i])/(2*padding+1);
      from_points.push_back(p*size);
      to_points.push_back(shape.part(i));
    }

    face_chip_details = chip_details(from_points, to_points, chip_dims(size,size));
    //cout << "chip angle: " << to_string(face_chip_details.angle) << endl;

    const rgb_pixel color_r(255,0,0);
    point_transform_affine pta = get_mapping_to_chip(face_chip_details);
    auto leye_new = pta(shape.part(2));
    auto nose_new = pta(shape.part(3));
    auto reye_new = pta(shape.part(5));


    // extract the face chip
    matrix<rgb_pixel> face_chip;
    extract_image_chip(img, face_chip_details, face_chip);

    face_chips.push_back(face_chip);

    // save the face chip_dims
    boost::filesystem::path orig_path(argv[1]);
    //std::string orig_ext = orig_path.extension().string();
    std::string chip_file = orig_path.stem().string() + "_chip_" + to_string(chipcount) + ".jpg";

    cout << "Extracted chip " << to_string(chipcount) << endl;

    chipcount++;
  }

  // FACE EMBEDDING AND IDENTIFY BEAR
  // Embedding Network
  net_type net;
  deserialize("metric_network_renset.dat") >> net;
  anet_type embedding_net = net;

  // SVM Classifier
  typedef matrix<float,128,1> sample_type;
  typedef linear_kernel<sample_type> kernel_type;
  typedef one_vs_one_trainer<any_trainer<sample_type> > ovo_trainer;
  one_vs_one_decision_function<ovo_trainer,
  decision_function<kernel_type>    // This is the output of the linear_trainer
  > df;
  std::vector <string> ids;
  double id_idx;
  deserialize("bear_svm.dat") >> df;
  deserialize("bear_svm_ids.dat") >> ids;

  for (auto&& chip : face_chips)
  {
    matrix<float,0,1> embedded = embedding_net(chip);
    id_idx = df(embedded);
    cout << "predicted label: "<< id_idx << " == " << ids[id_idx] << endl;
  }
}

catch(std::exception& e)
{
  cout << e.what() << endl;
}
