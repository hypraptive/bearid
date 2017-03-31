# bearid
Hypraptive BearID project code repository

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
