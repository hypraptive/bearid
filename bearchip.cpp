// The contents of this file are licensed under the MIT license.
// See LICENSE.txt for more information.

/*
  This program takes an XML metadata file produced by bearface or imglab
  and outputs a set of face chips for each listed image. The steps are:

    - align each face based on the landmarks
    - crop the faces to form face chips
*/

#include <dlib/cmd_line_parser.h>
#include <boost/filesystem.hpp>
#include <boost/algorithm/string.hpp>
#include <boost/property_tree/ptree.hpp>
#include <boost/property_tree/xml_parser.hpp>
#include <iostream>
#include <ctime>
#include <dlib/dnn.h>
#include <dlib/data_io.h>
#include <dlib/image_processing.h>
#include <dlib/gui_widgets.h>


using namespace std;
using namespace dlib;
using namespace boost::algorithm;
using boost::property_tree::ptree;
using boost::property_tree::write_xml;
using boost::property_tree::xml_writer_settings;

// WIN: image_window g_win_chip;
const unsigned long g_chip_size = 150;
const unsigned int chip_x = 4;
matrix<rgb_pixel> g_composite_features(g_chip_size*chip_x, g_chip_size*chip_x);
const unsigned int g_feature_radius = 3;

ptree g_xml_tree;

//--------------------------------------------------
// initialize xml
//--------------------------------------------------
int xml_add_headers (int argc, char** argv)
{
	time_t rawtime;
	struct tm * timeinfo;
	char buffer[80];
	std::string info_str;
	std::string prog_command;

	time (&rawtime);
	timeinfo = localtime(&rawtime);

	strftime(buffer,sizeof(buffer),"%Y%m%d%H%M",timeinfo);
	info_str = "Created on: ";
	info_str += buffer;
	for (int i=0; i<argc; i++)
	{
		prog_command += ' ';
		prog_command += argv[i];
	}

    g_xml_tree.add("dataset.name", "bearid dataset");
    g_xml_tree.add("dataset.comment", "Created by bearchip");
    g_xml_tree.add("dataset.info", info_str);
    g_xml_tree.add("dataset.command", prog_command);
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
	if (x < radius)
		x = radius;
	if (y < radius)
		y = radius;
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
//  set negative values to 0.
//------------------------------------------------------------------------
void clean_xy (dlib::vector<double, 2l>& part)
{
	if (part.x () < 0)
	{
		part.x () = 0;
	}
	if (part.y () < 0)
	{
		part.y () = 0;
	}
}


//------------------------------------------------------------------------
// Find Face Chips
//  args: : vector of boxes (bounds bear face & coords of face features)
//  		image of bear
//			transform_features: return features used
//			face_features: return transformed features
//  return: vector of facechips.
//  actions:write out
//------------------------------------------------------------------------
std::vector<matrix<rgb_pixel>> find_chips (
  std::vector<image_dataset_metadata::box>& boxes,
  matrix<rgb_pixel>& img,
  const float padding,
std::vector<float> eyes_loc,
  std::string& transform_features,    // features used in transformation
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
  float nose_x=.50, nose_y=.70;
  float leye_x=eyes_loc[0], leye_y=eyes_loc[1];
  float reye_x=eyes_loc[2], reye_y=eyes_loc[3];
  std::string bearID;
  //---------------
  for (auto&& b : boxes)  // for each face
  {
      part[0] = b.parts["head_top"];
      part[1] = b.parts["lear"];
      part[2] = b.parts["leye"];
      part[3] = b.parts["nose"];
      part[4] = b.parts["rear"];
      part[5] = b.parts["reye"];

      // chip_details based on get_face_chip_details
      const double mean_face_shape_x[] = { 0, 0, leye_x, nose_x, 0, reye_x };
      const double mean_face_shape_y[] = { 0, 0, leye_y, nose_y, 0, reye_y };
      //const double mean_face_shape_x[] = { 0, 0, 0.62, 0.54, 0, 0.38 }; // derrived from HOG image
      //const double mean_face_shape_y[] = { 0, 0, 0.45, 0.62, 0, 0.45 }; // derrived from HOG image
      // double padding = -0.12; // using negative padding so we don't have to adjust mean face shape
      chip_details face_chip_details;

      std::vector<dlib::vector<double,2> > from_points, to_points;
      //for (unsigned long i : {3, 5, 2})  // follow the order from face pose (nose, reye, leye)
	  // --------------------!!!!!!!
	  transform_features = "reye leye";
	  // --------------------!!!!!!!
	  // MAKE SURE transform_features REFLECTS FEATURES USED BELOW
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
      auto leye = pta(part[2]);
      auto nose = pta(part[3]);
      auto reye = pta(part[5]);
	  clean_xy (leye);
	  clean_xy (reye);
	  clean_xy (nose);
      auto leye_new = leye*chip_x;
      auto nose_new = nose*chip_x;
      nose_new.x() = std::min(nose_new.x(), (double)(g_chip_size*chip_x - g_feature_radius - 1));
      nose_new.y() = std::min(nose_new.y(), (double)(g_chip_size*chip_x - g_feature_radius - 1));
	  if (nose_new.y() < 0)
	  	nose_new.y() = g_feature_radius;
	  if (nose_new.x() < 0)
	  	nose_new.x() = g_feature_radius;
      auto reye_new = reye*chip_x;
	  face_features.push_back (leye);
	  face_features.push_back (nose);
	  face_features.push_back (reye);

      chip_circles.push_back(image_window::overlay_circle(reye_new, g_feature_radius, color_r));
	  add_overlay_circle(reye_new, g_feature_radius, color_r);
      chip_circles.push_back(image_window::overlay_circle(leye_new, g_feature_radius, color_b));
	  add_overlay_circle(leye_new, g_feature_radius, color_b);
      chip_circles.push_back(image_window::overlay_circle(nose_new, g_feature_radius, color_g));
	  add_overlay_circle(nose_new, g_feature_radius, color_g);
	  // WIN: g_win_chip.add_overlay (chip_circles);

      // extract the face chip
      matrix<rgb_pixel> face_chip;
      extract_image_chip(img, face_chip_details, face_chip);

      // save the face chip
      faces.push_back(face_chip);
  }
  return(faces);
}

// -----------------------------------------------------------------------------
// -----------------------------------------------------------------------------
int xml_add_part (ptree &part, std::string name, point pt)
{
	part.add ("<xmlattr>.name", name);
	part.add ("<xmlattr>.x", (int)pt.x());
	part.add ("<xmlattr>.y", (int)pt.y());
	return 0;
}

// -----------------------------------------------------------------------------
	/*
	<source file='/home//bearsbritishColumbia//bc_coco/IMG_4654.JPG'>
	  <box top='1267' left='1714' width='341' height='341'>
		<label>bc_coco</label>
		<part name='lear' x='1959' y='1311'/>
		<part name='leye' x='1946' y='1391'/>
		<part name='nose' x='1933' y='1536'/>
		<part name='rear' x='1776' y='1311'/>
		<part name='reye' x='1814' y='1403'/>
		<part name='head_top' x='1873' y='1276'/>
	  </box>
	</source>
	*/
// -----------------------------------------------------------------------------
int xml_populate_chip_source (ptree &xml_chip, image_dataset_metadata::box box, std::string src_file)
{
	point top = box.parts["head_top"];
	point lear = box.parts["lear"];
	point leye = box.parts["leye"];
	point nose = box.parts["nose"];
	point rear = box.parts["rear"];
	point reye = box.parts["reye"];

	// source
	ptree &xml_chip_source = xml_chip.add ("source", "");
	xml_chip_source.add ("<xmlattr>.file", src_file);
	// box element
	ptree &xml_chip_source_box = xml_chip_source.add ("box", "");
	xml_chip_source_box.add ("<xmlattr>.top", box.rect.top());
	xml_chip_source_box.add ("<xmlattr>.left", box.rect.left());
	xml_chip_source_box.add ("<xmlattr>.width", box.rect.width());
	xml_chip_source_box.add ("<xmlattr>.height", box.rect.height());
	// label
	xml_chip_source_box.add ("label", box.label);
	// all 6 parts
	ptree &sr_lear = xml_chip_source_box.add ("part", "");
	xml_add_part (sr_lear, "lear", lear);
	ptree &src_leye = xml_chip_source_box.add ("part", "");
	xml_add_part (src_leye, "leye", leye);
	ptree &src_nose = xml_chip_source_box.add ("part", "");
	xml_add_part (src_nose, "nose", nose);
	ptree &src_rear = xml_chip_source_box.add ("part", "");
	xml_add_part (src_rear, "rear", rear);
	ptree &src_reye = xml_chip_source_box.add ("part", "");
	xml_add_part (src_reye, "reye", reye);
	ptree &src_top = xml_chip_source_box.add ("part", "");
	xml_add_part (src_top, "head_top", top);
	return 0;
}

// -----------------------------------------------------------------------------
// -----------------------------------------------------------------------------
int populate_chip (ptree &xml_chip, image_dataset_metadata::box box, dlib::vector<double,2> leye,  dlib::vector<double,2> nose, dlib::vector<double,2> reye, std::string chip_dim, const std::string transform_features, std::string pathed_chip_file, std::string src_file)
{
	xml_chip.add ("label", box.label);
	xml_chip.add ("resolution", box.rect.width() * box.rect.height());
	xml_chip.add ("chip_dimensions", chip_dim);
	xml_chip.add ("transform_features", transform_features);
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
	xml_chip.add ("<xmlattr>.file", pathed_chip_file);
	xml_populate_chip_source (xml_chip, box, src_file);
	return 0;
}

// -----------------------------------------------------------------------------
// -----------------------------------------------------------------------------
int main(int argc, char** argv) try
{
    int total_faces = 0;
	std::string img_root = "/home/data/bears/imageSourceSmall/";
	std::string face_file;
	std::string chip_xml;
	std::string chip_dir;
	std::vector<float> eyes_loc {.62, .48, .38, .48};
	double user_padding = -.12;
	double default_padding = -.12;

	try
	{
		command_line_parser parser;
		parser.add_option("h","Display this help message.");
		// --root <img_root_path>
		parser.add_option("root","Strips image root path from chip location.", 1);
		parser.add_option("padding","Percent padding when generating chip", 1);
		parser.add_option("output","Name of xml file.", 1);
		parser.add_option("chipdir","Directory to write out chips", 1);
		parser.add_option("eyes","eye locations by percents: <l_x> <l_y> <r_x> <r_y>. \ne.g. .62 .45 .38 .45", 4);
		parser.parse(argc, argv);
	if (parser.option("h") || (parser.number_of_arguments() == 0))
	{
		cout << "\nGenerate chips from face xml file.";
        cout << "Usage: bearchip [options] <xml_file>\n";
        parser.print_options();

        return EXIT_SUCCESS;
    }
	if (parser.option("chipdir"))
	{
		chip_dir = parser.option ("chipdir").argument ();
		cout << "chip dir set to : " << chip_dir << endl;
	}
	if (parser.option("output"))
	{
		chip_xml = parser.option ("output").argument ();
	}
	if (parser.option("root"))
	{
		img_root = get_option (parser, "root", img_root);
	}
	if (parser.option("eyes"))
	{
		cout << "new location of eyes: "; 
    	for (unsigned long i : {0, 1, 2, 3})
		{
			eyes_loc[i] = atof (parser.option ("eyes").argument(i).c_str());
			cout << eyes_loc[i] << " ";
		}
		cout << endl;
	}
	if (parser.option("padding"))
	{
		// user_padding = parser.option ("padding").argument();
		user_padding = get_option (parser, "padding", default_padding);
		cout << "new padding = " << get_option (parser, "padding", default_padding) << endl;
	}

	face_file = parser[0];
	}
    catch (exception& e)
    {
	  // Note that this will catch any cmd_line_parse_error exceptions and print
	  // the default message.
		cout << e.what() << endl;
    }
    cout << "\nXML face file.... : " << face_file << endl;

	if (!boost::filesystem::exists(face_file))
	{
		cout << "\nError opening file " << face_file << ": No such file or directory.\n" << endl;
		return 0;
	}

    // create XML content file
	xml_add_headers (argc, argv);
	ptree &chips = g_xml_tree.add ("dataset.chips", "");

    dlib::image_dataset_metadata::dataset data;
    load_image_dataset_metadata(data, face_file);

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

        std::string orig_path(data.images[i].filename.c_str());
        boost::filesystem::path b_orig_path (orig_path);
        std::string orig_ext = b_orig_path.extension().string();
        // cout << "File: " << orig_path.string() << endl;
        // cout << "Image type " << orig_ext << endl;
		// remove root from path.

        load_image(img, data.images[i].filename.c_str());

        std::vector<matrix<rgb_pixel>> faces;
		std::string transform_features;    // features used in transformation
  		std::vector<image_dataset_metadata::box> boxes = data.images[i].boxes;
        faces = find_chips (boxes, img, user_padding, eyes_loc, transform_features, face_features);
        // cout << "Faces found: " << to_string(faces.size()) << endl;
		/*  check for more than one face.  shouldn't happen yet */
		if (faces.size() > 1)
		{
			cout << "multiple faces found: " << faces.size() << endl;
			// cin.get();
			// continue;
		}
        total_faces += faces.size();
		std::string chip_dim = std::to_string(g_chip_size) + " " + std::to_string(g_chip_size);
		// iterate through each face in image
	    boost::filesystem::path cur_dir = boost::filesystem::current_path();
        for (size_t i = 0; i < faces.size(); ++i)
        {
		  // /data/bears/imageSource/bf/fitz/bf480/IMG123.JPG  -> bf/fitz/bf480/IMG123.JPG
          std::string img_subdir_file = erase_first_copy (orig_path, img_root); 
		  if (chip_dir.empty ())
		  {
		      img_subdir_file = cur_dir.string() + "/" + img_subdir_file;
		  }
		  else
		  {
		      img_subdir_file = chip_dir + "/" + img_subdir_file;
		  }
          boost::filesystem::path p_img_subdir_file (img_subdir_file); // bf/fitz/bf_480/IMG123.JPG
		  boost::filesystem::path p_img_subdir = p_img_subdir_file.parent_path (); // bf/fitz/bf_480
		  boost::filesystem::create_directories (p_img_subdir.string());
          std::string chip_file = p_img_subdir_file.stem().string() + "_chip_" + to_string(i) + ".jpg";

		  ptree &xml_chip = chips.add ("chip", "");
		  // create chip info for chip.xml
		  int j = i*3; // # of features we care about {leye, nose, reye}
		  auto leye = face_features[j];
		  auto nose = face_features[j+1];
		  auto reye = face_features[j+2];

		  std::string rel_pathed_chip_file = p_img_subdir.string () + "/" + chip_file;

		  populate_chip (xml_chip, boxes[i], leye, nose, reye, chip_dim, transform_features, rel_pathed_chip_file, orig_path);
          cout << "... extracted chip " << to_string(i) << " to " << rel_pathed_chip_file << endl;
		  boost::filesystem::path chip_file_path (rel_pathed_chip_file);
		  if (!boost::filesystem::exists(chip_file_path.parent_path()))
			  boost::filesystem::create_directories(chip_file_path.parent_path());
          save_jpeg(faces[i], rel_pathed_chip_file, 95);
        }
    }
	std::string chips_jpg_file, chips_xml_file;
	if (chip_xml.empty ())
	{
		boost::filesystem::path xml_file (face_file);
		if (xml_file.has_parent_path ()) 
		{
			chips_jpg_file = xml_file.parent_path().string () + "/";
			chips_xml_file = xml_file.parent_path().string () + "/";
		}
		chips_jpg_file += xml_file.stem().string() + "_chip_composite.jpg";
		chips_xml_file += xml_file.stem().string() + "_chips.xml";
	}
	else
	{
		boost::filesystem::path xml_file (chip_xml);
		chips_jpg_file = xml_file.parent_path().string () + "/" + xml_file.stem().string() + "_composite.jpg";
		chips_xml_file = chip_xml;
	}
    save_jpeg(g_composite_features, chips_jpg_file, 95);
    cout << "Total faces found: " << total_faces << endl;

	xml_write_file (g_xml_tree, chips_xml_file);
	cout << "\ngenerated: \n\t" << chips_xml_file << "\n\t" << chips_jpg_file << "\n" << endl;
	// cin.get();
}
catch(std::exception& e)
{
    cout << e.what() << endl;
}
