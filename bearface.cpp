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
#include <boost/algorithm/string.hpp>
#include <iostream>
#include <dlib/dnn.h>
#include <dlib/data_io.h>
#include <dlib/image_processing.h>
#include <dlib/gui_widgets.h>
#include <dlib/image_io.h>
// #include <ctype.h>
// #include <stdio.h>
// #include <stdlib.h>
#include <unistd.h>

using namespace std;
using namespace dlib;

// ----------------------------------------------------------------------------------------

template <long num_filters, typename SUBNET> using con5d = con<num_filters,5,5,2,2,SUBNET>;
template <long num_filters, typename SUBNET> using con5  = con<num_filters,5,5,1,1,SUBNET>;

template <typename SUBNET> using downsampler  = relu<affine<con5d<32, relu<affine<con5d<32, relu<affine<con5d<16,SUBNET>>>>>>>>>;
template <typename SUBNET> using rcon5  = relu<affine<con5<45,SUBNET>>>;

using net_type = loss_mmod<con<1,9,9,1,1,rcon5<rcon5<rcon5<downsampler<input_rgb_image_pyramid<pyramid_down<6>>>>>>>>;

// ----------------------------------------------------------------------------------------

const unsigned MAX_LONG_SIDE = 4800;
const unsigned MAX_SHORT_SIDE = 3200;
const unsigned MAX_SIZE = MAX_LONG_SIDE*MAX_SHORT_SIDE;

// Find Faces and face landmarks
void find_faces (
  net_type& net,
  shape_predictor& sp,
  matrix<rgb_pixel>& img,
  std::vector<image_dataset_metadata::box>& faces,
  std::string bearID
)
{
  bool bUpscaled = false;
  bool bDownscaled = false;
  float pxRatio;

  // cout << "Image size: " << img.size() << " NR: " << img.nr() << " NC: " << img.nc() << endl;

  // If the image is too big (this is a memory constraint), we need to downsample it
  if (img.size() > (MAX_SIZE))
  {
    if (img.nc() > img.nr())
    {
      if (((float)MAX_LONG_SIDE / (float)img.nc()) < (float)MAX_SHORT_SIDE / (float)img.nr())
        pxRatio = (float)MAX_LONG_SIDE / (float)img.nc();
      else
        pxRatio = (float)MAX_SHORT_SIDE / (float)img.nr();
    }
    else
    {
      if (((float)MAX_LONG_SIDE / (float)img.nr()) < (float)MAX_SHORT_SIDE / (float)img.nc())
        pxRatio = (float)MAX_LONG_SIDE / (float)img.nr();
      else
        pxRatio = (float)MAX_SHORT_SIDE / (float)img.nc();
    }
    cout << "File TOO BIG" << " Ratio: " << pxRatio << endl;
    //cout << "New X: " << (int)(img.nc() * pxRatio) << " New Y: " << (int)(img.nr() * pxRatio) << endl;
    matrix<rgb_pixel> smimg((int)(img.nr() * pxRatio), (int)(img.nc() * pxRatio));
    resize_image(img, smimg);
    //resize_image((double)2.0, img);
    //resize_image(img, smimg, interpolate_billinear());
    //resize_image((double)(MAX_SIZE / img.size()), itImage);
    //pyramid_down(img);
    //cout << "Rescaled image size: " << smimg.size() << " NR: " << smimg.nr() << " NC: " << smimg.nc() << endl;
    bDownscaled = true;
    img = smimg;
    //return;
  }

  // Upsampling the image will allow us to find smaller faces but will use more
  // computational resources.
  //pyramid_up(img);

  // Find faces
  auto dets = net(img);

  // if no faces, try with upscaling
  if ((dets.size() == 0) && !bDownscaled)
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
      else if (bDownscaled)
      {
        cout << "File was downscaled" << endl;
        // TODO figure out the scale factor from pyramid_up
        face.rect.set_left((int)((float)d.rect.left() / pxRatio));
        face.rect.set_top((int)((float)d.rect.top() / pxRatio));
        face.rect.set_right((int)((float)d.rect.right() / pxRatio));
        face.rect.set_bottom((int)((float)d.rect.bottom() / pxRatio));
        face.parts["top"].x()  = (int)((float)shape.part(0).x() / pxRatio);
        face.parts["top"].y()  = (int)((float)shape.part(0).y() / pxRatio);
        face.parts["lear"].x() = (int)((float)shape.part(1).x() / pxRatio);
        face.parts["lear"].y() = (int)((float)shape.part(1).y() / pxRatio);
        face.parts["leye"].x() = (int)((float)shape.part(2).x() / pxRatio);
        face.parts["leye"].y() = (int)((float)shape.part(2).y() / pxRatio);
        face.parts["nose"].x() = (int)((float)shape.part(3).x() / pxRatio);
        face.parts["nose"].y() = (int)((float)shape.part(3).y() / pxRatio);
        face.parts["rear"].x() = (int)((float)shape.part(4).x() / pxRatio);
        face.parts["rear"].y() = (int)((float)shape.part(4).y() / pxRatio);
        face.parts["reye"].x() = (int)((float)shape.part(5).x() / pxRatio);
        face.parts["reye"].y() = (int)((float)shape.part(5).y() / pxRatio);
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
	  face.label = bearID;
      faces.push_back(face);
  }
}

// ----------------------------------------------------------------------------------------

int main(int argc, char** argv) try
{
    //image_window win_wireframe;
    int total_faces = 0;

	//----------------------------------------------------------------------
	int aflag = 0;
	int bflag = 0;
	char *lvalue = NULL;
	int index;
	int c;
	std::string bearID;
  bool bLabelFixed = false;

	while ((c = getopt (argc, argv, "l:")) != -1)
	  switch (c)
		{
		case 'l':
		  bearID = optarg;
      bLabelFixed = true;
		  break;
		default:
		  cout << "unrecognized argument: " << c << endl;
		  cout << "\nUsage:" << endl;
		  cout << "\t./bearface [-l label] mmod_dog_hipsterizer.dat <source_img_file>" << endl;
		  cout << "\nDetect bear faces in images.\n" << endl;
		  cout << "mmod_dog_hipsterizer.dat can be found at:\n";
		  cout << "\t /home/bearid/dlib-data/mmod_dog_hipsterizer.dat\n" << endl;
		  return 0;
    }
	if ((argc - optind) != 2)
	{
		cout << "\nUsage:" << endl;
		cout << "\t./bearface [-l label] mmod_dog_hipsterizer.dat <source_img_file>" << endl;
		cout << "\nDetect bear faces in images.\n" << endl;
		cout << "mmod_dog_hipsterizer.dat can be found at:\n";
		cout << "\t /home/bearid/dlib-data/mmod_dog_hipsterizer.dat\n" << endl;
		return 0;
	}
	std::string network = argv[optind];
	std::string imgs_file = argv[optind+1];

    // load the models as well as glasses and mustache.
    net_type net;
    shape_predictor sp;
    matrix<rgb_alpha_pixel> glasses, mustache;
    deserialize(network) >> net >> sp >> glasses >> mustache;

    // Load XML metadata file
    dlib::image_dataset_metadata::dataset data;
    load_image_dataset_metadata(data, imgs_file);

    //Handle list of images
	std::vector <string> fields;
    for (int i = 0; i < data.images.size(); ++i)
    {
        matrix<rgb_pixel> img;

        cout << data.images[i].filename.c_str() << "...";
        load_image(img, data.images[i].filename.c_str());

		if (!bLabelFixed)
		{
			std::string fullpathfile = data.images[i].filename;
			boost::split( fields, fullpathfile, boost::is_any_of( "/" ));
			bearID = fields[fields.size() - 2];
		}
        std::vector<image_dataset_metadata::box> faces;
        find_faces (net, sp, img, faces, bearID);
        data.images[i].boxes = faces;

        cout << "faces found: " << to_string(faces.size()) << endl;
        total_faces += faces.size();
    }
    cout << "Total faces found: " << total_faces << endl;
	boost::filesystem::path orig_path(imgs_file);
	std::string faces_file = orig_path.stem().string() + "_faces.xml";
    save_image_dataset_metadata(data, faces_file);
    if (!bLabelFixed)
    {
      cout << "\n\tGenerated with no label: " << faces_file << "\n" << endl;
    }
    else
    {
      cout << "\n\tGenerated with label " << bearID <<  ": " << faces_file << "\n" << endl;
    }
}
catch(std::exception& e)
{
    cout << e.what() << endl;
}
