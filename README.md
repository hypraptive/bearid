# bearid
[BearID Project](http://bearresearch.org/) code repository. For more information, read the [hypraptive blog](https://hypraptive.github.io/).

## Pre-Requisites
* [dlib](http://dlib.net/) (tested with version 19.7) - download and install somewhere. You should have OpenCV and CUDA and other packages which are helpful for dlib.
* [boost](http://www.boost.org/) (tested with version 1.58.0)

## Build
Uses cmake flow:

```
git clone https://github.com/hypraptive/bearid.git
cd bearid
mkdir build
cd build
cmake -DDLIB_PATH=<path_to_dlib> ..
cmake --build . --config Release
```

## Run
How to run end-to-end inferencing using ```bearid.py``` or each of it's components individually.

### Running bearid
Use the ```bearid.py``` python 3 script to predict the bear identities from a set of images.

The ```bearid.py``` script expects all of the binaries and networks to be in the same directory as the script. If, for example, you cloned and built bearid as ~/bearid and cloned the models as ~/bearid-models, you can:

```
mkdir ~/tools
cp ~/bearid/bearid.py ~/tools
cp ~/bearid/build/bear* ~/tools
cp ~/bearid-models/*.dat ~/tools
```

Then you can run:

```
~/tools/bearid.py <image_file/directories>
```

Intermediate results and log files will be written to the current working directory. Progress messages and final results are printed to standard out.

### Running each component
Use the imglab and the C++ bearid components:
* Imglab (from dlib) - create an XML file containing all source images
  * ```imglab -c <source_img_file> <image files/directories>```
* Bearface - find bear faces and face landmarks
  * ```./bearface <bearface_network_file> <source_img_file>```
* Bearchip - align and crop bear faces and produce bear chips
  * ```./bearchip [-root <img_root_dir>] <face_metadata_file>```
* Bearembed - generate a 128D embedding from bear chips
  * ```./bearembed --embed <bearembed_network_file> --anet <chip_metadata_file>```
* Bearsvm - classify set of embeddings using SVM one-vs-one classifier
  * ```./bearsvm --infer <bearsvm_network_file> <embed_metadata_file>```

## Tools
There are python tools and scripts in the `tools` directory for managing datasets and evaluating results.

## Models

For pre-trained network files, see:  [bearid-models](https://github.com/hypraptive/bearid-models).
