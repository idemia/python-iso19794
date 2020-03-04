
"""

ISO 19794-5 Images (Face)
-------------------------

Reading
'''''''

The :py:meth:`open()` method sets the following ``info`` properties

``version``
    Version (``010``, ``020`` or ``030``)

``nb_facial_images``
    The number of representations, i.e. the number of frames

In addition, each frame has the following additional attributes:

``header``
    The representation header (specific to each frame), containing:

    - For version ``010``:

      - ``landmark_points``
      - ``gender``
      - ``eye_colour``
      - ``hair_colour``
      - ``property_mask``
      - ``expression``
      - ``pose_yaw``
      - ``pose_pitch``
      - ``pose_roll``
      - ``pose_uncertainty_yaw``
      - ``pose_uncertainty_pitch``
      - ``pose_uncertainty_roll``
      - ``face_image_type``
      - ``image_data_type``
      - ``source_type``
      - ``device_type``
      - ``quality``

      When reading an image the fields ``gender``, ``eye_colour``, ``hair_colour``,
      ``property_mask``, ``expression``, ``face_image_type``, ``image_data_type`` and ``source_type``
      are converted to readable text.

Writing
'''''''

The ``save()`` method can take the following keyword arguments:

``save_all``
    If true, Pillow will save all frames of the image to a multirepresentation file.

``append_images``
    A list of images to append as additional frames. Each of the images in the list
    can be a single or multiframe image.

``version``
    The version of the format to use, one of ``010`` or ``030``. If not provided and if the image
    was loaded from an ISO 19794 image, the same version will be used.

Usage
'''''

First, let's create a sample image:

>>> from PIL import Image, ImageDraw
>>> sample = Image.new("RGB",(200,300),255)
>>> draw = ImageDraw.Draw(sample)
>>> for i in range(20,100,10):
...     for n in range(5):
...         draw.ellipse( (i+n,i+n,200-i-n,300-i-n),outline=0)

To build a single frame image, we first need a representation header. This can be built from
a list of key/value.

>>> import datetime
>>> header = dict(
...     landmark_points=[],
...     gender='M',
...     eye_colour='BLUE',
...     hair_colour='BLACK',
...     property_mask=['GLASSES'],
...     expression='NEUTRAL',
...     pose_yaw=0,
...     pose_pitch=0,
...     pose_roll=0,
...     pose_uncertainty_yaw=0,
...     pose_uncertainty_pitch=0,
...     pose_uncertainty_roll=0,
...     face_image_type='FULL_FRONTAL',
...     image_data_type='JPEG',
...     source_type='STATIC_CAMERA',
...     device_type=b'\\x00\\x00',
...     quality=b'\\x00\\x00',
...    )

An image with no representation header will not be generated

>>> import io
>>> buffer = io.BytesIO()
>>> sample.save(buffer,"FAC", version='010')
Traceback (most recent call last):
    ...
AttributeError: 'Image' object has no attribute 'header'

Header must be defined on the image for the save operation to work correctly, but
a minimal header is also possible (default values will be provided)

>>> sample.header = dict()
>>> buffer = io.BytesIO()
>>> sample.save(buffer,"FAC", version='010')

Using a fully defined header:

>>> sample.header = header
>>> buffer = io.BytesIO()
>>> sample.save(buffer,"FAC", version='010')
>>> print(len(buffer.getvalue()))   # should be 200*300 + 41 + 16
55373
>>> print(buffer.getvalue()[0:3])
b'FAC'
>>> print(buffer.getvalue()[4:7])
b'010'
>>> print(buffer.getvalue()[14])
0

Multi-frames image is generated with the ``save_all`` option:

>>> buffer_multi = io.BytesIO()
>>> sample.save(buffer_multi,"FAC",save_all=True,append_images=[sample], version='010')
>>> print(len(buffer_multi.getvalue()))   # should be 2*(200*300 + 41) + 16
110732

>>> nsample = Image.open(buffer)
>>> nsample.mode
'RGB'
>>> nsample.size
(200, 300)

For a single frame image, ``seek`` will fail if we want to access the second frame:

>>> nsample.seek(1)
Traceback (most recent call last):
    ...
EOFError: attempt to seek outside sequence

But it will not fail for a true multi-frame image:

>>> nsample = Image.open(buffer_multi)
>>> nsample.info['nb_facial_images']
2
>>> nsample.seek(1)
>>> nsample.mode
'RGB'
>>> nsample.size
(200, 300)

Image can be saved in ``JPEG`` format:

>>> buffer = io.BytesIO()
>>> sample.header['image_data_type'] ='JPEG'
>>> sample.save(buffer,"FAC", version="010")
>>> print(len(buffer.getvalue()) < 60061)   # should be less than 200*300 + 42 + 3 + 16
True

The same for a multiframe image:

>>> nsample = Image.open(buffer_multi)
>>> buffer = io.BytesIO()
>>> nsample.header['image_data_type'] = 'JPEG'
>>> nsample.save(buffer,"FAC",version='010',save_all=True)
>>> print(len(buffer.getvalue())>61000 and  len(buffer.getvalue())<120098)
True

Both frames can be compressed:

>>> buffer = io.BytesIO()
>>> nsample.seek(1)
>>> nsample.header['image_data_type'] = 'JPEG'
>>> nsample.save(buffer,"FAC",version='010',save_all=True)
>>> print(len(buffer.getvalue())>61000 and  len(buffer.getvalue())<90000)
True

And then read again:

>>> nsample2 = PIL.Image.open(buffer)
>>> data = nsample2.load()  # force decoding of the image
>>> nsample2.seek(1)
>>> data = nsample2.load()

Jpeg2000 is also supported (see https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#jpeg-2000
for the prerequisites)

>>> buffer = io.BytesIO()
>>> sample.header['image_data_type'] = 'JPEG2000'
>>> sample.save(buffer,"FAC",version='010')
>>> print(len(buffer.getvalue()) < 27000)
True
>>> sample2 = PIL.Image.open(buffer)
>>> data = sample2.load()
>>> sample2.tobytes()==sample.tobytes()
True

>>> buffer = io.BytesIO()
>>> sample.header['image_data_type'] = 'JPEG2000'
>>> sample.save(buffer,"FAC",version='010')
>>> print(len(buffer.getvalue()) > 20000)
True
>>> sample2 = PIL.Image.open(buffer)
>>> data = sample2.load()
>>> sample2.tobytes()==sample.tobytes()
True

Using an invalid compression algo will raise an exception:

>>> buffer = io.BytesIO()
>>> sample.header['image_data_type'] = 'UNKNOWN'
>>> sample.save(buffer,"FAC",version='010')
Traceback (most recent call last):
    ...
SyntaxError: Unknown compression algo UNKNOWN

"""

import io
import datetime
import struct
import types
import functools
from collections import namedtuple

from PIL import Image, ImageFile

#------------------------------------------------------------------------------
#
#
#------------------------------------------------------------------------------

FACRepresentationHeaderInfo = {
    'capture_datetime': [],
    'capture_device_technology_id': [],
    'capture_device_vendor_id': [],
    'capture_device_type_id': [],
    'quality_records': [],
    'landmark_points': ['010'],
    'gender': ['010'],
    'eye_colour': ['010'],
    'hair_colour': ['010'],
    'subject_height': [],
    'property_mask': ['010'],
    'expression': ['010'],
    'pose_yaw': ['010'],
    'pose_pitch': ['010'],
    'pose_roll': ['010'],
    'pose_uncertainty_yaw': ['010'],
    'pose_uncertainty_pitch': ['010'],
    'pose_uncertainty_roll': ['010'],
    'face_image_type': ['010'],
    'image_data_type': ['010'],
    'source_type': ['010'],
    'device_type': ['010'],
    'quality': ['010'],
}

FACLandmarkPoint = namedtuple('FACLandmarkPoint',[
    'point_type',
    'point_code',
    'x',
    'y',
    'z'
    ])

FACQualityRecord = namedtuple('FACQualityRecord',[
    'score',
    'algo_vendor_id',
    'algo_id'])

#
GENDER = {
    'X': 0,
    'M': 1,
    'F': 2,
    'U': 255,
}

#
EYE_COLOUR = {
    'UNSPECIFIED': 0,
    'BLACK': 1,
    'BLUE': 2,
    'BROWN': 3,
    'GRAY': 4,
    'GREEN': 5,
    'MULTI_COLOURED': 6,
    'PINK': 7,
    'UNKNOWN': 255,
}

#
HAIR_COLOUR = {
    'UNSPECIFIED': 0,
    'BALD': 1,
    'BLACK': 2,
    'BLONDE': 3,
    'BROWN': 4,
    'GRAY': 5,
    'WHITE': 6,
    'RED': 7,
    'UNKNOWN': 255,
}

#
PROPERTY_FLAGS = {
    'SPECIFIED':            0B000000000000000000000001,
    'GLASSES':              0B000000000000000000000010,
    'MOUSTACHE':            0B000000000000000000000100,
    'BEARD':                0B000000000000000000001000,
    'TEETH_VISIBLE':        0B000000000000000000010000,
    'BLINK':                0B000000000000000000100000,
    'MOUTH_OPEN':           0B000000000000000001000000,
    'LEFT_EYE_PATCH':       0B000000000000000010000000,
    'RIGHT_EYE_PATCH':      0B000000000000000100000000,
    'DARK_GLASSES':         0B000000000000001000000000,
    'MEDICAL_CONDITION':    0B000000000000010000000000,
}

#
EXPRESSION = {
    'UNSPECIFIED':      b"\x00\x00",
    'NEUTRAL':          b"\x00\x01",
    'SMILE_CLOSED_JAW': b"\x00\x02",
    'SMILE_OPEN_MOUTH': b"\x00\x03",
    'RAISED_EYEBROWS':  b"\x00\x04",
    'EYES_LOOKING_AWAY': b"\x00\x05",
    'SQUINTING':        b"\x00\x06",
    'FROWNING':         b"\x00\x07",
}

#
FACE_IMAGE_TYPE = {
    'BASIC': 0,
    'FULL_FRONTAL': 1,
    'TOKEN_FRONTAL': 2,
}

#
IMAGE_DATA_TYPE = {
    'JPEG': 0,
    'JPEG2000': 1,
}

#
SOURCE_TYPE = {
    'UNSPECIFIED': 0,
    'STATIC_UNKNOWN': 1,
    'STATIC_CAMERA': 2,
    'STATIC_SCANNER': 3,
    'FRAME_UNKNWON': 4,
    'FRAME_ANALOGUE_CAMERA': 5,
    'FRAME_DIGITAL_CAMERA': 6,
    'UNKNOWN': 7,
}

COLOUR_SPACE = {
    0: (24, 'RGB'),
    1: (24, 'RGB'),
    2: (24, 'YCbCr'),
    3: (8, 'L'),
    4: (24, 'RGB'),
}

#------------------------------------------------------------------------------
#
# Type 4 Images (fingerprint and palmprint)
#
#------------------------------------------------------------------------------

def _accept(prefix):
    return prefix[:4] == b"FAC\x00"

class FACImageFile(ImageFile.ImageFile):

    format = "FAC"
    format_description = "ISO19794-5 image (face image)"
    _close_exclusive_fp_after_loading = False

    def _open(self):
        # General header (§8.2)
        header = self.fp.read(17)
        if header[:4] != b"FAC\x00":
            raise SyntaxError("not a ISO19794-5 file")

        version = None
        if header[4:8] == b"010\x00":
            version = '010'
        elif header[4:8] == b"020\x00":
            version = '020'
        elif header[4:8] == b"030\x00":
            version = '030'
        if version is None:
            raise SyntaxError("Invalid version for a ISO19794-5 file")

        self.info['version'] = version
        if version=='010':
            length,self.info['nb_facial_images'] = struct.unpack(">IH",header[8:14])
            self.__first = self.__next = 14     # skip the general header
        elif version=='030':
            length,self.info['nb_facial_images'],self.info['certification_flag'],self.info['temporal_semantics'] = struct.unpack(">IH?H",header[8:14])
            self.__first = self.__next = 17     # skip the general header

        # setup frame pointers
        self.__frame = -1
        self.__fp = self.fp
        self._frame_pos = []
        self.n_frames = self.info['nb_facial_images']

        self._rheaders = []

        self._seek(0)

    def load_end(self):
        # allow closing if we're on the first frame, there's no next
        if self.__frame == 0 and not self.__next:
            self._close_exclusive_fp_after_loading = True

    def seek(self, frame):
        "Select a given frame as current image"
        if not self._seek_check(frame):
            return
        self._seek(frame)
        # Create a new core image object on second and
        # subsequent frames in the image. Image may be
        # different size/mode.
        Image._decompression_bomb_check(self.size)
        self.im = Image.core.new(self.mode, self.size)

    def __del__(self):
        if self.__fp and self._exclusive_fp:
            self.__fp.close()
            self.__fp = None
        elif self.fp and self._exclusive_fp:
            self.fp.close()
            self.fp = None

    def _seek_check(self, frame):
        if (frame < self._min_frame or
            frame >= self.n_frames+self._min_frame):
            raise EOFError("attempt to seek outside sequence")

        return self.tell() != frame

    def _seek(self, frame):
        # save rheader in case it has been modified
        if self.__frame>=0 and hasattr(self,"header"):
            self._rheaders[self.__frame] = self.header
        self.fp = self.__fp
        while len(self._frame_pos) <= frame:
            if not self.__next:
                raise EOFError("no more images in FAC file")
            # reset python3 buffered io handle in case fp
            # was passed to a libxxx, invalidating the buffer
            self.fp.tell()
            self.fp.seek(self.__next)
            self._frame_pos.append(self.__next)
            header,offset,ns = self.read_header()
            self._rheaders.append(header)
            self.__next = self._frame_pos[frame] + ns.length
            self.__frame += 1
        self.fp.seek(self._frame_pos[frame])
        header,offset,ns = self.read_header()
        self.header = self._rheaders[frame]
        self.__next = self._frame_pos[frame] + ns.length
        self.__frame = frame

        self.mode = ns.mode
        try:
            self.size = (ns.width,ns.height)
        except AttributeError:
            # Support Pillow >= 5.3.0
            self._size = (ns.width,ns.height)

        # data descriptor
        # Select decoder
        if header['image_data_type']=='JPEG':
            self.tile = [
                ('jpeg', (0, 0) + self.size, self._frame_pos[frame]+offset, (self.mode,self.mode,1,0))
            ]
        elif header['image_data_type']=='JPEG2000':
            sig = self.fp.read(4)
            codec = None
            if sig == b"\xff\x4f\xff\x51":
                codec = "j2k"
            else:
                sig = sig + self.fp.read(8)

                if sig == b"\x00\x00\x00\x0cjP  \x0d\x0a\x87\x0a":
                    codec = "jp2"
            if codec is None:
                raise SyntaxError("not a JPEG 2000 image")

            self.tile = [
                ('jpeg2k', (0, 0) + self.size, self._frame_pos[frame]+offset, (codec,))
            ]
        else:
            raise SyntaxError("Unknown image_data_type "+repr(header['image_data_type']))

    def tell(self):
        "Return the current frame number"
        return self.__frame

    def read_header(self):
        # Reader representation header starting at current position
        # return a namedtuple
        nb = 0
        # Temporary namespace used during the analysis of the header
        ns = types.SimpleNamespace()
        if self.info['version']=="010":
            ns.length, = struct.unpack(">I",self.fp.read(4))
            # Init other
            ns.capture_datetime = datetime.datetime.now()
            ns.capture_device_technology_id = "\x00"
            ns.capture_device_vendor_id = "\x00\x00"
            ns.capture_device_type_id = "\x00\x00"
            ns.quality_records = []
            nb += 4
        elif self.info['version']=="030":
            ns.length,ns.capture_datetime,ns.capture_device_technology_id,ns.capture_device_vendor_id,ns.capture_device_type_id,q_length = \
                struct.unpack(">I9ss2s2sB",self.fp.read(19))
            # XXX micro or milli seconds?
            ns.capture_datetime = datetime.datetime( *struct.unpack(">HBBBBBH",ns.capture_datetime) )
            nb += 19
            Q = []
            for i in range(q_length):
                Q.append( FACQualityRecord._make( struct.unpack(">B2s2s",self.fp.read(5)) ) )
                nb += 5
            ns.quality_records = Q

        # §5.5 Facial Information Block
        if self.info['version']=="010":
            ns.number_landmark_points, ns.gender, ns.eye_colour, ns.hair_colour, property_mask, \
            ns.expression, ns.pose_yaw, ns.pose_pitch, ns.pose_roll, \
            ns.pose_uncertainty_yaw, ns.pose_uncertainty_pitch, ns.pose_uncertainty_roll = \
                struct.unpack(">HBBB3s2sbbbbbb",self.fp.read(16))
            ns.property_mask = struct.unpack(">I",b"\x00"+property_mask)[0]
            nb += 16
        elif self.info['version']=="030":
            ns.number_landmark_points, ns.gender, ns.eye_colour, ns.hair_colour, ns.subject_height, ns.property_mask, \
            ns.expression, ns.pose_yaw, ns.pose_pitch, ns.pose_roll, \
            ns.pose_uncertainty_yaw, ns.pose_uncertainty_pitch, ns.pose_uncertainty_roll = \
                struct.unpack(">HBBBB3s2sbbbbbb",self.fp.read(17))
            nb += 17

        # §5.6 Landmark Point Block
        ns.landmark_points = []
        for n in range(ns.number_landmark_points):
            ns2 = types.SimpleNamespace()
            ns2.point_type, ns2.point_code, ns2.x, ns2.y, ns2.z = \
                struct.unpack(">BBHHH",self.fp.read(8))
            nb += 8

            ns.landmark_points.append(FACLandmarkPoint._make( (
                ns2.point_type, ns2.point_code, ns2.x, ns2.y, ns2.z
            )))

        # §5.7 Image Information Block
        if self.info['version']=="010":
            ns.face_image_type,ns.image_data_type,ns.width,ns.height,ns.colour_space,ns.source_type,ns.device_type,ns.quality = \
                struct.unpack(">BBHHBB2sH", self.fp.read(12))
            nb += 12
            ns.bit_depth,ns.mode = COLOUR_SPACE[ns.colour_space]
        # Buid the namedtuple and convert part of it
        d = dict(
            # capture_datetime=ns.capture_datetime,
            # capture_device_technology_id=ns.capture_device_technology_id,
            # capture_device_vendor_id=ns.capture_device_vendor_id,
            # capture_device_type_id=ns.capture_device_type_id,
            # quality_records=ns.quality_records,
            landmark_points=ns.landmark_points,
            gender={v: k for k, v in GENDER.items()}[ns.gender],
            eye_colour={v: k for k, v in EYE_COLOUR.items()}[ns.eye_colour],
            hair_colour={v: k for k, v in HAIR_COLOUR.items()}[ns.hair_colour],
            # subject_height=ns.subject_height,
            property_mask=[k for k, v in PROPERTY_FLAGS.items() if ns.property_mask & v],
            expression={v: k for k, v in EXPRESSION.items()}[ns.expression],
            pose_yaw=ns.pose_yaw,
            pose_pitch=ns.pose_pitch,
            pose_roll=ns.pose_roll,
            pose_uncertainty_yaw=ns.pose_uncertainty_yaw,
            pose_uncertainty_pitch=ns.pose_uncertainty_pitch,
            pose_uncertainty_roll=ns.pose_uncertainty_roll,
            face_image_type={v: k for k, v in FACE_IMAGE_TYPE.items()}[ns.face_image_type],
            image_data_type={v: k for k, v in IMAGE_DATA_TYPE.items()}[ns.image_data_type],
            source_type={v: k for k, v in SOURCE_TYPE.items()}[ns.source_type],
            device_type=ns.device_type,
            quality=ns.quality,
            )

        # XXX do we need to skip a block after the image?
        return d,nb,ns

#
# Save operations
#
import PIL.JpegImagePlugin
import PIL.Jpeg2KImagePlugin
def _save_frame(im,fp,version):
    # Return bytes for one frame
    try:
        info = im.encoderinfo
    except:
        im.encoderinfo = {}
        info = im.encoderinfo
    image_data = io.BytesIO()

    ns = im.header
    illegal_keys = set(ns.keys()) - {k for k,v in FACRepresentationHeaderInfo.items() if version in v}
    if len(illegal_keys)>0:
        raise SyntaxError("Unknown value in representation header "+str(illegal_keys))

    if ns.get('image_data_type',"JPEG")=="JPEG":
        info['quality'] = 'maximum'
        #info['dpi'] = (im.header.horizontal_image_sampling_rate,im.header.vertical_image_sampling_rate)
        PIL.JpegImagePlugin._save(im, image_data, "")
    elif ns.get('image_data_type',"JPEG")=="JPEG2000":
        # XXX compression ratio
        PIL.Jpeg2KImagePlugin._save(im, image_data, "non.j2k")
    else:
        raise SyntaxError("Unknown compression algo "+ns.get('image_data_type',None))
    image_data = image_data.getvalue()

    rheader = b''
    if version=='030':
        dt = ns.get('capture_datetime',datetime.datetime.now())
        rheader += struct.pack(">HBBBBBH",dt.year,dt.month,dt.day,dt.hour,dt.minute,dt.second,int(dt.microsecond/1000))

    if version=="010":
        rheader += struct.pack(">HBBB3s2sbbbbbb",
            len(ns.get('landmark_points',[])),
            GENDER[ns.get('gender','X')],
            EYE_COLOUR[ns.get('eye_colour','UNSPECIFIED')],
            HAIR_COLOUR[ns.get('hair_colour','UNSPECIFIED')],
            struct.pack(">I", functools.reduce(lambda x,y: x|y, [v for k,v in PROPERTY_FLAGS.items() if k in ns.get('property_mask',[]) ],0))[1:] ,
            EXPRESSION[ns.get('expression','UNSPECIFIED')],
            ns.get('pose_yaw',0),
            ns.get('pose_pitch',0),
            ns.get('pose_roll',0),
            ns.get('pose_uncertainty_yaw',0),
            ns.get('pose_uncertainty_pitch',0),
            ns.get('pose_uncertainty_roll',0) )

    if version=='030':
        for q in ns.get('quality_records',[]):
            rheader += struct.pack(">B2s2s",q.score,q.algo_vendor_id,q.algo_id)

    # Landmark Point Block
    for pt in ns.get('landmark_points',[]):
        rheader += struct.pack(">BBHHH",
            pt.point_type,
            pt.point_code,
            pt.x, pt.y, pt.z)

    # Image Information Block
    rheader += struct.pack(">BBHHBB2sH",
        FACE_IMAGE_TYPE[ns.get('face_image_type','BASIC')],
        IMAGE_DATA_TYPE[ns.get('image_data_type','JPEG')],
        im.size[0], im.size[1],
        [k for k, v in COLOUR_SPACE.items() if im.mode==v[1]][0],
        SOURCE_TYPE[ns.get('source_type','UNSPECIFIED')],
        b"\x00\x00",
        0)

    # Write the frame
    fp.write(struct.pack(">I",4+len(rheader)+len(image_data)))
    fp.write(rheader)
    fp.write(image_data)


def _save(im, fp, filename):
    encoderinfo = im.encoderinfo.copy()
    version = encoderinfo.get("version", im.info.get('version','030'))

    fr = io.BytesIO()
    _save_frame(im,fr,version)
    fr_data = fr.getvalue()

    # Write the general header
    fp.write(b"FAC\x00")
    if version=='010':
        fp.write(struct.pack(">4sIH", b"010\x00",14+len(fr_data),1))

    # Write the frame
    fp.write(fr_data)

def _save_all(im, fp, filename):
    encoderinfo = im.encoderinfo.copy()
    version = encoderinfo.get("version", im.info.get('version','030'))
    append_images = list(encoderinfo.get("append_images", []))
    if not hasattr(im, "n_frames") and not append_images:
        return _save(im, fp, filename)
    images = [im]+append_images

    # Generator to loop on all images/frames
    def frames(images):
        for image in images:
            if not hasattr(image,'n_frames'):
                yield image
            else:
                for idx in range(image.n_frames):
                    image.seek(idx)
                    yield image

    # Generate the frames
    frames_buffers = []
    length = 0
    for frame in frames(images):
        fr = io.BytesIO()
        _save_frame(frame,fr,version)
        frames_buffers.append( fr.getvalue() )
        length += len(frames_buffers[-1])

    # Write the general header
    fp.write(b"FAC\x00")
    if version=='010':
        fp.write(struct.pack(">4sIH", b"010\x00",14+length,len(frames_buffers)))
    elif version=='030':
        fp.write(struct.pack(">4sIH?H", b"030\x00",17+length,len(frames_buffers),0,1 if len(positions)>1 else 0))

    for buf in frames_buffers:
        fp.write(buf)

def _debug(image):
    print('Info'+str(image.info))
    for i in range(image.n_frames):
        image.seek(i)
        print("Frame #%d: mode: %s size=%dx%d" % (i,image.mode, image.size[0], image.size[1]))
        print("\tHeader: ",image.header)
#
# Registration
#
Image.register_open(FACImageFile.format, FACImageFile, _accept)
Image.register_save(FACImageFile.format, _save)
Image.register_save_all(FACImageFile.format, _save_all)

Image.register_extension(FACImageFile.format, ".fac")
Image.register_mime(FACImageFile.format, "image/fac")


if __name__ == "__main__":
    import doctest
    doctest.testmod()


