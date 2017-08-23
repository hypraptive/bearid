// The contents of this file are licensed under the MIT license.
// See LICENSE.txt for more information.

/*
  This program takes an XML metadata file produced by bearface or imglab
  and outputs a set of face chips for each listed image. The steps are:

    - align each face based on the landmarks
    - crop the faces to form face chips
*/

#include <boost/filesystem.hpp>
#include <boost/property_tree/ptree.hpp>
#include <boost/property_tree/xml_parser.hpp>
#include <iostream>
#include <dlib/dnn.h>
#include <dlib/data_io.h>
#include <dlib/image_processing.h>
#include <dlib/gui_widgets.h>


using namespace std;
using namespace dlib;
using boost::property_tree::ptree;
using boost::property_tree::write_xml;
using boost::property_tree::xml_writer_settings;

image_window g_win_chip;
const unsigned long g_chip_size = 150;
const unsigned int chip_x = 4;
matrix<rgb_pixel> g_composite_features(g_chip_size*chip_x, g_chip_size*chip_x);

ptree g_xml_tree;

//--------------------------------------------------
// initialize xml
//--------------------------------------------------
int xml_add_headers ()
{
    g_xml_tree.add("dataset.name", "bearid dataset");
    g_xml_tree.add("dataset.comment", "Created by bearchip");
	return 0;
}

//--------------------------------------------------
// add chip to xml
//  <chip file='/home/bears/... chunk_chip_0.jpg'>
//--------------------------------------------------
ptree xml_add_chip (std::string chipname)
{
	// ptree& chip = g_xml_chips.add ("chip.<xmlattr>.file", chipname); // call doesn't return usablel chip. bug??
	ptree chip;
	return chip;
}

int xml_add_chip_part (ptree &chip, std::string part_name, int x, int y)
{
	ptree &chip_part = chip.add ("part.<xmlattr>.name", part_name);
	chip_part.add ("<xmlattr>.x", x);
	chip_part.add ("<xmlattr>.y", y);
	return 0;
}

int xml_write_file (ptree g_xml_tree, std::string xml_filename)
{
    // write_xml(xml_filename, g_xml_tree,
        // std::locale(), xml_writer_settings<char>(' ', 4));

    write_xml(xml_filename, g_xml_tree,std::locale(),
	    boost::property_tree::xml_writer_make_settings<std::string>(' ', 4, "utf-8"));

    return 0;
}

//--------------------------------------------------
// add specified circle to g_composite_features
//--------------------------------------------------
void add_overlay_circle (
	point p,
	int radius,
	rgb_pixel color
)
{
	int i,j;
	int y = p.x();
	int x = p.y();
	for (i=0; i <= radius; i++)
	{
		j = round (sqrt ((float) ((radius*radius) - (i*i))));
		g_composite_features (x+i,y+j) = color;
		g_composite_features (x+i,y-j) = color;
		g_composite_features (x-i,y+j) = color;
		g_composite_features (x-i,y-j) = color;
	}
}

//------------------------------------------------------------------------
// Find Face Chips
//  input : vector of boxes (box around bear face & coords of face features
//  output: vector of facechips.
//  actions:write out 
//------------------------------------------------------------------------
std::vector<matrix<rgb_pixel>> find_chips (
  std::vector<image_dataset_metadata::box>& boxes,
  matrix<rgb_pixel>& img,
  std::vector<dlib::vector<double,2> >& face_features // for all features
)
{
  std::vector<matrix<rgb_pixel>> faces;
  point part[6];
  // display face lear, rear, nose on uniform grey canvas
  std::vector<image_window::overlay_circle> chip_circles;
  const rgb_pixel color_r(255,0,0);
  const rgb_pixel color_g(0,255,0);
  const rgb_pixel color_b(0,0,255);
  //---------------
  for (auto&& b : boxes)  // for each face
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
          from_points.push_back(p*g_chip_size);
          to_points.push_back(part[i]);
          //cout << "from:" << p*g_chip_size << endl;
          //cout << "to:" << shape.part(i) << endl;
      }

      face_chip_details = chip_details(from_points, to_points, chip_dims(g_chip_size,g_chip_size));

	  // ---------------------------------------
	  // get mapping for display
      point_transform_affine pta = get_mapping_to_chip(face_chip_details);
      auto leye_new = pta(part[2])*chip_x;
      auto nose_new = pta(part[3])*chip_x;
      auto reye_new = pta(part[5])*chip_x;
	  face_features.push_back (leye_new);
	  face_features.push_back (nose_new);
	  face_features.push_back (reye_new);

      chip_circles.push_back(image_window::overlay_circle(reye_new, 3, color_r));
	  add_overlay_circle(reye_new,3, color_r);
      chip_circles.push_back(image_window::overlay_circle(leye_new, 3, color_b));
	  add_overlay_circle(leye_new, 3, color_b);
      chip_circles.push_back(image_window::overlay_circle(nose_new, 3, color_g));
	  add_overlay_circle(nose_new, 3, color_g);
	  g_win_chip.add_overlay (chip_circles);

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
	ptree &chips = g_xml_tree.add ("dataset.chips", "");
	//--------------

	//--------------
    dlib::image_dataset_metadata::dataset data;
    load_image_dataset_metadata(data, argv[1]);

	// create image for composite of tranformations
    const rgb_pixel color_grey(50,50,50);
    for (int i=0; i < g_chip_size*chip_x; i++)
    {
        for (int j=0; j < g_chip_size*chip_x; j++)
	    {
            g_composite_features(i, j) = color_grey;
	    }
    }
    // g_win_chip.set_image(g_composite_features);  // display composite
	//--------------------------------------------- 


    // Now process each image and extract a face chip using the metadata
    for (int i = 0; i < data.images.size(); ++i)
    {
        matrix<rgb_pixel> img;
		std::vector<dlib::vector<double,2> > face_features; // for all features

        boost::filesystem::path orig_path(data.images[i].filename.c_str());
        std::string orig_ext = orig_path.extension().string();

        cout << "File: " << orig_path.string() << endl;
        cout << "Image type " << orig_ext << endl;

        load_image(img, data.images[i].filename.c_str());

        std::vector<matrix<rgb_pixel>> faces;
        faces = find_chips (data.images[i].boxes, img, face_features);
        cout << "Faces found: " << to_string(faces.size()) << endl;
		/*  check for more than one face.  shouldn't happen yet
		if (faces.size() > 1)
		{
			cout << "faces found: " << faces.size() << endl;
			cin.get();
		}
		*/
        total_faces += faces.size();
        for (size_t i = 0; i < faces.size(); ++i)
        {
          // save the face chip_dims
          std::string chip_file = orig_path.stem().string() + "_chip_" + to_string(i) + ".jpg";

		  ptree &xml_chip = chips.add ("chip", "");
		  xml_chip.add ("<xmlattr>.file", chip_file);
		  // write image out to chips.xml
		  int j = i*3; // # of features we care about {leye, nose, reye}
		  auto leye = face_features[j];
		  auto nose = face_features[j+1];
		  auto reye = face_features[j+2];
		  // xml_add_chip_part (g_cur_chip, "leye", leye.x(), leye.y());
		  ptree &xml_part_leye = xml_chip.add ("part", "");
		  xml_part_leye.add ("<xmlattr>.name", "leye");
		  xml_part_leye.add ("<xmlattr>.x", (int)leye.x());
		  xml_part_leye.add ("<xmlattr>.y", (int)leye.y());
		  ptree &xml_part_nose = xml_chip.add ("part", "");
		  xml_part_nose.add ("<xmlattr>.name", "nose");
		  xml_part_nose.add ("<xmlattr>.x", (int)nose.x());
		  xml_part_nose.add ("<xmlattr>.y", (int)nose.y());
		  ptree &xml_part_reye = xml_chip.add ("part", "");
		  xml_part_reye.add ("<xmlattr>.name", "reye");
		  xml_part_reye.add ("<xmlattr>.x", (int)reye.x());
		  xml_part_reye.add ("<xmlattr>.y", (int)reye.y());
		  // xml_add_chip_part (g_cur_chip, "reye", reye.x(), reye.y());
		  // xml_add_chip_part (g_cur_chip, "nose", nose.x(), nose.y());
          cout << argv[i] << ": extracted chip " << to_string(i) << " to " << chip_file << endl;
          save_jpeg(faces[i], chip_file, 95);
        }

    }
	boost::filesystem::path xml_file (argv[1]);
	std::string chips_jpg_file = xml_file.filename().stem().string() + "_chip_composite.jpg";
	std::string chips_xml_file = xml_file.filename().stem().string() + "_chips.xml";
    save_jpeg(g_composite_features, chips_jpg_file, 95);
    cout << "Total faces found: " << total_faces << endl;
	// cout << "Hit return to finish." << endl;

	xml_add_headers (); // put at end since writing reverse order added
	xml_write_file (g_xml_tree, chips_xml_file);
	cout << "\ngenerated: \n\t" << chips_xml_file << "\n\t" << chips_jpg_file << "\n" << endl;
	// cin.get();
}
catch(std::exception& e)
{
    cout << e.what() << endl;
}
