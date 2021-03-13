from pynq import allocate
from pynq import Overlay
import numpy as np
import pynq.lib.dma
import time
import pynq
import pandas as pd
import features

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

        overlay = Overlay('dance3.bit')   # load bitstream inside FPGA
        self.dma = overlay.axi_dma_0    

        self.input_buffer0 = allocate(shape=(100,), dtype=np.float32)
        input_buffer1 = allocate(shape=(32,), dtype=np.float32)
        input_buffer2 = allocate(shape=(3,), dtype=np.float32)
        self.output_buffer0 = allocate(shape=(3,), dtype=np.float32)

        ##weights
        for i in range(32):
            for k in range(100):
                self.input_buffer0[k] = weight_0[k][i]
            self.dma.sendchannel.transfer(self.input_buffer0)
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
        
        scaler_mean = [-9.79599139e+03, -7.85817580e+03, -2.06396179e+03,  4.39034055e+03,
        4.13546555e+03,  5.12006625e+03,  4.43163483e+03,  3.64003694e+03,
        2.09117943e+03, -2.44344242e+03, -1.21686964e+03,  1.46744898e+03,
        7.02187494e+03,  5.29885584e+03,  2.97970307e+03, -1.79777142e-01,
       -3.15613952e-01,  8.77378569e-02, -3.37793280e-01,  9.13876005e-02,
       -2.10357415e-01,  4.27493911e+05,  4.23001515e-01,  2.30117195e-02,
       -7.57461966e-02, -7.50229682e+01, -1.13643993e+02, -1.62351590e+02,
        6.53984099e+01,  1.14621687e+02,  1.64045495e+02,  4.21426301e+01,
        6.25108089e+01,  1.06656975e+02, -3.41482627e+00, -4.33497497e+00,
        3.24014282e+00,  6.31487412e+01,  8.74146422e+01,  1.77145981e+02,
       -3.06855061e-02,  1.05354111e-01, -9.47604365e-03, -2.23981007e-01,
        5.85347542e-03, -3.35334291e-01,  6.25266696e+03,  1.17591037e-02,
        6.33330636e-02, -1.46770511e-01, -5.47314156e+03, -1.83796025e+03,
       -3.71488715e+03,  7.96023410e+03,  6.00601656e+03,  1.07321837e+04,
        3.84188800e+03,  2.39030212e+03,  4.30289795e+03,  1.22657278e+03,
        1.95544570e+03,  2.68431862e+03,  5.43309773e+03,  3.69618858e+03,
        6.21613025e+03,  2.91636081e-02,  1.46393416e-01,  2.87109870e-01,
       -2.05706989e-01, -3.01033654e-01, -4.27174939e-02,  4.34163939e+05,
        4.71974018e-01, -2.94832017e-01,  5.41903192e-01, -1.35257067e+02,
       -8.66942359e+01, -2.19385822e+02,  1.40969523e+02,  9.26191475e+01,
        2.16189046e+02,  7.81929102e+01,  5.69649527e+01,  1.33056581e+02,
       -9.20148704e-01,  3.32748454e+00,  7.57511779e+00,  1.13931979e+02,
        9.15854406e+01,  2.11561120e+02,  1.07176740e-01,  1.31108518e-02,
       -6.11308436e-02,  2.64919513e-02, -3.43702336e-01, -3.69493695e-01,
        7.88305267e+03, -2.73798307e-03, -5.41356581e-01,  7.04638648e-01]
        scaler_scale = [5.62917689e+03, 6.92785301e+03, 3.59816629e+03, 6.05103410e+03,
        5.89583922e+03, 3.39389584e+03, 2.80835040e+03, 2.26414784e+03,
        1.39559388e+03, 4.07238128e+03, 5.33076222e+03, 2.32635934e+03,
        5.43547323e+03, 4.23169231e+03, 2.35793064e+03, 8.13880308e-01,
        9.24499010e-01, 8.01123677e-01, 1.73755802e+00, 1.99782069e+00,
        1.51942199e+00, 9.73462099e+04, 4.96770251e-01, 6.32930284e-01,
        6.01693016e-01, 6.58188226e+01, 7.42067713e+01, 1.33954244e+02,
        5.99971644e+01, 8.73172308e+01, 1.23915718e+02, 2.99813902e+01,
        3.74257957e+01, 7.36866151e+01, 3.48649278e+01, 3.45420683e+01,
        7.79403739e+01, 5.31112692e+01, 6.38353667e+01, 1.47477662e+02,
        8.30111233e-01, 7.94410540e-01, 8.82889162e-01, 1.72374335e+00,
        1.70826483e+00, 2.23469581e+00, 3.40345410e+03, 5.57255259e-01,
        6.42258600e-01, 5.66106611e-01, 5.79060689e+03, 3.73707028e+03,
        6.05589156e+03, 5.63339632e+03, 3.31379480e+03, 8.28381802e+03,
        2.43428723e+03, 1.64370394e+03, 2.95026784e+03, 3.84842880e+03,
        2.20608866e+03, 5.18149146e+03, 3.99288884e+03, 3.06278675e+03,
        5.11718516e+03, 7.78662655e-01, 8.07449908e-01, 8.55648880e-01,
        1.54020309e+00, 1.68691606e+00, 1.88136369e+00, 1.30248121e+05,
        4.81776102e-01, 5.38245066e-01, 4.31849817e-01, 1.03309687e+02,
        7.51044001e+01, 1.85845921e+02, 1.11156395e+02, 6.97695094e+01,
        1.49765215e+02, 5.24924023e+01, 3.98922353e+01, 9.20332833e+01,
        4.95473001e+01, 4.14028792e+01, 9.25099564e+01, 9.47740898e+01,
        7.67346351e+01, 1.77450836e+02, 8.34369831e-01, 8.53469150e-01,
        7.63679642e-01, 1.83869198e+00, 1.95639488e+00, 1.59928619e+00,
        4.53949157e+03, 6.15557672e-01, 4.74216535e-01, 3.96184625e-01]

        segment = (segment * scaler_mean) / scaler_scale
        test = segment

        for j in range(100):
            self.input_buffer0[j] = test[j]
        self.dma.sendchannel.transfer(self.input_buffer0)
        self.dma.recvchannel.transfer(self.output_buffer0)
        self.dma.sendchannel.wait()
        self.dma.recvchannel.wait()

        return self.output_buffer0
