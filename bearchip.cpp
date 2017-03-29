// The contents of this file are in the public domain. See LICENSE_FOR_EXAMPLE_PROGRAMS.txt
/*
    This example shows how to run a CNN based dog face detector using dlib.  The
    example loads a pretrained model and uses it to find dog faces in images.
    We also use the dlib::shape_predictor to find the location of the eyes and
    nose and then draw glasses and a mustache onto each dog found :)


    Users who are just learning about dlib's deep learning API should read the
    dnn_introduction_ex.cpp and dnn_introduction2_ex.cpp examples to learn how
    the API works.  For an introduction to the object detection method you
    should read dnn_mmod_ex.cpp



    TRAINING THE MODEL
        Finally, users interested in how the dog face detector was trained should
        read the dnn_mmod_ex.cpp example program.  It should be noted that the
        dog face detector used in this example uses a bigger training dataset and
        larger CNN architecture than what is shown in dnn_mmod_ex.cpp, but
        otherwise training is the same.  If you compare the net_type statements
        in this file and dnn_mmod_ex.cpp you will see that they are very similar
        except that the number of parameters has been increased.

        Additionally, the following training parameters were different during
        training: The following lines in dnn_mmod_ex.cpp were changed from
            mmod_options options(face_boxes_train, 40*40);
            trainer.set_iterations_without_progress_threshold(300);
        to the following when training the model used in this example:
            mmod_options options(face_boxes_train, 80*80);
            trainer.set_iterations_without_progress_threshold(8000);

        Also, the random_cropper was left at its default settings,  So we didn't
        call these functions:
            cropper.set_chip_dims(200, 200);
            cropper.set_min_object_height(0.2);

        The training data used to create the model is also available at
        http://dlib.net/files/data/CU_dogs_fully_labeled.tar.gz

        Lastly, the shape_predictor was trained with default settings except we
        used the following non-default settings: cascade depth=20, tree
        depth=5, padding=0.2
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

int main(int argc, char** argv) try
{
    if (argc < 3)
    {
        cout << "Call this program like this:" << endl;
        cout << "./dnn_mmod_dog_hipsterizer mmod_dog_hipsterizer.dat faces/dogs.jpg" << endl;
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

    //image_window win1(glasses);
    //image_window win2(mustache);
    //image_window win_wireframe;
    image_window win_chip;
    //image_window win_hipster;

    // Now process each image, find bear, and extract a face chip
    for (int i = 2; i < argc; ++i)
    {
        std::string upscaled = "";
        matrix<rgb_pixel> img;
        load_image(img, argv[i]);

        if (img.size() > (MAX_SIZE))
        {
          cout << argv[i] << ": TOO BIG" << endl;
          continue;
        }

        // Upsampling the image will allow us to find smaller dog faces but will use more
        // computational resources.
        //pyramid_up(img);

        auto dets = net(img);
        //win_wireframe.clear_overlay();
        //win_wireframe.set_image(img);
        // We will also draw a wireframe on each dog's face so you can see where the
        // shape_predictor is identifying face landmarks.
        std::vector<image_window::overlay_line> lines;
        //cout << "dets size: " << dets.size() << endl;

        // if no faces, try with upscaling
        if (dets.size() == 0)
        {
          if (img.size() > (MAX_SIZE/4))
          {
            cout << argv[i] << ": TOO BIG to UPSCALE" << endl;
            continue;
          }

          pyramid_up(img);
          upscaled = " UPSCALED";
          dets = net(img);

          if (dets.size() == 0)
          {
            cout << argv[i] << ": has no faces" << endl;
            continue;
          }
        }

        // if more than one face, we exit
        //if (dets.size() > 1)
        //{
        //  cout << argv[i] << upscaled << ": has too many faces = " << dets.size() << endl;
        //  continue;
        //}

        unsigned chipcount = 0;
        for (auto&& d : dets)
        {
            std::vector<image_window::overlay_line> chip_lines;
            // print the rectangle
            //cout << "Rectangle:" << d.rect << endl;

            // get the landmarks for this dog's face
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
            lines.push_back(image_window::overlay_line(leye, nose, color));
            lines.push_back(image_window::overlay_line(nose, reye, color));
            lines.push_back(image_window::overlay_line(reye, leye, color));
            lines.push_back(image_window::overlay_line(reye, rear, color));
            lines.push_back(image_window::overlay_line(rear, top, color));
            lines.push_back(image_window::overlay_line(top, lear,  color));
            lines.push_back(image_window::overlay_line(lear, leye,  color));

            // chip_details based on get_face_chip_details
            //const double mean_face_shape_x[] = { 0, 0, 0.65, 0.50, 0, 0.35 };
            //const double mean_face_shape_y[] = { 0, 0, 0.50, 0.65, 0, 0.50 };
            const double mean_face_shape_x[] = { 0, 0, 0.62, 0.50, 0, 0.38 };
            const double mean_face_shape_y[] = { 0, 0, 0.48, 0.70, 0, 0.48 };
            //const double mean_face_shape_x[] = { 0, 0, 0.62, 0.54, 0, 0.38 }; // derrived from HOG image
            //const double mean_face_shape_y[] = { 0, 0, 0.45, 0.62, 0, 0.45 }; // derrived from HOG image
            const unsigned long size = 150;
            const double padding = 0.0;
            chip_details face_chip_details;

            std::vector<dlib::vector<double,2> > from_points, to_points;
            //for (unsigned long i = 0; i < 6; ++i)
            for (unsigned long i : {3, 5, 2})  // follow the order from face pose (nose, reye, leye)
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
            chip_lines.push_back(image_window::overlay_line(from_points[0], from_points[1],  color));
            chip_lines.push_back(image_window::overlay_line(from_points[1], from_points[2],  color));
            chip_lines.push_back(image_window::overlay_line(from_points[2], from_points[0],  color));

            const rgb_pixel color_r(255,0,0);
            point_transform_affine pta = get_mapping_to_chip(face_chip_details);
            auto leye_new = pta(shape.part(2));
            auto nose_new = pta(shape.part(3));
            auto reye_new = pta(shape.part(5));
            chip_lines.push_back(image_window::overlay_line(leye_new, nose_new,  color_r));
            chip_lines.push_back(image_window::overlay_line(nose_new, reye_new,  color_r));
            chip_lines.push_back(image_window::overlay_line(reye_new, leye_new,  color_r));


            // extract the face chip
            matrix<rgb_pixel> face_chip;
            extract_image_chip(img, face_chip_details, face_chip);
            win_chip.clear_overlay();

            // save the face chip_dims
            boost::filesystem::path orig_path(argv[i]);
            //std::string orig_ext = orig_path.extension().string();
            std::string chip_file = orig_path.stem().string() + "_chip_" + to_string(chipcount) + ".jpg";

            cout << argv[i] << upscaled << ": extracted chip " << to_string(chipcount) << " to " << chip_file << endl;
            save_jpeg(face_chip, chip_file, 95);

            win_chip.set_image(face_chip);
            win_chip.add_overlay(chip_lines);
            chipcount++;
        }


        //win_wireframe.add_overlay(lines);
        //win_hipster.set_image(img);

        //cout << "Hit enter to process the next image." << endl;
        //cin.get();
    }
}
catch(std::exception& e)
{
    cout << e.what() << endl;
}
