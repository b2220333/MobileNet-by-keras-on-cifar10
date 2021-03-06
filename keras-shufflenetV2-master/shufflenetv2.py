import numpy as np
from keras.utils import plot_model
from keras_applications.imagenet_utils import _obtain_input_shape
from keras.engine.topology import get_source_inputs
from keras.layers import Input, Conv2D, MaxPool2D, GlobalMaxPooling2D, GlobalAveragePooling2D
from keras.layers import Activation, Dense
from keras.models import Model
import keras.backend as K
from keras.datasets import cifar10
from utils import block
import cv2
import keras
num_classes=6


x_train = np.empty((2517,384,512,3),dtype="float32")
#x_test = np.empty((473,384,512,3),dtype="float32")
x_test=list()
y_train=list()
y_test=list()
def load():
  tra_i=0
  tes_i=0
  datas = os.listdir('./')
  total = len(datas)
  #print(datas)
  for e in datas:
    img = cv2.imread(e)
    if e[:5] == 'cardb':
      img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
      x_train[tra_i] = img
      y_train.append([1])
      tra_i+=1
    if e[:5] == 'glass':
      img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
      x_train[tra_i] = img
      y_train.append([2])
      tra_i+=1
    if e[:5] == 'metal':
      img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
      x_train[tra_i] = img
      y_train.append([3])
      tra_i+=1
    if e[:5] == 'paper':
      img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
      x_train[tra_i] = img
      y_train.append([4])
      tra_i+=1
    if e[:5] == 'plast':
      img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
      x_train[tra_i] = img
      y_train.append([5])
      tra_i+=1
    if e[:5] == 'trash':
      img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
      x_train[tra_i] = img
      y_train.append([0])
      tra_i+=1
  return (x_train,np.array(y_train)) , (x_test,np.array(y_test))



def ShuffleNetV2(include_top=True,
                 input_tensor=None,
                 scale_factor=1.0,
                 pooling='max',
                 input_shape=(384,512,3),
                 load_model=None,
                 num_shuffle_units=[3,7,3],
                 bottleneck_ratio=1,
                 classes=6):
    if K.backend() != 'tensorflow':
        raise RuntimeError('Only tensorflow supported for now')
    name = 'ShuffleNetV2_{}_{}_{}'.format(scale_factor, bottleneck_ratio, "".join([str(x) for x in num_shuffle_units]))
    input_shape = _obtain_input_shape(input_shape, default_size=224, min_size=28, require_flatten=include_top,
                                      data_format=K.image_data_format())
    out_dim_stage_two = {0.5:48, 1:116, 1.5:176, 2:244}

    if pooling not in ['max', 'avg']:
        raise ValueError('Invalid value for pooling')
    if not (float(scale_factor)*4).is_integer():
        raise ValueError('Invalid value for scale_factor, should be x over 4')
    exp = np.insert(np.arange(len(num_shuffle_units), dtype=np.float32), 0, 0)  # [0., 0., 1., 2.]
    out_channels_in_stage = 2**exp
    out_channels_in_stage *= out_dim_stage_two[bottleneck_ratio]  #  calculate output channels for each stage
    out_channels_in_stage[0] = 24  # first stage has always 24 output channels
    out_channels_in_stage *= scale_factor
    out_channels_in_stage = out_channels_in_stage.astype(int)

    if input_tensor is None:
        img_input = Input(shape=input_shape)
    else:
        if not K.is_keras_tensor(input_tensor):
            img_input = Input(tensor=input_tensor, shape=input_shape)
        else:
            img_input = input_tensor

    # create shufflenet architecture
    x = Conv2D(filters=out_channels_in_stage[0], kernel_size=(3, 3), padding='same', use_bias=False, strides=(2, 2),
               activation='relu', name='conv1')(img_input)
    x = MaxPool2D(pool_size=(3, 3), strides=(2, 2), padding='same', name='maxpool1')(x)

    # create stages containing shufflenet units beginning at stage 2
    for stage in range(len(num_shuffle_units)):
        repeat = num_shuffle_units[stage]
        x = block(x, out_channels_in_stage,
                   repeat=repeat,
                   bottleneck_ratio=bottleneck_ratio,
                   stage=stage + 2)

    if bottleneck_ratio < 2:
        k = 1024
    else:
        k = 2048
    x = Conv2D(k, kernel_size=1, padding='same', strides=1, name='1x1conv5_out', activation='relu')(x)

    if pooling == 'avg':
        x = GlobalAveragePooling2D(name='global_avg_pool')(x)
    elif pooling == 'max':
        x = GlobalMaxPooling2D(name='global_max_pool')(x)

    if include_top:
        x = Dense(classes, name='fc')(x)
        x = Activation('softmax', name='softmax')(x)

    if input_tensor:
        inputs = get_source_inputs(input_tensor)

    else:
        inputs = img_input

    model = Model(inputs, x, name=name)

    if load_model:
        model.load_weights('', by_name=True)

    return model

if __name__ == '__main__':
    import os
    (x_train, y_train), (x_test, y_test) = load()
    y_train = keras.utils.to_categorical(y_train, num_classes)
    x_train /= 255
    model = ShuffleNetV2(include_top=True, input_shape=(384, 512, 3), bottleneck_ratio=1)
    model.compile(loss='categorical_crossentropy',optimizer='adam',metrics=['accuracy'])
    model.summary()
    model.fit(x_train, y_train,
              batch_size=32,
              epochs=15,
              shuffle=True,
              verbose=1)
