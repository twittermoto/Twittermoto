from twittermoto import database
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


class DetectionAlgorithm(object):

    def __init__(self, m, b, dt=5):
        self.T_STA = 60     # timescale of short term average [s]
        self.T_LTA = 3600   # timescale of long term average [s]
        self.m     = m      # sensitivity constant [?]
        self.b     = b      # sensitivity constant [tweets/min]
        self.dt    = dt     # sampling period [s]

        self.X = np.zeros(self.T_STA//dt) # tweet-per-minute history of STA
        self.Y = np.zeros(self.T_LTA//dt) # tweet-per-minute history of LTA

        self.detections         = []
        self.earthquakeDetected = False

    def __call__(self, t, x):
        self.update(x)
        if self.output() >= 1 and not self.earthquakeDetected:
            self.detections.append([t, -1])
            self.earthquakeDetected = True
        elif self.output() < 1 and self.earthquakeDetected:
            self.detections[-1][1] = t
            self.earthquakeDetected = False

        return self.output()


    def update(self, x):
        '''
        Updates the tweet-per-minute history given the number of tweets for the last dt seconds.
        '''
        self.X = np.roll(self.X, 1)
        self.Y = np.roll(self.Y, 1)

        self.X[0] = x*60/self.dt
        self.Y[0] = x*60/self.dt


    def output(self):
        '''
        Returns the characteristic function of the detection algorithm.
        Values greater than 1 indicate a detection.
        '''
        return self.X.mean()/(self.m*self.Y.mean() + self.b)




def run(db):
    time, tweet_freq = db.binned_count(dt=5)


    DAs = [DetectionAlgorithm(2, 5),
           DetectionAlgorithm(4, 10),
           DetectionAlgorithm(19, 9)]
    DA_labels = ['sensative', 'moderate', 'conservative']

    C_t = x = [[] for i in range(len(DAs))]

    # loop through tweet frequency data to simulate realtime measurements
    for tf in tweet_freq:
        # update each detection algorithm with current tweet frequency
        for i, DA in enumerate(DAs):
            C_t[i].append(DA(tf))

    # Plot
    fig, axes = plt.subplots(2, 1, sharex=True)
    axes[0].set_ylabel('Tweets per 5 second period')
    axes[1].set_ylabel('Characteristic function')
    axes[0].plot(time, tweet_freq)
    for i, ct in enumerate(C_t):
        axes[1].plot(time, ct, label=DA_labels[i])
    axes[1].axhline(1, ls='--', lw=1, c='k')
    axes[1].set_ylim(0, 2)
    axes[1].legend()
    fig.autofmt_xdate()
    myFmt = mdates.DateFormatter('%d-%b %H:%M')
    axes[1].xaxis.set_major_formatter(myFmt)

    plt.show()



if __name__ == '__main__':
    pass
