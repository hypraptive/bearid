// The contents of this file are licensed under the MIT license.
// See LICENSE.txt for more information.

/*
  This program takes an XML file with a list of photos brown bears, finds all the
  bear faces and the face landmarks then outputs an XML metadata file.

  The input XML file can be generated using "imglab -c". The output file can be
  viewed and edited using imglab.

  The face detector uses a pretrained CNN from the dlib example:

  https://github.com/davisking/dlib/blob/master/examples/dnn_mmod_dog_hipsterizer.cpp

  While the model was trained for dogs, it works reasonably well for bears. The
  pretrained CNN data can be found here:

  http://dlib.net/files/mmod_dog_hipsterizer.dat.bz2
*/

#include <boost/filesystem.hpp>
#include <iostream>
#include <dlib/dnn.h>
#include <dlib/data_io.h>
#include <dlib/image_processing.h>
#include <dlib/gui_widgets.h>


using namespace std;
using namespace dlib;

// ----------------------------------------------------------------------------------------

template <long num_filters, typename SUBNET> using con5d = con<num_filters,5,5,2,2,SUBNET>;
template <long num_filters, typename SUBNET> using con5  = con<num_filters,5,5,1,1,SUBNET>;

template <typename SUBNET> using downsampler  = relu<affine<con5d<32, relu<affine<con5d<32, relu<affine<con5d<16,SUBNET>>>>>>>>>;
template <typename SUBNET> using rcon5  = relu<affine<con5<45,SUBNET>>>;

using net_type = loss_mmod<con<1,9,9,1,1,rcon5<rcon5<rcon5<downsampler<input_rgb_image_pyramid<pyramid_down<6>>>>>>>>;

// ----------------------------------------------------------------------------------------

const unsigned MAX_SIZE = 5000*3500;

// Find Faces and face landmarks
void find_faces (
  net_type& net,
  shape_predictor& sp,
  matrix<rgb_pixel>& img,
  std::vector<image_dataset_metadata::box>& faces
)
{
  bool bUpscaled = false;

  cout << "Image size: " << img.size() << endl;
  if (img.size() > (MAX_SIZE))
  {
    cout << "File TOO BIG" << endl;
    return;
  }

  // Upsampling the image will allow us to find smaller faces but will use more
  // computational resources.
  //pyramid_up(img);

  // Find faces
  auto dets = net(img);

  // if no faces, try with upscaling
  if (dets.size() == 0)
  {
    if (img.size() > (MAX_SIZE/4))
    {
      //cout << "File TOO BIG to UPSCALE" << endl;
      return;
    }

    pyramid_up(img);
    //cout << "File UPSCALED" << endl;
    dets = net(img);

    if (dets.size() == 0)
    {
      //cout << "File has no faces" << endl;
      return;
    }
    cout << "Upscaled image size: " << img.size() << endl;
    bUpscaled = true;
  }

  // For each face, find the face landmarks
  for (auto&& d : dets)
  {
      // get the landmarks for this face
      auto shape = sp(img, d.rect);

      // fill in the data to faces
      image_dataset_metadata::box face;
      if (bUpscaled)
      {
        cout << "File was upscaled" << endl;
        // TODO figure out the scale factor from pyramid_up
        face.rect.set_left(d.rect.left() / 2);
        face.rect.set_top(d.rect.top() / 2);
        face.rect.set_right(d.rect.right() / 2);
        face.rect.set_bottom(d.rect.bottom() / 2);
        face.parts["top"].x()  = shape.part(0).x() / 2;
        face.parts["top"].y()  = shape.part(0).y() / 2;
        face.parts["lear"].x() = shape.part(1).x() / 2;
        face.parts["lear"].y() = shape.part(1).y() / 2;
        face.parts["leye"].x() = shape.part(2).x() / 2;
        face.parts["leye"].y() = shape.part(2).y() / 2;
        face.parts["nose"].x() = shape.part(3).x() / 2;
        face.parts["nose"].y() = shape.part(3).y() / 2;
        face.parts["rear"].x() = shape.part(4).x() / 2;
        face.parts["rear"].y() = shape.part(4).y() / 2;
        face.parts["reye"].x() = shape.part(5).x() / 2;
        face.parts["reye"].y() = shape.part(5).y() / 2;
      }
      else
      {
        face.rect = d.rect;
        face.parts["top"]  = shape.part(0);
        face.parts["lear"] = shape.part(1);
        face.parts["leye"] = shape.part(2);
        face.parts["nose"] = shape.part(3);
        face.parts["rear"] = shape.part(4);
        face.parts["reye"] = shape.part(5);
      }
      faces.push_back(face);
  }
}

// ----------------------------------------------------------------------------------------

int main(int argc, char** argv) try
{
    //image_window win_wireframe;
    int total_faces = 0;

    if (argc != 3)
    {
        cout << "Call this program like this:" << endl;
        cout << "./bearface mmod_dog_hipsterizer.dat <metadata_file>" << endl;
        cout << "\nYou can get the mmod_dog_hipsterizer.dat file from:\n";
        cout << "http://dlib.net/files/mmod_dog_hipsterizer.dat.bz2" << endl;
        return 0;
    }


    // load the models as well as glasses and mustache.
    net_type net;
    shape_predictor sp;
    matrix<rgb_alpha_pixel> glasses, mustache;
    deserialize(argv[1]) >> net >> sp >> glasses >> mustache;

    // Load XML metadata file
    dlib::image_dataset_metadata::dataset data;
    load_image_dataset_metadata(data, argv[2]);

    //Handle list of images
    for (int i = 0; i < data.images.size(); ++i)
    {
        matrix<rgb_pixel> img;

        cout << "File: " << data.images[i].filename.c_str() << endl;
        load_image(img, data.images[i].filename.c_str());

        std::vector<image_dataset_metadata::box> faces;
        find_faces (net, sp, img, faces);
        data.images[i].boxes = faces;

        cout << "Faces found: " << to_string(faces.size()) << endl;
        total_faces += faces.size();
    }
    cout << "Total faces found: " << total_faces << endl;
    save_image_dataset_metadata(data, "faces.xml");
}
catch(std::exception& e)
{
    cout << e.what() << endl;
}
