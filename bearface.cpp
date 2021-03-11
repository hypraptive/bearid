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
// #include <dlib/gui_widgets.h>
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
unsigned MAX_LONG_SIDE = 2000;
unsigned MAX_SHORT_SIDE = 1500;
unsigned MAX_SIZE = MAX_LONG_SIDE*MAX_SHORT_SIDE;

std::vector<std::vector<double> > get_interocular_distances (
    const std::vector<std::vector<full_object_detection> >& objects
);

matrix<rgb_pixel> downscale_large_image_old (
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

//------------------------------------------------------------------------------
//  scale image down to MAX_SIZE, fill in pxRatio
//------------------------------------------------------------------------------
matrix<rgb_pixel> downscale_image (
  matrix<rgb_pixel>& img,
  float& pxRatio
)
{
  pxRatio = 1;
  if (img.size() > (MAX_SIZE))
  {
	long orig_img_size = img.size ();
	pxRatio = sqrt ( (float) MAX_SIZE / (float) img.size());
    // cout << "File TOO BIG" << " Ratio: " << pxRatio << endl;
    matrix<rgb_pixel> smimg((int)(img.nr() * pxRatio), (int)(img.nc() * pxRatio));
    resize_image(img, smimg);
	long new_img_size = smimg.size ();
	float new_ratio = sqrt (orig_img_size / new_img_size);
	cout << "old size: " << orig_img_size << endl;
	cout << "new size: " << new_img_size << endl;
    return smimg;
  }
  return img;
}

//------------------------------------------------------------------------------
//  scale parts by ratio
//------------------------------------------------------------------------------
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
//  set rect
//------------------------------------------------------------------------------
void set_face_rect (
	rectangle &rect,
	rectangle detect_rect
)
{
	rect.set_left (detect_rect.left());
	rect.set_top (detect_rect.top());
	rect.set_right (detect_rect.right());
	rect.set_bottom (detect_rect.bottom());
}

//------------------------------------------------------------------------------
//  scale the rect by the ratio
//------------------------------------------------------------------------------
void scale_face_rect (
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
//  set face
//------------------------------------------------------------------------------
void set_face_parts (
	image_dataset_metadata::box &face,
    full_object_detection shape
)
{
	std::vector<std::string> landmarks = {"head_top", "lear", "leye", "nose", "rear", "reye"};
	for (int i = 0; i < landmarks.size (); ++i)
	{
		face.parts[landmarks[i]].x() = shape.part(i).x();
		face.parts[landmarks[i]].y() = shape.part(i).y();
	}
}

//------------------------------------------------------------------------------
//  scale face parts by ratio
//------------------------------------------------------------------------------
void scale_face_parts (
	image_dataset_metadata::box &face,
	float pxRatio
)
{
	std::vector<std::string> landmarks = {"head_top", "lear", "leye", "nose", "rear", "reye"};
	for (int i = 0; i < landmarks.size(); ++i)
	{
		face.parts[landmarks[i]].x() *= pxRatio;
		face.parts[landmarks[i]].y() = face.parts[landmarks[i]].y() * pxRatio;
	}
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
		img = downscale_image (img, pxRatio);
		if (pxRatio != 1.0) { // downscaled.  apply to faces of img
			imgs[i] = img;
			faces = faces_list[i];
			for (unsigned long j=0; j < faces_list[i].size() ; ++j)
				scale_face_rect ((faces_list[i][j]).rect, pxRatio);
		}
	}
}

//------------------------------------------------------------------------------
// upscale image if it will remain under MAX_SIZE
//------------------------------------------------------------------------------
bool upscale_image (
  matrix<rgb_pixel>& img,
  float& pxRatio
)
{
  int upscaleRatio = 2;
	long origImgSize = img.size ();
    if (img.size() < (MAX_SIZE/(upscaleRatio*upscaleRatio)))
	{
	  cout << "upscaling..." << endl;
	  pyramid_up(img);
	  pxRatio = sqrt (img.size () / origImgSize);
	  cout << "Upscaled image size: " << img.size() << endl;
	  return true;
	}
	return false;
}

//------------------------------------------------------------------------------
// Find Faces
//------------------------------------------------------------------------------
std::vector<dlib::mmod_rect> find_faces (
  net_type& net,
  matrix<rgb_pixel>& img,
  float &sideRatio
)
{
  img = downscale_image (img, sideRatio);

  // Find faces
  cout << "Finding faces..." << endl;
  std::vector<dlib::mmod_rect> dets;
  // auto dets = net(img);
  dets = net(img);

  // if no faces, try with upscaling
  if (dets.size() == 0)
  {
	if (upscale_image (img, sideRatio))
	  dets = net(img);
  }
  return dets;
}
//------------------------------------------------------------------------------
// Find Faces and face landmarks
//------------------------------------------------------------------------------
void find_faces_and_landmarks (
  net_type& net,
  shape_predictor& sp,
  matrix<rgb_pixel>& img,
  std::vector<image_dataset_metadata::box>& faces,
  std::string bearID
)
{
  float pxRatio = 1.0;
  int numShapeParts = 6;
  // auto dets = net(img);

  auto dets = find_faces (net, img, pxRatio);

  // --- For each face, find the face landmarks ----
  // cout << "Finding landmarks..." << endl;
  for (auto&& d : dets)
  {
      // get the landmarks for this face
      auto shape = sp(img, d.rect);

      // fill in the data for faces
      image_dataset_metadata::box face;
	  float scaleRatio = 1/pxRatio;
	  // face: dlib::image_dataset_metadata::box

	  set_face_rect (face.rect, d);
	  scale_face_rect (face.rect, scaleRatio);
	  set_face_parts (face, shape);
	  scale_face_parts (face, scaleRatio);
	  face.label = bearID;
      faces.push_back(face);
  }
}

//------------------------------------------------------------------------------
// load a batch of images and their corresponding boxes
//------------------------------------------------------------------------------
void get_image_batch (
  size_t num_images,
  dlib::image_dataset_metadata::dataset data,
  std::vector<std::string>& files,
  std::vector<matrix<rgb_pixel>>& images_batch,
  std::vector<std::vector<mmod_rect>>& face_boxes_batch
)
{
  random_cropper cropper;
  std::mutex rnd_mutex;
  images_batch.clear();
  face_boxes_batch.clear();
  files.clear();
  cout << "num imagea per batch: " << num_images << endl;
  for (size_t i = 0; i < num_images; ++i)
  {
    matrix<rgb_pixel> img;
    size_t idx;
    idx = std::rand() % data.images.size();
    //{ std::lock_guard<std::mutex> lock(rnd_mutex);
    //    idx = rnd.get_random_64bit_number()%data.images.size();
    //}

    //cout << idx << " : " << data.images[idx].filename.c_str() << "..." << endl;
    load_image(img, data.images[idx].filename.c_str());
    std::vector<mmod_rect> boxes;
    for (unsigned long j = 0; j < data.images[idx].boxes.size(); ++j)
    {
      boxes.push_back(mmod_rect(data.images[idx].boxes[j].rect));
    }
    matrix<rgb_pixel> crop;
    std::vector<mmod_rect> crop_rects;
    cropper(img, boxes, crop, crop_rects);
    face_boxes_batch.push_back(crop_rects);
    images_batch.push_back(crop);
    files.push_back(data.images[idx].filename.c_str());
  }
}

// ----------------------------------------------------------------------------------------
//   copy of test_object_detection_function from dlib/dnn/validation.h
//		changes:
//		- load only one image at time due to memory limitation
//	  	- downscale image if beyond MAX_SIZE
//    	- if detect no faces, upscale if doesn't violate MAX_SIZE
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
	double correct = 0;
	double correct_hits = 0;
	double total_true_targets = 0;

	std::vector<std::pair<double,bool> > all_dets;
	unsigned long missing_detections = 0;
	unsigned long prev_missed = 0;
	resizable_tensor temp;

	for (unsigned long i = 0; i < img_data.images.size(); ++i)
	{
		std::vector<mmod_rect> hits;
        matrix<rgb_pixel> img;
        // cout << img_data.images[i].filename.c_str() << "..." << endl;
        load_image(img, img_data.images[i].filename.c_str());

		float pxRatio = 1.0;
		//--------------------------------------------------
		//--------------------------------------------------
		img = downscale_image (img, pxRatio);
		detector.to_tensor(&img, &img+1, temp);
		detector.subnet().forward(temp);
		detector.loss_details().to_label(temp, detector.subnet(), &hits, adjust_threshold);
		if (hits.size () == 0)  // no faces found, try upscale image
		{
			if (upscale_image (img, pxRatio))
			{
				detector.to_tensor(&img, &img+1, temp);
				detector.subnet().forward(temp);
				detector.loss_details().to_label(temp, detector.subnet(), &hits, adjust_threshold);
			}
		}
		//--------------------------------------------------
		//--------------------------------------------------
        std::vector<mmod_rect> truth_dets;
		truth_dets.clear();
		// populate truth detects
		for (unsigned long j = 0; j < img_data.images[i].boxes.size(); ++j)
		{
			if (img_data.images[i].boxes[j].ignore)
			{
				cout << "Encountered unexpected ignore!" << endl;
			}
			else
			{
				if (pxRatio != 1) { // downscaled.  apply to truth recs
					scale_face_rect (img_data.images[i].boxes[j].rect, pxRatio);
				}
				truth_dets.push_back(mmod_rect(img_data.images[i].boxes[j].rect));
			}
		}
		// iterate through labels though we don't use labels
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

			prev_missed = missing_detections;
			correct = impl::number_of_truth_hits(truth_boxes, ignore, boxes, overlap_tester, all_dets, missing_detections, overlaps_ignore_tester);
			correct_hits += correct;
			if (boxes.size () > truth_boxes.size ()) // # detects more than # truths
			{
				if (correct < truth_boxes.size()) // # detects == # truths but some didn't match
				{
					cout << img_data.images[i].filename.c_str() << " has extra detections and " << truth_boxes.size () - correct << " erroneous detection" << endl;
				}
				else
				{
					cout << img_data.images[i].filename.c_str() << " has extra detections" << endl;
				}
			}
			else if (boxes.size () < truth_boxes.size ()) // # detects less than # truths
			{
				if (correct < boxes.size ())
					cout << img_data.images[i].filename.c_str() << " has missing detections and " << boxes.size () - correct << " erroneous detection" << endl;
				else
					cout << img_data.images[i].filename.c_str() << " has missing detections" << endl;
			}
			else if (correct < boxes.size()) // # detects == # truths but some didn't match
			{
        		cout << img_data.images[i].filename.c_str() << " has " << boxes.size () - correct << " erroneous detections" << endl;
			}
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
			img = downscale_image (img, pxRatio);
			// extract box rects from img_data
			auto objects = img_data.images[i].boxes;

            for (unsigned long j = 0; j < objects.size(); ++j)
            {
                // Just use a scale of 1 (i.e. no scale at all) if the caller didn't supply
                // any scales.
				if (pxRatio != 1.0)
				{
					scale_parts (objects[j].parts, pxRatio);
					scale_face_rect (objects[j].rect, pxRatio);
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
//  train_obj
//----------------------------------------------------------------
net_type_bn run_train_obj (std::string train_file, int batch_size)
{
  cout << "\n\tTraining with file: " << train_file << endl;
  dlib::image_dataset_metadata::dataset data;
  load_image_dataset_metadata(data, train_file);

  std::vector<matrix<rgb_pixel>> images_train;
  std::vector<std::vector<mmod_rect>> face_boxes_train;
  //load_image_dataset(images_train, face_boxes_train, train_file);
  cout << "num training images: " << data.images.size() << endl;
  // --- scale images and face boxes ---
  //downscale_imgs_and_faces (images_train, face_boxes_train);
  for (unsigned long i = 0; i < data.images.size(); ++i)
  {
    std::vector<mmod_rect> boxes;
    for (unsigned long j = 0; j < data.images[i].boxes.size(); ++j)
    {
      boxes.push_back(mmod_rect(data.images[i].boxes[j].rect));
    }
    face_boxes_train.push_back(boxes);
  }

  clear_box_labels (face_boxes_train);

  // mmod_options options(face_boxes_train, 40,40); // doghip
  mmod_options options(face_boxes_train, 80,80); // bearface_network
  // mmod_options options(face_boxes_train, 40,40); // AnimalWeb
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
  std::vector<std::string> mini_batch_files;
  //random_cropper cropper;
  // cropper.set_chip_dims(200, 200);  // doghip
  // cropper.set_min_object_size(0.2);  // doghip

  // Run the trainer until the learning rate gets small.  This will probably take several
  // hours.

  // Set up data loaders
  dlib::pipe<std::vector<std::string>> qfiles(4);
  dlib::pipe<std::vector<matrix<rgb_pixel>>> qimages(4);
  dlib::pipe<std::vector<std::vector<mmod_rect>>> qlabels(4);
  auto data_loader = [&batch_size, &data, &qfiles, &qimages, &qlabels](time_t seed)
  {
    dlib::rand rnd(time(0)+seed);
    std::vector<matrix<rgb_pixel>> images;
    std::vector<std::vector<mmod_rect>> labels;
    std::vector<std::string> files;
    dlib::rand rnd_color(time(0)+seed);
    while(qimages.is_enabled())
    {
      try
      {
        get_image_batch(batch_size, data, files, images, labels);
        //get_image_batch(90, data, images, labels);
        //load_mini_batch(numid, numface, rnd, objs, images, labels);
        // We can also randomly jitter the colors and that often helps a detector
        // generalize better to new images.
        for (auto&& img : images)
          disturb_colors(img, rnd_color);

        //cout << "Queue batch" << endl;
        //for (size_t i = 0; i < files.size(); ++i)
        //{
        //  cout << i << " queue : " << files[i] << "..." << endl;
        //}

        qfiles.enqueue(files);
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

  cout << "\tRunning training ... \n" << endl;
  while(trainer.get_learning_rate() >= 1e-4)
  {
    // load a batch of images and their corresponding boxes from the queue
    qimages.dequeue(mini_batch_samples);
    qlabels.dequeue(mini_batch_labels);
    qfiles.dequeue(mini_batch_files);
    //cout << "Dequeue batch" << endl;
    //for (size_t i = 0; i < mini_batch_files.size(); ++i)
    //{
      //cout << "dequeue : " << mini_batch_files[i] << "..." << endl;
    //}
    //get_image_batch(75, data, mini_batch_samples, mini_batch_labels);
    // cropper(150, images_train, face_boxes_train, mini_batch_samples, mini_batch_labels);
    // crop size of 10
    //cropper(75, images_batch, face_boxes_batch, mini_batch_samples, mini_batch_labels);
    trainer.train_one_step(mini_batch_samples, mini_batch_labels);
  }
  // wait for training threads to stop
  trainer.get_net();
  cout << "done training" << endl;
  qimages.disable();
  qlabels.disable();
  qfiles.disable();
  data_loader1.join();
  data_loader2.join();
  data_loader3.join();
  data_loader4.join();
  data_loader5.join();

	return net;
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
		parser.add_option("size_max", "scale images to max size.", 1);
		parser.add_option("xy_max", "scale images to max x and y.", 2);
		parser.add_option("out_network","Newly trained network.", 1);
		parser.add_option("train_sp","Train shape predictor.", 1);
		parser.add_option("test_obj","Test object detector.", 1);
		parser.add_option("test_sp","Test shape predictor.", 1);
		parser.add_option("infer","Detect faces using network file.", 1);
		parser.add_option("batch_size","Images to load into GPU for each train step. Defaults to 90.", 1);
		parser.add_option("load_all","Load all images into memory. Not yet implemented.");
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
		if (parser.option ("size_max"))
		{
			MAX_SIZE = stoi (parser.option ("size_max").argument());
		}
		if (parser.option ("xy_max"))
		{
			MAX_LONG_SIDE = stoi (parser.option ("xy_max").argument(0));
			MAX_SHORT_SIDE = stoi (parser.option ("xy_max").argument(1));
			MAX_SIZE = MAX_LONG_SIDE*MAX_SHORT_SIDE;
		}
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
	int batch_size = 90;
	std::string bearID;
	bool bLabelFixed = false;

	std::string imgs_file = parser[0];
	if (parser.option("batch_size"))
		batch_size = stoi (parser.option ("batch_size").argument());

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
		//std::string out_network = "";
    std::string out_net = get_output_network_name (parser);
    net_type_bn net = run_train_obj (imgs_file, batch_size);

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
        find_faces_and_landmarks (net, sp, img, faces, bearID);
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
