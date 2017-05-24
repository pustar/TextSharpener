
import tensorflow as tf
import numpy as np


class ImageSharpener:
    def __init__(self):
        self.W1 = tf.Variable(tf.random_normal([16,16,3,3],stddev=1/256.0))
        self.W2 = tf.Variable(tf.random_normal([16,16,3,3],stddev=1/256.0))
        self.W3 = tf.Variable(tf.random_normal([16,16,3,3],stddev=1/256.0))
        self.W4 = tf.Variable(tf.random_normal([16,16,3,3],stddev=1/256.0))

        self.b1 = tf.Variable(tf.random_normal([1]))
        self.b2 = tf.Variable(tf.random_normal([1]))
        self.b3 = tf.Variable(tf.random_normal([1]))
        self.b4 = tf.Variable(tf.random_normal([1]))


    def init_net(self, input_tensor):
        layer_1 = self.conv_layer(input_tensor, self.W1, self.b1, tf.nn.relu)
        
        layer_2 = self.conv_layer(layer_1, self.W2, self.b2, tf.nn.relu)
        
        layer_3 = self.conv_layer(layer_2, self.W3, self.b3, tf.nn.relu)
        
        layer_4 = self.conv_layer(layer_3, self.W4, self.b4, tf.identity)
    
        return layer_4

    def conv_layer(self,x,W,b,activation):
        res = tf.add(tf.nn.conv2d(tf.reshape(x, [1,100,100,3]),W,[1,1,1,1],padding="SAME"),b)
        return activation(res)

    def make_file_pipeline(self, train_files, label_files):
        training_data_queue = tf.train.string_input_producer(
                train_files
        , shuffle=True, seed=1)
        
        training_label_queue = tf.train.string_input_producer(
                label_files
        , shuffle=True, seed=1)
        
        data_reader = tf.WholeFileReader()
        data_key, data_value = data_reader.read(training_data_queue)
        image = tf.image.decode_png(data_value, channels=3)
        
        label_reader = tf.WholeFileReader()
        label_key, label_value = label_reader.read(training_label_queue)
        label = tf.image.decode_png(data_value, channels=3)
        
        image_norm = tf.reshape(tf.to_float(image) / 256.0, [1,100,100,3])
        label_norm = tf.reshape(tf.to_float(label) / 265.0, [1,100,100,3])
        
        return tf.train.slice_input_producer([image_norm, label_norm])

    def train_on_images(self, train_files, label_files, val_train_files, val_label_files):
        train_data, train_label = self.make_file_pipeline(train_files, label_files)
        val_data, val_label = self.make_file_pipeline(val_train_files, val_label_files)

        train_net_out = self.init_net(train_data)
        val_net_out = self.init_net(val_data)

        #cost = tf.reduce_mean((train_data + train_net_out - train_label)**10)
        #val_cost = tf.reduce_mean((val_data + val_net_out - val_label)**10)

        cost = tf.reduce_mean(2**((train_data + train_net_out - train_label)**2))
        val_cost = tf.reduce_mean(2**((val_data + val_net_out - val_label)**2))
        
        train = tf.train.GradientDescentOptimizer(0.03).minimize(cost)
        
        with tf.Session() as sess:
            coord = tf.train.Coordinator()
            threads = tf.train.start_queue_runners(coord=coord)
        
            sess.run(tf.global_variables_initializer())
            
            for _ in range(500):
                if _ % 10 == 0:
                    print("Cost at iteration {} is {}".format(_,sess.run([cost])[0]))
                sess.run([train])
        
            cost_sum = 0
            for _ in range(len(val_train_files)):
                cost_sum += sess.run([val_cost])[0]
            print("Validation cost {}".format(cost_sum / len(val_train_files)))

            coord.request_stop()
            coord.join(threads)

    def sharpen(self, train_files):
        train_data, train_label = self.make_file_pipeline(train_files, train_files)
        train_net_out = self.init_net(train_data)

        image_out = tf.image.encode_png(tf.reshape(tf.cast(train_net_out*256.0,tf.uint8),[100,100,3]))

        with tf.Session() as sess:
            coord = tf.train.Coordinator()
            threads = tf.train.start_queue_runners(coord=coord)
        
            sess.run(tf.global_variables_initializer())
            
            for f_str in train_files:
                out_file = open(f_str[:-4]+"_sharpened.png","w")
                out_file.write(sess.run([image_out])[0])
                out_file.close()

            coord.request_stop()
            coord.join(threads)



ims = ImageSharpener()

ims.train_on_images(
        ["../data/set_1_train"+str(i)+".png" for i in range(100)],
        ["../data/set_1_label"+str(i)+".png" for i in range(100)],
        ["../data/validation_1_train"+str(i)+".png" for i in range(10)],
        ["../data/validation_1_train"+str(i)+".png" for i in range(10)]
        )

ims.sharpen(
        ["../data/validation_1_train"+str(i)+".png" for i in range(10)],
        )

