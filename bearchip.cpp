// The contents of this file are licensed under the MIT license.
// See LICENSE.txt for more information.

/*
  This program takes a set of photos or videos of brown bears and outputs a set
  of face chips. The steps are:
  
    - find all faces and face landmarks
    - align each face based on the landmarks
    - crop the faces to form face chips

  The face detector uses a pretrained CNN from the dlib example:

  https://github.com/davisking/dlib/blob/master/examples/dnn_mmod_dog_hipsterizer.cpp

  While the model was trained for dogs, it works reasonably well for bears. The
  pretrained CNN data can be found here:

  http://dlib.net/files/mmod_dog_hipsterizer.dat.bz2

  Videos are handled using OpenCV's VideoCapture module to extract frames.
*/

#include <boost/filesystem.hpp>
#include <iostream>
#include <dlib/dnn.h>
#include <dlib/data_io.h>
#include <dlib/image_processing.h>
#include <dlib/gui_widgets.h>
#include <dlib/opencv.h>
#include <opencv2/opencv.hpp>


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

// Find Face Chips
std::vector<matrix<rgb_pixel>> find_face_chips (
  net_type& net,
  shape_predictor& sp,
  matrix<rgb_pixel>& img
)
{
  //image_window win1(glasses);
  //image_window win2(mustache);
  //image_window win_wireframe;
  //image_window win_chip;
  //image_window win_hipster;
  std::vector<matrix<rgb_pixel>> faces;

  if (img.size() > (MAX_SIZE))
  {
    cout << "File TOO BIG" << endl;
    return(faces);
  }

  // Upsampling the image will allow us to find smaller faces but will use more
  // computational resources.
  //pyramid_up(img);

  auto dets = net(img);
  //win_wireframe.clear_overlay();
  //win_wireframe.set_image(img);
  // We will also draw a wireframe on each face so you can see where the
  // shape_predictor is identifying face landmarks.
  //std::vector<image_window::overlay_line> lines;
  //cout << "dets size: " << dets.size() << endl;

  // if no faces, try with upscaling
  if (dets.size() == 0)
  {
    if (img.size() > (MAX_SIZE/4))
    {
      //cout << "File TOO BIG to UPSCALE" << endl;
      return(faces);
    }

    pyramid_up(img);
    //cout << "File UPSCALED" << endl;
    dets = net(img);

    if (dets.size() == 0)
    {
      //cout << "File has no faces" << endl;
      return(faces);
    }
  }

  // if more than one face, we exit
  //if (dets.size() > 1)
  //{
  //  cout << argv[i] << upscaled << ": has too many faces = " << dets.size() << endl;
  //  continue;
  //}

  for (auto&& d : dets)
  {
      std::vector<image_window::overlay_line> chip_lines;
      // print the rectangle
      //cout << "Rectangle:" << d.rect << endl;

      // get the landmarks for this face
      auto shape = sp(img, d.rect);

      const rgb_pixel color(0,255,0);
      auto top  = shape.part(0);
      auto lear = shape.part(1);
      auto leye = shape.part(2);
      auto nose = shape.part(3);
      auto rear = shape.part(4);
      auto reye = shape.part(5);

      // overlay bounding box
      //win_wireframe.add_overlay(d);

      // Record the lines needed for the face wire frame.
      //lines.push_back(image_window::overlay_line(leye, nose, color));
      //lines.push_back(image_window::overlay_line(nose, reye, color));
      //lines.push_back(image_window::overlay_line(reye, leye, color));
      //lines.push_back(image_window::overlay_line(reye, rear, color));
      //lines.push_back(image_window::overlay_line(rear, top, color));
      //lines.push_back(image_window::overlay_line(top, lear,  color));
      //lines.push_back(image_window::overlay_line(lear, leye,  color));

      // chip_details based on get_face_chip_details
      //const double mean_face_shape_x[] = { 0, 0, 0.65, 0.50, 0, 0.35 };
      //const double mean_face_shape_y[] = { 0, 0, 0.50, 0.65, 0, 0.50 };
      const double mean_face_shape_x[] = { 0, 0, 0.62, 0.50, 0, 0.38 };
      const double mean_face_shape_y[] = { 0, 0, 0.48, 0.70, 0, 0.48 };
      //const double mean_face_shape_x[] = { 0, 0, 0.62, 0.54, 0, 0.38 }; // derrived from HOG image
      //const double mean_face_shape_y[] = { 0, 0, 0.45, 0.62, 0, 0.45 }; // derrived from HOG image
      const unsigned long size = 150;
      //const double padding = 0.0;
      const double padding = -0.12; // using negative padding so we don't have to adjust mean face shape
      chip_details face_chip_details;

      std::vector<dlib::vector<double,2> > from_points, to_points;
      //for (unsigned long i : {3, 5, 2})  // follow the order from face pose (nose, reye, leye)
      for (unsigned long i : {5, 2}) // follow order from face pose (reye, leye) EYES_ONLY
      {
          // Ignore top and ears
          if ((i == 0) || (i == 1) || (i == 4))
              continue;

          dlib::vector<double,2> p;
          p.x() = (padding+mean_face_shape_x[i])/(2*padding+1);
          p.y() = (padding+mean_face_shape_y[i])/(2*padding+1);
          from_points.push_back(p*size);
          to_points.push_back(shape.part(i));
          //cout << "from:" << p*size << endl;
          //cout << "to:" << shape.part(i) << endl;
      }

      face_chip_details = chip_details(from_points, to_points, chip_dims(size,size));
      //cout << "chip angle: " << to_string(face_chip_details.angle) << endl;
      //chip_lines.push_back(image_window::overlay_line(from_points[0], from_points[1],  color));
      //chip_lines.push_back(image_window::overlay_line(from_points[1], from_points[2],  color));
      //chip_lines.push_back(image_window::overlay_line(from_points[2], from_points[0],  color));

      const rgb_pixel color_r(255,0,0);
      point_transform_affine pta = get_mapping_to_chip(face_chip_details);
      auto leye_new = pta(shape.part(2));
      //auto nose_new = pta(shape.part(3)); // EYES_ONLY
      auto reye_new = pta(shape.part(5));
      //chip_lines.push_back(image_window::overlay_line(leye_new, nose_new,  color_r));
      //chip_lines.push_back(image_window::overlay_line(nose_new, reye_new,  color_r));
      //chip_lines.push_back(image_window::overlay_line(reye_new, leye_new,  color_r));


      // extract the face chip
      matrix<rgb_pixel> face_chip;
      extract_image_chip(img, face_chip_details, face_chip);
      //win_chip.clear_overlay();

      // save the face chip
      faces.push_back(face_chip);

      //win_chip.set_image(face_chip);
      //win_chip.add_overlay(chip_lines);
  }
  return(faces);
}

// ----------------------------------------------------------------------------------------

int main(int argc, char** argv) try
{
    //image_window win_wireframe;
    int total_faces = 0;

    if (argc < 3)
    {
        cout << "Call this program like this:" << endl;
        cout << "./bearchip mmod_dog_hipsterizer.dat <image_file>" << endl;
        cout << "\nYou can get the mmod_dog_hipsterizer.dat file from:\n";
        cout << "http://dlib.net/files/mmod_dog_hipsterizer.dat.bz2" << endl;
        return 0;
    }


    // load the models as well as glasses and mustache.
    net_type net;
    shape_predictor sp;
    matrix<rgb_alpha_pixel> glasses, mustache;
    deserialize(argv[1]) >> net >> sp >> glasses >> mustache;
    //serialize("doghip_net.dat") << net;
    //serialize("doghip_sp.dat") << sp;
    //pyramid_up(glasses);
    //pyramid_up(mustache);

    // Now process each image, find bear, and extract a face chip
    for (int i = 2; i < argc; ++i)
    {
        matrix<rgb_pixel> img;

        boost::filesystem::path orig_path(argv[i]);
        std::string orig_ext = orig_path.extension().string();

        cout << "File: " << orig_path.string() << endl;
        // For image files
        if (orig_ext.compare(".jpg") == 0)
        {
          cout << "Image type " << orig_ext << endl;
          load_image(img, argv[i]);
          std::vector<matrix<rgb_pixel>> faces;
          faces = find_face_chips (net, sp, img);
          cout << "Faces found: " << to_string(faces.size()) << endl;
          total_faces += faces.size();
          for (size_t i = 0; i < faces.size(); ++i)
          {
              // save the face chip_dims
              std::string chip_file = orig_path.stem().string() + "_chip_" + to_string(i) + ".jpg";

              cout << argv[i] << ": extracted chip " << to_string(i) << " to " << chip_file << endl;
              save_jpeg(faces[i], chip_file, 95);
          }
        }
        // For Video files
        else if ((orig_ext.compare(".mp4") == 0) || (orig_ext.compare(".AVI") == 0))
        {
          cout << "Video type " << orig_ext << endl;
          cv::VideoCapture cap(argv[i]);
          int frame_num = 0;
          while (cap.isOpened())
          {
            // Grab a frame
            cv::Mat temp;
            if (!cap.read(temp)) break;
            // Turn OpenCV's Mat into something dlib can deal with.  Note that this just
            // wraps the Mat object, it doesn't copy anything.  So cimg is only valid as
            // long as temp is valid.  Also don't do anything to temp that would cause it
            // to reallocate the memory which stores the image as that will make cimg
            // contain dangling pointers.  This basically means you shouldn't modify temp
            // while using cimg.
            assign_image(img, cv_image<bgr_pixel>(temp));
            //win_wireframe.clear_overlay();
            //win_wireframe.set_image(img);
            //cv::cvtColor(temp, temp2, CV_BGR2RGB);
            //cv_image<bgr_pixel> cimg(temp);
            //cv_image<rgb_pixel> cimg(temp2);
            std::vector<matrix<rgb_pixel>> faces;
            faces = find_face_chips (net, sp, img);
            total_faces += faces.size();
            cout << "Frame: " << frame_num << " Faces found: " << to_string(faces.size()) << endl;
            for (size_t i = 0; i < faces.size(); ++i)
            {
                // save the face chip_dims
                std::string chip_file = orig_path.stem().string() + "_fr_" + to_string(frame_num) + "_chip_" + to_string(i) + ".jpg";

                cout << argv[i] << ": extracted chip " << to_string(i) << " to " << chip_file << endl;
                save_jpeg(faces[i], chip_file, 95);
            }
            //cout << "Hit enter to process the next image." << endl;
            //cin.get();
            frame_num++;
          }
        }

        else
        {
          cout << "File type unknown: " << orig_ext << endl;
        }

        //win_wireframe.add_overlay(lines);
        //win_hipster.set_image(img);

        //cout << "Hit enter to process the next image." << endl;
        //cin.get();
    }
    cout << "Total faces found: " << total_faces << endl;
}
catch(std::exception& e)
{
    cout << e.what() << endl;
}
