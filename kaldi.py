import json
import logging
import numpy as np
from asyncio import create_task, Lock, open_connection, wait_for, sleep

from av.audio.resampler import AudioResampler

log = logging.getLogger('web')

logging.getLogger('asyncio').setLevel(logging.WARNING)

class KaldiSink:
    """
    This class is a proxy between the client browser (aka peer connection) and the Kaldi server.

    It creates 2 tasks that transfer data between the two:
    1. __run_audio_xfer transfers audio from the browser (mic) to the Kaldi server
    2. __run_text_xfer transfers text from the Kaldi server to the browser
    """

    def __init__(self, user_connection, kaldi_server):
        self.__resampler = AudioResampler(format='s16', layout='mono', rate=kaldi_server.samplerate)

        self.__pc = user_connection
        self.__audio_task = None
        self.__text_task = None

        self.__ks = kaldi_server
        self.__kaldi_reader = None
        self.__kaldi_writer = None

        self.__channel = None

    async def set_audio_track(self, track):
        self.__track = track

    async def set_text_channel(self, channel):
        self.__channel = channel

    async def start(self):
        try:
            self.__kaldi_reader, self.__kaldi_writer = await open_connection(host=self.__ks.host, port=self.__ks.port)
        except:
            log.exception("Error opening conenction to Kaldi server")
            self.__pc.close()
            await self.__ks.free()
            return
        log.info(f'Connected to Kaldi server {self.__ks.host}:{self.__ks.port}...')
        self.__audio_task = create_task(self.__run_audio_xfer())
        self.__text_task = create_task(self.__run_text_xfer())

    async def stop(self):
        if self.__audio_task is not None:
            self.__audio_task.cancel()
            self.__audio_task = None
        if self.__text_task is not None:
            self.__text_task.cancel()
            self.__text_task = None
        if self.__kaldi_writer:
            self.__kaldi_writer.close()
            self.__kaldi_writer = None
            await self.__ks.free()

    async def __run_audio_xfer(self):
        while True:
            try:
                frame = await self.__track.recv()
                frame = self.__resampler.resample(frame)
                data = frame.to_ndarray()
                data2 = data.tobytes()
                self.__kaldi_writer.write(data2)
                await self.__kaldi_writer.drain() #without this we won't catch any write exceptions
            except:
                self.__kaldi_writer.close()
                await self.__ks.free()
                return

    command = list()
    with open('/server/command.txt', 'r') as file:
        for line in file:
            command.append(line.strip().split())

    id2text = dict()
    with open('/server/HW4_transcript.txt', 'r') as file:
        for line in file:
            temp = line.strip().split()
            id2text[temp[0]] = temp[1:]
    id2text['0000'] = ['โกวาจี']
            
    label = list()
    test = list()
    with open('/server/answer.txt', 'r') as file:
        for line in file:
            temp = line.strip().split()
            text = id2text[temp[0].split('_')[1]]
            test.append(temp[1:])
            label.append(text)
            
    words = set()
    for cmd in command:
        for w in cmd:
            words.add(w)

    def dist(x, y):
        if x == y: return 0
        elif x[0] == y[0]: return abs(len(x) - len(y)) / (len(x) + len(y)) * 0.25 + 0.5
        else: return abs(len(x) - len(y)) / (len(x) + len(y)) * 0.5 + 0.5

    def DTW(s1, s2):
        
        arr = np.zeros((len(s1) + 1, len(s2) + 1))
        arr[:, :] = np.inf
        for i in range(1, len(s1) + 1):
            for j in range(1, len(s2) + 1):
                row = i - 1
                col = j - 1
                if i == 1 and j == 1:
                    arr[i, j] = dist(s1[row], s2[col])
                    continue
                    
                arr[i, j] = min(arr[i, j-1] + dist(s1[row],s2[col]),\
                                arr[i-1, j-1] + 2*dist(s1[row],s2[col]),\
                                arr[i-1, j] + dist(s1[row],s2[col]))
        
        return arr[-1, -1]

    def find_best_match(test , all_command):
        mn = np.inf
        best_match = ''
        for cmd in all_command:
            distance = DTW(cmd, test)
            if mn > distance:
                mn = distance
                best_match = cmd
        return best_match, distance
    async def __run_text_xfer(self):
        await sleep(1) # this is useful to
        self.__channel.send('<s>\r') # this is only sent to inform the web UI we are ready to send data
        # since the above token doesn't end with \n it will be erased once Kaldi recognizes something
        while True:
            a = await self.__kaldi_reader.read(256)

            print('kaldi', str(a, encoding='utf-8'))
            t = str(a, encoding='utf-8').split(' ')
            b, d = find_best_match(t, command)
            print('kaldi res', (' ').join(b))
            self.__channel.send((' ').join(b))


class KaldiServer:
    """
    This class describes the Kaldi server resource. It is a representation of a running instance of the Kaldi server
    together with its parameters.
    """

    def __init__(self, srv_config):
        for key in ['name', 'host', 'port', 'samplerate']:
            if key in srv_config:
                setattr(self, key, srv_config[key])

    async def free(self):
        """
        Relases the resource back to the queue.
        :return:
        """

        await kaldi_server_queue.put(self)


class KaldiServerQueue:
    """
    This class represents the servers available for usage by the clients.

    When a server is used it is removed from the queue. After it is released it gets back in the queue.
    """

    def __init__(self):
        self.__servers = set()
        self.__lock = Lock()

    def load(self, config):
        with open(config) as f:
            servers = json.load(f)

        for server in servers:
            self.__servers.add(KaldiServer(server))

    async def get(self):
        async with self.__lock:
            if self.__servers:
                try:
                    return self.__servers.pop()
                except KeyError:
                    return None

    async def put(self, server):
        async with self.__lock:
            self.__servers.add(server)


kaldi_server_queue = KaldiServerQueue()
