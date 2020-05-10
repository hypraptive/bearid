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
#include <dlib/cmd_line_parser.h>
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
using namespace boost::filesystem;

// -----------------------------------------------------------------------------

// A 3x3 conv layer that doesn't do any downsampling
template <long num_filters, typename SUBNET> using con3  = con<num_filters,3,3,1,1,SUBNET>;
// A 5x5 conv layer that does 2x downsampling
template <long num_filters, typename SUBNET> using con5d = con<num_filters,5,5,2,2,SUBNET>;
template <long num_filters, typename SUBNET> using con5  = con<num_filters,5,5,1,1,SUBNET>;

template <typename SUBNET> using downsampler  = relu<affine<con5d<32, relu<affine<con5d<32, relu<affine<con5d<16,SUBNET>>>>>>>>>;
template <typename SUBNET> using downsampler_bn  = relu<bn_con<con5d<32, relu<bn_con<con5d<32, relu<bn_con<con5d<16,SUBNET>>>>>>>>>;
template <typename SUBNET> using rcon5  = relu<affine<con5<45,SUBNET>>>;
template <typename SUBNET> using rcon5_bn  = relu<bn_con<con5<45,SUBNET>>>;

using net_type = loss_mmod<con<1,9,9,1,1,rcon5<rcon5<rcon5<downsampler<input_rgb_image_pyramid<pyramid_down<6>>>>>>>>;
using net_type_bn = loss_mmod<con<1,9,9,1,1,rcon5_bn<rcon5_bn<rcon5_bn<downsampler_bn<input_rgb_image_pyramid<pyramid_down<6>>>>>>>>;

// -----------------------------------------------------------------------------
// Define the 8x downsampling block with conv5d blocks.  
// Use relu and batch normalization in the standard way.
template <typename SUBNET> using downsampler_t  = relu<bn_con<con5d<32, relu<bn_con<con5d<32, relu<bn_con<con5d<32,SUBNET>>>>>>>>>;

// The rest of the network will be 3x3 conv layers with batch normalization and
// relu.  So we define the 3x3 block we will use here.
template <typename SUBNET> using rcon3  = relu<bn_con<con3<32,SUBNET>>>;

// Finally, we define the entire network.   The special input_rgb_image_pyramid
// layer causes the network to operate over a spatial pyramid, making the detector
// scale invariant.
using net_type_t  = loss_mmod<con<1,6,6,1,1,rcon3<rcon3<rcon3<downsampler_t<input_rgb_image_pyramid<pyramid_down<6>>>>>>>>;

// -----------------------------------------------------------------------------

std::string g_mode;  // one of train_obj, train_sp, test, infer
const unsigned MAX_LONG_SIDE = 2000;
const unsigned MAX_SHORT_SIDE = 1500;
const unsigned MAX_SIZE = MAX_LONG_SIDE*MAX_SHORT_SIDE;

std::vector<std::vector<double> > get_interocular_distances (
    const std::vector<std::vector<full_object_detection> >& objects
);

matrix<rgb_pixel> downscale_large_image (
  matrix<rgb_pixel>& img,
  float& pxRatio
)
{
  bool bDownscaled = false;
  // If the image is too big (this is a memory constraint), we need to downsample it
  pxRatio = 1;
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
    // cout << "File TOO BIG" << " Ratio: " << pxRatio << endl;
    matrix<rgb_pixel> smimg((int)(img.nr() * pxRatio), (int)(img.nc() * pxRatio));
    resize_image(img, smimg);
    bDownscaled = true;
    return smimg;
  }
  return img;
}

void scale_parts (
	std::map<std::string,point> &parts,
	float pxRatio
)
{
	std::map<std::string,point>::const_iterator itr;
	for (itr = parts.begin(); itr != parts.end(); ++itr)
	{
		parts[itr->first].x() = int((float)itr->second.x() * pxRatio);
		parts[itr->first].y() = int((float)itr->second.y() * pxRatio);
	}
}

//------------------------------------------------------------------------------ 
//  scale the rect by the ratio
//------------------------------------------------------------------------------ 
void scale_rect (
	rectangle &rect,
	float pxRatio
)
{
	// cout << "before scale: " << rect.left () << endl;
	rect.set_left((int)((float)rect.left() * pxRatio));
	rect.set_top((int)((float)rect.top() * pxRatio));
	rect.set_right((int)((float)rect.right() * pxRatio));
	rect.set_bottom((int)((float)rect.bottom() * pxRatio));
	// cout << "after scale: " << rect.left () << endl;
}

//------------------------------------------------------------------------------ 
// clear labels from boxes so they won't be trained with images
//------------------------------------------------------------------------------ 
void clear_box_labels (std::vector<std::vector<mmod_rect>> &faces_list)
{
	for (unsigned long i=0; i < faces_list.size() ; ++i)
	{
		for (unsigned long j=0; j < faces_list[i].size() ; ++j)
			(faces_list[i][j]).label = "";
	}
}

//------------------------------------------------------------------------------ 
// downscale imgs and face boxes
//------------------------------------------------------------------------------ 
void downscale_imgs_and_faces (
	std::vector<matrix<rgb_pixel>> &imgs,
	std::vector<std::vector<mmod_rect>> &faces_list
	)
{
	matrix<rgb_pixel> img;
	float pxRatio = 1.0;
	std::vector<mmod_rect> faces;
	for (unsigned long i=0; i < imgs.size() ; ++i)
	{
		img = imgs[i];
		img = downscale_large_image (img, pxRatio);
		if (pxRatio != 1) { // downscaled.  apply to faces of img
			imgs[i] = img;
			faces = faces_list[i];
			for (unsigned long j=0; j < faces_list[i].size() ; ++j)
				scale_rect ((faces_list[i][j]).rect, pxRatio);
		}
	}
}


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
  cout << "Finding faces..." << endl;
  auto dets = net(img);

  // if no faces, try with upscaling
  if ((dets.size() == 0) && !bDownscaled)
  {
    cout << "Try upscaling..." << endl;
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
  // cout << "Finding landmarks..." << endl;
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
        face.parts["head_top"].x()  = shape.part(0).x() / 2;
        face.parts["head_top"].y()  = shape.part(0).y() / 2;
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
        face.parts["head_top"].x()  = (int)((float)shape.part(0).x() / pxRatio);
        face.parts["head_top"].y()  = (int)((float)shape.part(0).y() / pxRatio);
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
        face.parts["head_top"]  = shape.part(0);
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
//   copy of test_object_detection_function from dlib/dnn/validation.h
// ----------------------------------------------------------------------------------------

template <
	typename SUBNET
	>
const matrix<double,1,3> my_test_object_detection_function (
	loss_mmod<SUBNET>& detector,
    dlib::image_dataset_metadata::dataset img_data,
	const std::vector<std::vector<mmod_rect>>& old_truth_dets,
	const test_box_overlap& overlap_tester = test_box_overlap(),
	const double adjust_threshold = 0,
	const test_box_overlap& overlaps_ignore_tester = test_box_overlap()
)
{
	// make sure requires clause is not broken
	/*
	DLIB_CASSERT( is_learning_problem(images,truth_dets) == true ,
				"\t matrix my_test_object_detection_function()"
				<< "\n\t invalid inputs were given to this function"
				<< "\n\t is_learning_problem(images,truth_dets): " << is_learning_problem(images,truth_dets)
				<< "\n\t images.size(): " << images.size()
				);
				*/

	double correct_hits = 0;
	double total_true_targets = 0;

	std::vector<std::pair<double,bool> > all_dets;
	unsigned long missing_detections = 0;

	resizable_tensor temp;

	for (unsigned long i = 0; i < img_data.images.size(); ++i)
	{
		std::vector<mmod_rect> hits;
        matrix<rgb_pixel> img;
        // cout << img_data.images[i].filename.c_str() << "..." << endl;
        load_image(img, img_data.images[i].filename.c_str());

		float pxRatio;
		img = downscale_large_image (img, pxRatio);
		// extract box rects from img_data
        std::vector<mmod_rect> truth_dets;
		truth_dets.clear();
		for (unsigned long j = 0; j < img_data.images[i].boxes.size(); ++j)
		{
			if (img_data.images[i].boxes[j].ignore)
			{
				cout << "Encountered unexpected ignore!" << endl;
			}
			else
			{

				if (pxRatio != 1) { // downscaled.  apply to truth recs
					// cout << "downscaling rect by " << pxRatio << endl;
					scale_rect (img_data.images[i].boxes[j].rect, pxRatio);
				}
				truth_dets.push_back(mmod_rect(img_data.images[i].boxes[j].rect));
			}
		}

		detector.to_tensor(&img, &img+1, temp);
		detector.subnet().forward(temp);
		detector.loss_details().to_label(temp, detector.subnet(), &hits, adjust_threshold);


		for (auto& label : impl::get_labels(truth_dets, hits))
		{
			std::vector<full_object_detection> truth_boxes;
			std::vector<rectangle> ignore;
			std::vector<std::pair<double,rectangle>> boxes;
			// copy hits and truth_dets into the above three objects
			for (auto&& b : truth_dets)
			{
				if (b.ignore)
				{
					ignore.push_back(b);
				}
				else // if (b.label == label)
				{
					truth_boxes.push_back(full_object_detection(b.rect));
					++total_true_targets;
				}
			}
			for (auto&& b : hits)
			{
				// if (b.label == label)
					boxes.push_back(std::make_pair(b.detection_confidence, b.rect));
			}

			correct_hits += impl::number_of_truth_hits(truth_boxes, ignore, boxes, overlap_tester, all_dets, missing_detections, overlaps_ignore_tester);
		}
	}

	std::sort(all_dets.rbegin(), all_dets.rend());

	double precision, recall;

	double total_hits = all_dets.size();

	if (total_hits == 0)
		precision = 1;
	else
		precision = correct_hits / total_hits;

	if (total_true_targets == 0)
		recall = 1;
	else
		recall = correct_hits / total_true_targets;

	matrix<double, 1, 3> res;
	res = precision, recall, average_precision(all_dets, missing_detections);
	return res;
}

// ----------------------------------------------------------------
// initial copy from dlib/image_processing/shape_preditor.h
//   modified to take metadata instead of array of images
//	 due to memory limit.  load a single image and scale as needed.
// ----------------------------------------------------------------

    double my_test_shape_predictor (
        const shape_predictor& sp,
        dlib::image_dataset_metadata::dataset img_data,
        double & mean,
        double & stddev
    )
    {
	/*
		dlib::array<array2d<unsigned char> > images_test2;
		std::vector<std::vector<full_object_detection> > faces_test;
		load_image_dataset(images_test2, faces_test, imgs_file);
        cout << "shape predictor mean testing error:  " <<
            my_test_shape_predictor(sp, images_test2, faces_test, get_interocular_distances(faces_test)) << endl;
	*/

        running_stats<double> rs;
		for (unsigned long i = 0; i < img_data.images.size(); ++i)
		{
			matrix<rgb_pixel> img;
			// cout << i << ": " << img_data.images[i].filename.c_str() << "..." << endl;
			load_image(img, img_data.images[i].filename.c_str());

			float pxRatio = 1.0;
			// --- scale image -----
			img = downscale_large_image (img, pxRatio);
			// extract box rects from img_data
			auto objects = img_data.images[i].boxes;

            for (unsigned long j = 0; j < objects.size(); ++j)
            {
                // Just use a scale of 1 (i.e. no scale at all) if the caller didn't supply
                // any scales.
				if (pxRatio != 1.0)
				{
					scale_parts (objects[j].parts, pxRatio);
					scale_rect (objects[j].rect, pxRatio);
				}
                const double scale = length (objects[j].parts["leye"] - objects[j].parts["reye"]);

                full_object_detection det = sp(img, objects[j].rect);

				std::map<std::string,point>::const_iterator itr;
				unsigned long k = 0;
				for (itr = objects[j].parts.begin(); itr != objects[j].parts.end(); ++itr)
				{

					double score = length(det.part(k) - itr->second)/scale;
					// cout << "score for " << itr->first << ": " << score;
					// cout << " : " <<  det.part(k) << endl;
					rs.add(score);
					k++;
                }
            }
        }
        mean = rs.mean();
        stddev = rs.stddev();
        return mean;
    }

//----------------------------------------------------------------
//  train_sp 
//----------------------------------------------------------------
shape_predictor run_train_sp (std::string train_file)
{
	cout << "\n\tTraining with file: " << train_file << endl;
	// dlib::image_dataset_metadata::dataset data;
	// load_image_dataset_metadata(data, imgs_file);

	// std::vector<matrix<rgb_pixel>> images_train;
	// std::vector<std::vector<mmod_rect>> face_boxes_train;
	// load_image_dataset(images_train, face_boxes_train, train_file);
	// --- scale images and face boxes ---
	// downscale_imgs_and_faces (images_train, face_boxes_train);

//----------------------------------------------------------------------

	dlib::array<array2d<unsigned char> > images_train;
	std::vector<std::vector<full_object_detection> > faces_train;
	load_image_dataset(images_train, faces_train, train_file);
	cout << "num training images: " << images_train.size() << endl;
	shape_predictor_trainer trainer;
	trainer.set_oversampling_amount(300);
	trainer.set_nu(0.05);
	trainer.set_tree_depth(2);
	trainer.set_num_threads(2);
	// cascade depth=20, tree depth=5, padding=0.2
	trainer.set_cascade_depth (20);
	trainer.set_tree_depth (5);
	trainer.set_feature_pool_region_padding (0.2);

	trainer.be_verbose();
	cout << "\trunning shape predictor training ... \n";
	shape_predictor sp = trainer.train(images_train, faces_train);
	return sp; 
	/*
	cout << "mean training error: "<< 
		test_shape_predictor(sp, images_train, faces_train, get_interocular_distances(faces_train)) << endl;
	cout << "mean testing error:  "<< 
		test_shape_predictor(sp, images_test, faces_test, get_interocular_distances(faces_test)) << endl;
	serialize("sp.dat") << sp;
	*/
}

//----------------------------------------------------------------
// get_output_network_name ()
//	 if specified in argument, ensure parent directory exist.
//	 else append current timestamp
//----------------------------------------------------------------
std::string get_output_network_name (command_line_parser& parser)
{
	std::string out_net;
	if (parser.option ("out_network"))
	{
		out_net = parser.option ("out_network").argument();
		boost::filesystem::path p_out_network (out_net);
		if (p_out_network.has_parent_path () &&
			!boost::filesystem::exists(p_out_network.parent_path()))
			boost::filesystem::create_directories(p_out_network.parent_path());
	}
	else
	{
		time_t rawtime;
		struct tm * timeinfo;
		char buffer[80];

		time (&rawtime);
		timeinfo = localtime(&rawtime);

		strftime(buffer,sizeof(buffer),"%Y%m%d%I%M",timeinfo);
		out_net = "network_";
		out_net.append (buffer);
		out_net.append (".dat");
	}
	return out_net;
}

// ----------------------------------------------------------------------------------------

// ----------------------------------------------------------------------------------------

int main(int argc, char** argv)
{try
{
		time_t timeStart = time(NULL);
		command_line_parser parser;

		parser.add_option("h","Display this help message.");
		parser.add_option("train_obj","Train object detector.", 1);
		parser.add_option("out_network","Newly trained network.", 1);
		parser.add_option("train_sp","Train shape predictor.", 1);
		parser.add_option("test_obj","Test object detector.", 1);
		parser.add_option("test_sp","Test shape predictor.", 1);
		parser.add_option("infer","Detect faces using network file.", 1);
		parser.parse(argc, argv);

		const char* one_time_opts[] = {"h", "train_obj", "train_sp", "test_obj", "test_sp", "infer"};
		parser.check_one_time_options(one_time_opts); // Can't give an option more than once

		if (parser.option("h") || parser.number_of_arguments () != 1)
		{
			cout << "\n\t bearface is used to detect a bear face in an image using a\n";
			cout << "\tnetwork file with the --infer option.";
			cout << "\tIt can be trained using the --train_obj or --train_sp \n";
			cout << "\tand tested with the --test flags.\n\n";
			cout << "\nUsage  : bearface --<infer|test|train_sp|train_obj> <network_file> <img_xml>\n";
			cout << "\nUsage  : bearface --infer bearface_network.dat imgs.xml\n";
			cout << "\nExample: bearface --test bearface_network.dat imgs.xml\n\n";
			cout << "\nExample: bearface --train_obj bearface_network.dat -out new_network.dat imgs.xml\n\n";
			parser.print_options();

			return EXIT_SUCCESS;
		}
		std::string network;
		if (parser.option("train_obj"))
		{
			g_mode = "train_obj";
			network = parser.option ("train_obj").argument();
		}
		else if (parser.option("train_sp"))
		{
			g_mode = "train_sp";
			network = parser.option ("train_sp").argument();
		}
		else if (parser.option("test_obj"))
		{
			g_mode = "test_obj";
			network = parser.option ("test_obj").argument();
		}
		else if (parser.option("test_sp"))
		{
			g_mode = "test_sp";
			network = parser.option ("test_sp").argument();
		}
		else if (parser.option("infer"))
		{
			g_mode = "infer";
			network = parser.option ("infer").argument();
		}


	//----------------------------------------------------------------------
    //image_window win_wireframe;

	char *lvalue = NULL;
	int index;
	int c;
	std::string bearID;
  bool bLabelFixed = false;

	std::string imgs_file = parser[0];

    // load the models as well as glasses and mustache.
    net_type net;
    shape_predictor sp;
    matrix<rgb_alpha_pixel> glasses, mustache;
    deserialize(network) >> net >> sp >> glasses >> mustache;

	// doing testing
	if ((g_mode == "test_sp") || (g_mode == "test_obj")) {
		cout << "\tTesting with " << imgs_file << endl;
		std::vector<matrix<rgb_pixel>> images_test;
		std::vector<std::vector<mmod_rect>> face_boxes_test;
		dlib::image_dataset_metadata::dataset data;
		load_image_dataset_metadata(data, imgs_file);
		cout << "num testing images:  " << data.images.size() << endl;
		// ---  running test on object detection -----
		if (g_mode == "test_obj") {
			cout << "\tstarting object detector test..." << endl;
			matrix<double, 1, 3> res = my_test_object_detection_function(net, data, face_boxes_test);
			cout << "precision =  correct hits / total hits         " << endl;
			cout << "recall    =  correct hits / total true targets " << endl;
			cout << "av precision  " << endl;
			cout << "                   precision    average precision" << endl;
			cout << "                           recall " << endl;
			cout << "testing results:  " << res << endl;
		} else {
			// doing shape predictor testing
			cout << "\tstarting shape predictor test..." << endl;
			dlib::array<array2d<unsigned char> > images_test2;
			std::vector<std::vector<full_object_detection> > faces_test;
			double sp_mean, sp_stddev;

			my_test_shape_predictor(sp, data, sp_mean, sp_stddev);
			cout << "shape predictor mean testing error:  " <<
				sp_mean << " +/- " << sp_stddev << endl;

			cout << "on " << data.images.size() << " tests" << endl;
			cout << endl;
		}
		return 0;
	}
	//----------------------------------------------------------------------
	// 
	//----------------------------------------------------------------------
	if (g_mode == "train_sp") {
		std::string out_net = get_output_network_name (parser);
		shape_predictor new_sp = run_train_sp (imgs_file);

		cout << "\n\tWriting to network: " << out_net+"_bn" << endl;
		net.clean();
		net_type anet = net;
		serialize(out_net) << anet << new_sp << glasses << mustache;
		cout << "\n\tWriting to network: " << out_net << endl;

		return 0;
	}
	else if (g_mode == "train_obj") {
		std::string out_network = "";
		const std::string train_file = imgs_file;
		cout << "\n\tTraining with file: " << train_file << endl;
		dlib::image_dataset_metadata::dataset data;
		load_image_dataset_metadata(data, imgs_file);

		std::string out_net = get_output_network_name (parser);

		std::vector<matrix<rgb_pixel>> images_train;
		std::vector<std::vector<mmod_rect>> face_boxes_train;
		load_image_dataset(images_train, face_boxes_train, train_file);
		cout << "num training images: " << images_train.size() << endl;
		// --- scale images and face boxes ---
		downscale_imgs_and_faces (images_train, face_boxes_train);
		clear_box_labels (face_boxes_train);

		// mmod_options options(face_boxes_train, 40,40); // doghip
		mmod_options options(face_boxes_train, 80,80);
		// The detector will automatically decide to use multiple sliding windows if needed.
		// For the face data, only one is needed however.
		cout << "num detector windows: "<< options.detector_windows.size() << endl;
		for (auto& w : options.detector_windows)
			cout << "detector window width by height: " << w.width << " x " << w.height << endl;
		cout << "overlap NMS IOU thresh:             " << options.overlaps_nms.get_iou_thresh() << endl;
		cout << "overlap NMS percent covered thresh: " << options.overlaps_nms.get_percent_covered_thresh() << endl;

		// Now we are ready to create our network and trainer.
		net_type_bn net(options);
		// The MMOD loss requires that the number of filters in the final network layer equal
		// options.detector_windows.size().  So we set that here as well.
		net.subnet().layer_details().set_num_filters(options.detector_windows.size());
		dnn_trainer<net_type_bn> trainer(net);
		trainer.set_learning_rate(0.1);
		trainer.be_verbose();
		trainer.set_synchronization_file("mmod_sync", std::chrono::minutes(5));
		// trainer.set_iterations_without_progress_threshold(300); // doghip
		trainer.set_iterations_without_progress_threshold(8000);

		// Now let's train the network.  We are going to use mini-batches of 150
		// images.   The images are random crops from our training set (see
		// random_cropper_ex.cpp for a discussion of the random_cropper).
		std::vector<matrix<rgb_pixel>> mini_batch_samples;
		std::vector<std::vector<mmod_rect>> mini_batch_labels;
		random_cropper cropper;
		// cropper.set_chip_dims(200, 200);  // doghip
		// cropper.set_min_object_size(0.2);  // doghip
		dlib::rand rnd;
		// Run the trainer until the learning rate gets small.  This will probably take several
		// hours.
		cout << "\tRunning training ... \n" << endl;
		while(trainer.get_learning_rate() >= 1e-4)
		{
			// cropper(150, images_train, face_boxes_train, mini_batch_samples, mini_batch_labels);
			// crop size of 10
			cropper(75, images_train, face_boxes_train, mini_batch_samples, mini_batch_labels);
			// We can also randomly jitter the colors and that often helps a detector
			// generalize better to new images.
			for (auto&& img : mini_batch_samples)
				disturb_colors(img, rnd);
			trainer.train_one_step(mini_batch_samples, mini_batch_labels);
		}
		// wait for training threads to stop
		trainer.get_net();
		cout << "done training" << endl;

		// Save the network to disk
		net.clean();

		serialize(out_net+"_bn") << net << sp << glasses << mustache;
		cout << "\n\tWriting to network: " << out_net+"_bn" << endl;
		net_type anet = net;
		serialize(out_net) << anet << sp << glasses << mustache;
		cout << "\n\tWriting to network: " << out_net << endl;

		return 0;
	}


	// doing inferencing

    int total_faces = 0;
	int files_with_faces = 0;
	int files_without_faces = 0;
	cout << "\nDoing inferencing ...\n" << endl;
    // Load XML metadata file
    dlib::image_dataset_metadata::dataset data;
    load_image_dataset_metadata(data, imgs_file);

    //Handle list of images
	std::vector <string> fields;
    for (int i = 0; i < data.images.size(); ++i)
    {
        matrix<rgb_pixel> img;

        cout << "processing: " << data.images[i].filename.c_str() << "...";
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
		if (faces.size () == 0)
			files_without_faces++;
		else
			files_with_faces++;
    }
    cout << "Files with detected faces   : " << files_with_faces << endl;
    cout << "Files without detected faces: " << files_without_faces << endl;
    cout << "Total faces found           : " << total_faces << endl;
	path orig_path(imgs_file);
	std::string faces_file;
	if (orig_path.has_parent_path ())
	{
		faces_file = orig_path.parent_path().string () + "/";
	}
	faces_file += orig_path.stem().string() + "_faces.xml";
	cout << "faces_file: " << faces_file << endl;
    save_image_dataset_metadata(data, faces_file);
    if (!bLabelFixed)
    {
      cout << "\n\tGenerated " << total_faces << " faces in file: " << faces_file << "\n" << endl;
    }
    else
    {
      cout << "\n\tGenerated " << total_faces << " faces with label " << bearID << " in file: " << faces_file << "\n" << endl;
    }
}
catch(std::exception& e)
{
    cout << e.what() << endl;
}
}

// ----------------------------------------------------------------------------------------


double interocular_distance (
    const full_object_detection& det
)
{
    dlib::vector<double,2> l, r;
    // Find the center of the left eye by averaging the points around
    // the eye.
	l = det.part(2);


    // Find the center of the right eye by averaging the points around
    // the eye.
	r = det.part(5);

    // Now return the distance between the centers of the eyes
    return length(l-r);
}

std::vector<std::vector<double> > get_interocular_distances (
    const std::vector<std::vector<full_object_detection> >& objects
)
{
    std::vector<std::vector<double> > temp(objects.size());
    for (unsigned long i = 0; i < objects.size(); ++i)
    {
        for (unsigned long j = 0; j < objects[i].size(); ++j)
        {
            temp[i].push_back(interocular_distance(objects[i][j]));
        }
    }
    return temp;
}
