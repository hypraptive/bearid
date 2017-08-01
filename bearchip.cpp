// The contents of this file are licensed under the MIT license.
// See LICENSE.txt for more information.

/*
  This program takes an XML metadata file produced by bearface or imglab
  and outputs a set of face chips for each listed image. The steps are:

    - align each face based on the landmarks
    - crop the faces to form face chips
*/

#include <boost/filesystem.hpp>
#include <iostream>
#include <dlib/dnn.h>
#include <dlib/data_io.h>
#include <dlib/image_processing.h>
#include <dlib/gui_widgets.h>


using namespace std;
using namespace dlib;

// Find Face Chips
std::vector<matrix<rgb_pixel>> find_chips (
  std::vector<image_dataset_metadata::box>& boxes,
  matrix<rgb_pixel>& img
)
{
  std::vector<matrix<rgb_pixel>> faces;
  point part[6];
  for (auto&& b : boxes)
  {
      part[0] = b.parts["top"];
      part[1] = b.parts["lear"];
      part[2] = b.parts["leye"];
      part[3] = b.parts["nose"];
      part[4] = b.parts["rear"];
      part[5] = b.parts["reye"];

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
          to_points.push_back(part[i]);
          //cout << "from:" << p*size << endl;
          //cout << "to:" << shape.part(i) << endl;
      }

      face_chip_details = chip_details(from_points, to_points, chip_dims(size,size));

      // extract the face chip
      matrix<rgb_pixel> face_chip;
      extract_image_chip(img, face_chip_details, face_chip);

      // save the face chip
      faces.push_back(face_chip);
  }
  return(faces);
}

// ----------------------------------------------------------------------------------------

int main(int argc, char** argv) try
{
    int total_faces = 0;

    if (argc != 2)
    {
        cout << "Call this program like this:" << endl;
        cout << "./bearchip <metadata_file>" << endl;
        return 0;
    }

    // Load XML metadata file
    dlib::image_dataset_metadata::dataset data;
    load_image_dataset_metadata(data, argv[1]);

    // Now process each image and extract a face chip using the metadata
    for (int i = 0; i < data.images.size(); ++i)
    {
        matrix<rgb_pixel> img;

        boost::filesystem::path orig_path(data.images[i].filename.c_str());
        std::string orig_ext = orig_path.extension().string();

        cout << "File: " << orig_path.string() << endl;
        cout << "Image type " << orig_ext << endl;

        load_image(img, data.images[i].filename.c_str());

        std::vector<matrix<rgb_pixel>> faces;
        faces = find_chips (data.images[i].boxes, img);
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
    cout << "Total faces found: " << total_faces << endl;
}
catch(std::exception& e)
{
    cout << e.what() << endl;
}
