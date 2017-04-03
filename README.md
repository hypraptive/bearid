# bearid
Hypraptive BearID project code repository

## Programs
* Bearchip - finds bear faces, aligns and crops
  * ./bearchip ../../../dlib-data/mmod_dog_hipsterizer.dat <IMG or DIR>
* Bearembed - uses a set of bear faces to train a 128D embedding
  * ./bearembed -train <face_chip_dir>
  * ./bearembed -test <face_chip_dir>
  * ./bearembed -embed <embedded_dir> <face_chip_dir>
* Bearsvm - uses a set of embeddings to train and SVM one-vs-one classifier
  * ./bearsvm <embedded_dir>
* Bearid - puts it all together
  * ./bearid <image_file>

## Data Sources
* [Carla Farris on Flickr](https://www.flickr.com/photos/129908461@N03/albums/with/72157672138992512)
  * [Brooks Falls 2015](https://www.flickr.com/photos/129908461@N03/albums/72157657150224152)
  * [Brooks Falls 2016](https://www.flickr.com/photos/129908461@N03/albums/72157672138992512)
* [Ike Fitz on Flickr](https://www.flickr.com/photos/ikefitz/albums)
  * [Brooks River Wildlife 2015](https://www.flickr.com/photos/ikefitz/albums/72157666514167600)
  * [Brooks River Wildlife 2016](https://www.flickr.com/photos/ikefitz/albums/72157665026099739)
