#include <stdio.h>
#include <tensorflow/c/c_api.h>

int main() {
  printf("Hello from TensorFlow C library version %s\n", TF_Version());

  const int num_bytes = 24 * sizeof(float);
  int64_t dims[] = {2, 3, 4};
  TF_Tensor* t = TF_AllocateTensor(TF_FLOAT, dims, 3, num_bytes);
  
  printf("TF_TensorType(t) %d\n", TF_TensorType(t));
  printf("TF_NumDims(t) %d\n", TF_NumDims(t));
  printf("TF_TensorByteSize(t) %lu\n", TF_TensorByteSize(t));

  TF_DeleteTensor(t);

  return 0;
}
