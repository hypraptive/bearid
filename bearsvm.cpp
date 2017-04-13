// The contents of this file are licensed under the MIT license.
// See LICENSE.txt for more information.

/*
  This program will train a linear SVM to classify bears from bear face
  embeddings.
*/

#include <iostream>
#include <ctime>
#include <vector>
#include <dlib/svm_threaded.h>
#include <dlib/svm.h>
#include <dlib/image_io.h>
#include <boost/algorithm/string.hpp>

using namespace std;
using namespace dlib;

// This function spiders the top level directory and obtains a list of all the
// files.
std::vector<std::vector<string>> load_objects_list (
  const string& dir
)
{
  std::vector<std::vector<string>> objects;
  for (auto subdir : directory(dir).get_dirs())
  {
    std::vector<string> imgs;
    for (auto img : subdir.get_files())
    imgs.push_back(img);

    if (imgs.size() != 0)
    objects.push_back(imgs);
  }
  return objects;
}

// Set folds higer for cross validation
// However, any bears with less than folds number of embeddings will be skipped
int folds = 1;

int main(int argc, char** argv)
{
  if (argc == 1)
  {
      cout << "Give this program a path to the embeddings.\n" << endl;
      cout << "For example: " << endl;
      cout << "   ./bearsvm <embedded_dir>" << endl;
      return 1;
  }

  // Samples are embeddings, which ar 128D vector of floats
  typedef matrix<float,128,1> sample_type;
  std::vector<sample_type> samples;
  std::vector<double> labels;
  std::vector <string> fields;
  std::vector <string> ids;

  // Onve vs One trainer
  typedef one_vs_one_trainer<any_trainer<sample_type> > ovo_trainer;
  ovo_trainer trainer;

  // Linear SVM
  typedef linear_kernel<sample_type> kernel_type;
  svm_c_linear_trainer<kernel_type> linear_trainer;
  linear_trainer.set_c(100);

  // Use the SVM classifier for the OVO trainer
  trainer.set_trainer(linear_trainer);

  // get samples and labels
  auto objs = load_objects_list(argv[1]);

  for (size_t i = 0; i < objs.size(); ++i)
  {
    cout << "ID: " << i << " Files: " << objs[i].size() << endl;

    // If using cross validation, each id need at least as many embeddings as folds
    if (objs[i].size() < folds)
    {
      cout << "Skipping..." << endl;
      continue;
    }
    for (size_t j = 0; j < objs[i].size(); ++j)
    {
      if (j==0)
      {
        boost::split( fields, objs[i][j], boost::is_any_of( "/" ));
        //cout << fields.size() << " token[s-2] " << fields[fields.size() - 2] << endl;
        cout << i << " : " << fields[fields.size() - 2] << endl;
        ids.push_back(fields[fields.size() - 2]);
      }
      sample_type embedded;
      deserialize(objs[i][j]) >> embedded;
      samples.push_back(embedded);
      labels.push_back(i);
    }
  }

  // Now let's do 5-fold cross-validation using the one_vs_one_trainer we just setup.
  // As an aside, always shuffle the order of the samples before doing cross validation.
  randomize_samples(samples, labels);
  cout << "cross validation: \n" << cross_validate_multiclass_trainer(trainer, samples, labels, folds) << endl;

  // Create a decision function
  one_vs_one_decision_function<ovo_trainer> df = trainer.train(samples, labels);

  // Test one_vs_one_decision_function
  cout << "predicted label: "<< df(samples[0])  << ", true label: "<< labels[0] << endl;

  // Save SVM to disk
  one_vs_one_decision_function<ovo_trainer,
  decision_function<kernel_type>    // This is the output of the linear_trainer
  > df2, df3;
  df2 = df;
  serialize("bear_svm.dat") << df2;
  serialize("bear_svm_ids.dat") << ids;

  // Check serialization
  std::vector <string> ids2;
  deserialize("bear_svm_ids.dat") >> ids2;
  deserialize("bear_svm.dat") >> df3;
  cout << "predicted label: "<< df3(samples[0])  << ", true label: "<< labels[0] << " == " << ids2[labels[0]] << endl;

}
