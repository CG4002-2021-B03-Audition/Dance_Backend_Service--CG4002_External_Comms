from pynq import allocate
from pynq import Overlay
import numpy as np
import pynq.lib.dma
import time
import pynq
import pandas as pd
import features
import joblib # ASH

class ai():
    def __init__(self):
        weight_0 = np.load('weights_3dance/weight_0.npy')
        weight_1 = np.load('weights_3dance/weight_1.npy')
        weight_2 = np.load('weights_3dance/weight_2.npy')
        weight_3 = np.load('weights_3dance/weight_3.npy')
        bias_0 = np.load('weights_3dance/bias_0.npy')
        bias_1 = np.load('weights_3dance/bias_1.npy')
        bias_2 = np.load('weights_3dance/bias_2.npy')
        bias_3 = np.load('weights_3dance/bias_3.npy')

        overlay = Overlay('3dance.bit')   # load bitstream inside FPGA
        self.dma = overlay.axi_dma_0    

        self.input_buffer0 = allocate(shape=(100,), dtype=np.float32)
        input_buffer1 = allocate(shape=(32,), dtype=np.float32)
        input_buffer2 = allocate(shape=(3,), dtype=np.float32)
        self.output_buffer0 = allocate(shape=(3,), dtype=np.float32)

        ##weights
        for i in range(32):
            for k in range(100):
                input_buffer0[k] = weight_0[k][i]
            self.dma.sendchannel.transfer(input_buffer0)
            self.dma.sendchannel.wait()
        for i in range(32):
            for k in range(32):
                input_buffer1[k] = weight_1[k][i]
            self.dma.sendchannel.transfer(input_buffer1)
            self.dma.sendchannel.wait()
        for i in range(32):
            for k in range(32):
                input_buffer1[k] = weight_2[k][i]
            self.dma.sendchannel.transfer(input_buffer1)
            self.dma.sendchannel.wait()
        for i in range(3):
            for k in range(32):
                input_buffer1[k] = weight_3[k][i]
            self.dma.sendchannel.transfer(input_buffer1)
            self.dma.sendchannel.wait()
        ##bias
        for k in range(32):
            input_buffer1[k] = bias_0[k]
        self.dma.sendchannel.transfer(input_buffer1)
        self.dma.sendchannel.wait()
        for k in range(32):
            input_buffer1[k] = bias_1[k]
        self.dma.sendchannel.transfer(input_buffer1)
        self.dma.sendchannel.wait()
        for k in range(32):
            input_buffer1[k] = bias_2[k]
        self.dma.sendchannel.transfer(input_buffer1)
        self.dma.sendchannel.wait()
        for k in range(3):
            input_buffer2[k] = bias_3[k]
        self.dma.sendchannel.transfer(input_buffer1)
        self.dma.sendchannel.wait()

        self.fns = [f for f in features.__dict__ if callable(getattr(features, f)) and f.startswith("get_")]


    def preprocess_segment(self, segment):
        def derivative_of(data):
            return pd.DataFrame(np.gradient(data, axis=1))

        row = np.empty(0)
        acc = segment.iloc[:, 0:3]
        gyro = segment.iloc[:, 3:6]
        for data in [acc,
                    gyro,
                    derivative_of(acc),
                    derivative_of(gyro),
                    # derivative_of(derivative_of(acc)),
                    # derivative_of(derivative_of(gyro))
                    ]:
            for fn in self.fns:
                f = getattr(features, fn)
                np.append(row, np.asarray(f(data)))
                row = np.concatenate((row, np.asarray(f(data))), axis=None)

        return row


    def fpga_evaluate(self, imu_data):
        print(imu_data)
        segment = self.preprocess_segment(pd.DataFrame(imu_data))
        scaler = joblib.load("scaler_object.pkl")
        segment = scaler.transform(segment)
        test = segment

        for j in range(100):
            self.input_buffer0[j] = test[j]
        self.dma.sendchannel.transfer(self.input_buffer0)
        self.dma.recvchannel.transfer(self.output_buffer0)
        self.dma.sendchannel.wait()
        self.dma.recvchannel.wait()

        return self.output_buffer0