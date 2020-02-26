
"""

This module defines a Pillow extension to support ISO 19794:2011 images.

ISO 19794-5 Images
------------------

Reading
'''''''

When opening an ISO 19794-5 image, the following fields are set:

header
    The header of the image with the number of representations (number of frames)
    and the number of positions. The header is not required when saving an image
    (content will be inferred from the frames). Header contains:

    - ``version``: fixed version (``020``)
    - ``length``: length of the image
    - ``nb_repr``: number of representations
    - ``cert_flag``: always 0
    - ``temporal_semantics``: number of position

rheader
    The representation header (specific to each frame), containing:

    - ``length``: length of this single frame (including this header, the image data and the extended data)
    - ``capture_datetime``
    - ``capture_device_technology_id``
    - ``capture_device_vendor_id``
    - ``capture_device_type_id``
    - ``quality_records``: a list of quality records (``score``, ``algo_vendor_id``, ``algo_id``)
    - ``position``: the finger/plam position as a text
    - ``number``: the image number
    - ``scale_units``: the scale unit as a text
    - ``horizontal_scan_sampling_rate``
    - ``vertical_scan_sampling_rate``
    - ``horizontal_image_sampling_rate``
    - ``vertical_image_sampling_rate``
    - ``image_compression_algo``: the compression algo as a text
    - ``impression_type``: the impression type as text

    When reading an image the fields ``position``, ``scale_units``, ``image_compression_algo`` and
    ``impression_type`` are converted to readable text. When writing image, the numeric value can be defined
    if this is more convenient to use.

Both header and rheader are returned as namedtuple.

Writing
'''''''

The ``save()`` method can take the following keyword arguments:

``save_all``
    If true, Pillow will save all frames of the image to a multirepresentation file.

``append_images``
    A list of images to append as additional frames. Each of the images in the list
    can be a single or multiframe image.

Usage
'''''

First, let's create a sample image looking like a fingerprint:

>>> from PIL import Image, ImageDraw
>>> sample = Image.new("L",(200,300),255)
>>> draw = ImageDraw.Draw(sample)
>>> for i in range(20,100,10):
...     for n in range(5):
...         draw.ellipse( (i+n,i+n,200-i-n,300-i-n),outline=0)

To build a single frame image, we first need a representation header. This can be built from
a list of key/value.

>>> import datetime
>>> rheader = FACRepresentationHeader(
...     length=0,                                       # will be calculated when image is saved
...     capture_datetime = datetime.datetime.now(),
...     capture_device_technology_id=b'\\x00',          # unknown
...     capture_device_vendor_id=b'\\xab\\xcd',
...     capture_device_type_id=b'\\x12\\x34',
...     quality_records=[],
...     position='Left index finger',
...     number=1,
...     scale_units='PPI',
...     horizontal_scan_sampling_rate=500,
...     vertical_scan_sampling_rate=500,
...     horizontal_image_sampling_rate=500,
...     vertical_image_sampling_rate=500,
...     image_compression_algo='RAW',
...     impression_type='Live-scan rolled'
... )

An image with no representation header will not be generated

>>> import io
>>> buffer = io.BytesIO()
>>> sample.save(buffer,"FAC")
Traceback (most recent call last):
    ...
AttributeError: 'Image' object has no attribute 'rheader'

Header must be defined on the image for the save operation to work correctly:

>>> sample.rheader = rheader
>>> buffer = io.BytesIO()
>>> sample.save(buffer,"FAC")
>>> print(len(buffer.getvalue()))   # should be 200*300 + 41 + 16
60057
>>> print(buffer.getvalue()[0:3])
b'FAC'
>>> print(buffer.getvalue()[4:7])
b'020'
>>> print(buffer.getvalue()[14])
0

Multi-frames image is generated with the ``save_all`` option:

>>> buffer_multi = io.BytesIO()
>>> sample.save(buffer_multi,"FAC",save_all=True,append_images=[sample])
>>> print(len(buffer_multi.getvalue()))   # should be 2*(200*300 + 41) + 16
120098

For a single frame image, ``seek`` will fail if we want to access the second frame:

>>> nsample.seek(1)
Traceback (most recent call last):
    ...
EOFError: attempt to seek outside sequence

But it will not fail for a true multi-frame image:

>>> nsample = Image.open(buffer_multi)
>>> nsample.header.nb_repr
2
>>> nsample.header.nb_pos
1
>>> nsample.seek(1)
>>> nsample.mode
'L'
>>> nsample.size
(200, 300)

Image can be saved in ``JPEG`` format:

>>> buffer = io.BytesIO()
>>> sample.rheader = sample.rheader._replace(image_compression_algo='JPEG')
>>> sample.save(buffer,"FAC")
>>> print(len(buffer.getvalue()) < 60061)   # should be less than 200*300 + 42 + 3 + 16
True

The same for a multiframe image:

>>> nsample = Image.open(buffer_multi)
>>> buffer = io.BytesIO()
>>> nsample.rheader = nsample.rheader._replace(image_compression_algo='JPEG')
>>> nsample.save(buffer,"FAC",save_all=True)
>>> print(len(buffer.getvalue())>61000 and  len(buffer.getvalue())<120098)
True

Both frames can be compressed:

>>> buffer = io.BytesIO()
>>> nsample.seek(1)
>>> nsample.rheader = nsample.rheader._replace(image_compression_algo='JPEG')
>>> nsample.save(buffer,"FAC",save_all=True)
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
>>> sample.rheader = sample.rheader._replace(image_compression_algo='JPEG2000_LOSSY')
>>> sample.save(buffer,"FAC")
>>> print(len(buffer.getvalue()) < 6000)
True
>>> sample2 = PIL.Image.open(buffer)
>>> data = sample2.load()
>>> sample2.tobytes()==sample.tobytes()
False

>>> buffer = io.BytesIO()
>>> sample.rheader = sample.rheader._replace(image_compression_algo='JPEG2000_LOSSLESS')
>>> sample.save(buffer,"FAC")
>>> print(len(buffer.getvalue()) > 20000)
True
>>> sample2 = PIL.Image.open(buffer)
>>> data = sample2.load()
>>> sample2.tobytes()==sample.tobytes()
True

Using an invalid compression algo will raise an exception:

>>> buffer = io.BytesIO()
>>> sample.rheader = sample.rheader._replace(image_compression_algo='UNKNOWN')
>>> sample.save(buffer,"FAC")
Traceback (most recent call last):
    ...
SyntaxError: Unknown compression algo UNKNOWN

"""

import io
import datetime
import struct
import types
from collections import namedtuple

from PIL import Image, ImageFile

#------------------------------------------------------------------------------
#
# Namedtuple types extracted from the standard for Type 4 (fingerprint and palmprint)
#
#------------------------------------------------------------------------------

# Table 1
FACHeader = namedtuple('FACHeader',[
    'version',
    'length',
    'nb_repr',
    'cert_flag',
    'temporal_semantics'
    ])


FACLandmarkPoint = namedtuple('FACLandmarkPoint',[
    'point_type',
    'point_code',
    'x',
    'y',
    'z'
    ])

# 
FACRepresentationHeader = namedtuple('FACRepresentationHeader',[
    'length',
    'capture_datetime',
    'capture_device_technology_id',
    'capture_device_vendor_id',
    'capture_device_type_id',
    'quality_records',
    'landmark_points',
    'gender',
    'eye_colour',
    'hair_colour',
    'subject_height',
    'property_mask',
    'expression',
    'pose_yaw',
    'pose_pitch',
    'pose_roll',
    'pose_uncertainty_yaw',
    'pose_uncertainty_pitch',
    'pose_uncertainty_roll',
    'face_image_type',
    'image_data_type',
    'width',
    'height',
    'colour_space',
    'source_type',
    'device_type',
    'quality',
    'bit_depth',
    ])

FACQualityRecord = namedtuple('FACQualityRecord',[
    'score',
    'algo_vendor_id',
    'algo_id'])

# Conversion of position (Table 6, 7 and 8)
POSITION = {
    # Table 6
    'Unknown': 0,
    'Right thumb': 1,
    'Right index finger': 2,
    'Right middle finger': 3,
    'Right ring finger': 4,
    'Right little finger': 5,
    'Left thumb': 6,
    'Left index finger': 7,
    'Left middle finger': 8,
    'Left ring finger': 9,
    'Left little finger': 10,
    'Plain right four fingers': 13,
    'Plain left four fingers': 14,
    'Plain thumbs (2)': 15,
    # Table 7
    'Right index and middle': 40,
    'Right middle and ring': 41,
    'Right ring and little': 42,
    'Left index and middle': 43,
    'Left middle and ring': 44,
    'Left ring and little': 45,
    'Right index and Left index': 46,
    'Right index and middle and ring': 47,
    'Right middle and ring and little': 48,
    'Left index and middle and ring': 49,
    'Left middle and ring and little': 50,
    # Table 8
    'Unknown palm': 20,
    'Right full palm': 21,
    'Right writer\'s palm': 22,
    'Left full palm': 23,
    'Left writer\'s palm': 24,
    'Right lower palm': 25,
    'Right upper palm': 26,
    'Left lower palm': 27,
    'Left upper palm': 28,
    'Right other': 29,
    'Left other': 30,
    'Right interdigital': 31,
    'Right thenar': 32,
    'Right hypothenar': 33,
    'Left interdigital': 34,
    'Left thenar': 35,
    'Left hypothenar': 36,
}

# Conversion of compression (Table 9)
COMPRESSION = {
    'RAW': 0,
    'RAW_PACKED': 1,
    'WSQ': 2,
    'JPEG': 3,
    'JPEG2000_LOSSY': 4,
    'JPEG2000_LOSSLESS': 5,
    'PNG': 6,
}

# Conversion of impression type (Table 10)
IMPRESSION = {
    'Live-scan plain': 0,
    'Live-scan rolled': 1,
    'Nonlive-scan plain': 2,
    'Nonlive-scan rolled': 3,
    'Latent impression': 4,
    'Latent tracing': 5,
    'Latent photo': 6,
    'Latent lift': 7,
    'Live-scan swipe': 8,
    'Live-scan vertical roll': 9,
    'Live-scan palm': 10,
    'Nonlive-scan palm': 11,
    'Latent palm impression': 12,
    'Latent palm tracing': 13,
    'Latent palm photo': 14,
    'Latent palm lift': 15,
    'Live-scan optical contactless plain': 24,
    'Other': 28,
    'Unknown': 29,
}

# Conversion of units (Table 2)
UNIT = {
    'PPI': 1,
    'PPCM': 2,
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

        if header[4:8] != b"010\x00" and header[4:8] != b"030\x00":
            raise SyntaxError("Invalid version for a ISO19794-5 file")

        # Big Endian (§6.1)
        if header[4:8] == b"010\x00":
            self.header = FACHeader._make(struct.unpack(">4sIH",header[4:14])+(False,0))
            self.__first = self.__next = 14     # skip the general header

        if header[4:8] == b"030\x00":
            self.header = FACHeader._make(struct.unpack(">4sIH?H",header[4:17]))
            self.__first = self.__next = 17     # skip the general header

        self.__frame = -1
        self.__fp = self.fp
        self._frame_pos = []
        self.n_frames = self.header.nb_repr

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
        if self.__frame>=0 and hasattr(self,"rheader"):
            self._rheaders[self.__frame] = self.rheader
        self.fp = self.__fp
        while len(self._frame_pos) <= frame:
            if not self.__next:
                raise EOFError("no more images in FAC file")
            # reset python3 buffered io handle in case fp
            # was passed to a libxxx, invalidating the buffer
            self.fp.tell()
            self.fp.seek(self.__next)
            self._frame_pos.append(self.__next)
            rheader,offset,ns = self.read_header()
            self._rheaders.append(rheader)
            self.__next = self._frame_pos[frame] + rheader.length
            self.__frame += 1
        self.fp.seek(self._frame_pos[frame])
        rheader,offset,ns = self.read_header()
        self.rheader = self._rheaders[frame]
        self.__next = self._frame_pos[frame] + self.rheader.length
        self.__frame = frame

        if ns.bit_depth==8:
            self.mode = "L"
        else:
            self.mode = "RGB"
        try:
            self.size = (ns.width,ns.height)
        except AttributeError:
            # Support Pillow >= 5.3.0
            self._size = (ns.width,ns.height)

        # data descriptor
        # Select decoder
        if rheader.image_data_type==0:
            self.tile = [
                ('jpeg', (0, 0) + self.size, self._frame_pos[frame]+offset, (self.mode,self.mode,1,0))
            ]
        elif rheader.image_data_type==1:
            sig = self.fp.read(4)
            codec = "j2k"
            if sig == b"\xff\x4f\xff\x51":
                codec = "j2k"
            else:
                sig = sig + self.fp.read(8)

                if sig == b"\x00\x00\x00\x0cjP  \x0d\x0a\x87\x0a":
                    codec = "jp2"
            self.tile = [
                ('jpeg2k', (0, 0) + self.size, self._frame_pos[frame]+offset, (codec,))
            ]
        else:
            raise SyntaxError("Unknown image_data_type "+repr(rheader.image_data_type))

    def tell(self):
        "Return the current frame number"
        return self.__frame

    def read_header(self):
        # Reader representation header starting at current position
        # return a namedtuple
        nb = 0
        # Temporary namespace used during the analysis of the header
        ns = types.SimpleNamespace()
        if self.header.version==b"010\x00":
            ns.length, = struct.unpack(">I",self.fp.read(4))
            # Init other
            ns.capture_datetime = datetime.datetime.now()
            ns.capture_device_technology_id = "\x00"
            ns.capture_device_vendor_id = "\x00\x00"
            ns.capture_device_type_id = "\x00\x00"
            ns.quality_records = []
            nb += 4
        if self.header.version==b"030\x00":
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
        if self.header.version==b"010\x00":
            ns.number_landmark_points, ns.gender, ns.eye_colour, ns.hair_colour, ns.property_mask, \
            ns.expression, ns.pose_yaw, ns.pose_pitch, ns.pose_roll, \
            ns.pose_uncertainty_yaw, ns.pose_uncertainty_pitch, ns.pose_uncertainty_roll = \
                struct.unpack(">HBBB3s2sbbbbbb",self.fp.read(16))
            ns.subject_height = 0
            nb += 16
        if self.header.version==b"030\x00":
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
        if self.header.version==b"010\x00":
            ns.face_image_type,ns.image_data_type,ns.width,ns.height,ns.colour_space,ns.source_type,ns.device_type,ns.quality = \
                struct.unpack(">BBHHBB2sH", self.fp.read(12))
            nb += 12
            if ns.colour_space==1:
                ns.bit_depth = 24
            elif ns.colour_space==3:
                ns.bit_depth = 8
            else:
                ns.bit_depth = 24
        # Buid the namedtuple and convert part of it
        nt = FACRepresentationHeader._make( (
            ns.length,
            ns.capture_datetime,ns.capture_device_technology_id,ns.capture_device_vendor_id,ns.capture_device_type_id,
            ns.quality_records,
            ns.landmark_points,
            ns.gender,
            ns.eye_colour,
            ns.hair_colour,
            ns.subject_height,
            ns.property_mask,
            ns.expression,
            ns.pose_yaw,
            ns.pose_pitch,
            ns.pose_roll,
            ns.pose_uncertainty_yaw,
            ns.pose_uncertainty_pitch,
            ns.pose_uncertainty_roll,
            ns.face_image_type,
            ns.image_data_type,
            ns.width,
            ns.height,
            ns.colour_space,
            ns.source_type,
            ns.device_type,
            ns.quality,
            ns.bit_depth,
            ) )

        # XXX do we need to skip a block after the image?
        return nt,nb,ns

#
# Save operations
#
import PIL.JpegImagePlugin
import PIL.Jpeg2KImagePlugin
def _save_frame(im,fp):
    # Return bytes for one frame
    try:
        info = im.encoderinfo
    except:
        im.encoderinfo = {}
        info = im.encoderinfo
    image_data = io.BytesIO()

    ns = im.rheader
    if im.mode == 'L':
        bit_depth = 8
    else:
        bit_depth = 24

    if ns.image_compression_algo=="JPEG":
        info['quality'] = 'maximum'
        info['dpi'] = (im.rheader.horizontal_image_sampling_rate,im.rheader.vertical_image_sampling_rate)
        PIL.JpegImagePlugin._save(im, image_data, "")
    elif ns.image_compression_algo=="JPEG2000_LOSSY":
        info['quality_mode'] = "rates"
        info['quality_layers'] = (15,)
        # XXX parameters needed? (up to 15 compression max according to the specs)
        PIL.Jpeg2KImagePlugin._save(im, image_data, "non.j2k")
    elif ns.image_compression_algo=="JPEG2000_LOSSLESS":
        info['quality_mode'] = "rates"
        info['quality_layers'] = (0,)
        # XXX parameters needed? (up to 15 compression max according to the specs)
        PIL.Jpeg2KImagePlugin._save(im, image_data, "non.j2k")
    else:
        raise SyntaxError("Unknown compression algo "+ns.image_compression_algo)
    image_data = image_data.getvalue()

    dt = ns.capture_datetime
    rheader = b''
    rheader += struct.pack(">HBBBBBH",dt.year,dt.month,dt.day,dt.hour,dt.minute,dt.second,int(dt.microsecond/1000))
    rheader += struct.pack(">s2s2sB",ns.capture_device_technology_id,ns.capture_device_vendor_id,ns.capture_device_type_id,len(ns.quality_records))
    for q in ns.quality_records:
        rheader += struct.pack(">B2s2s",q.score,q.algo_vendor_id,q.algo_id)

    rheader += struct.pack(">BBBHHHHBBBHHI",
        ns.position if type(ns.position) is int else POSITION[ns.position],
        ns.number,
        ns.scale_units if type(ns.scale_units) is int else UNIT[ns.scale_units],
        ns.horizontal_scan_sampling_rate,
        ns.vertical_scan_sampling_rate,
        ns.horizontal_image_sampling_rate,
        ns.vertical_image_sampling_rate,
        bit_depth,
        ns.image_compression_algo if type(ns.image_compression_algo) is int else COMPRESSION[ns.image_compression_algo],
        ns.impression_type if type(ns.impression_type) is int else IMPRESSION[ns.impression_type],
        im.size[0],
        im.size[1],
        len(image_data)
    )

    # Write the frame
    fp.write(struct.pack(">I",4+len(rheader)+len(image_data)))
    fp.write(rheader)
    fp.write(image_data)


def _save(im, fp, filename):

    fr = io.BytesIO()
    _save_frame(im,fr)
    fr_data = fr.getvalue()

    # Write the general header
    fp.write(b"FAC\x00")
    fp.write(struct.pack(">4sIH?H", b"030\x00",17+len(fr_data),1,False,0))

    # Write the frame
    fp.write(fr_data)

def _save_all(im, fp, filename):
    encoderinfo = im.encoderinfo.copy()
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

    # Count number of position
    positions = set()
    for frame in frames(images):
        positions.add(frame.rheader.position)

    # Generate the frames
    frames_buffers = []
    length = 0
    for frame in frames(images):
        fr = io.BytesIO()
        _save_frame(frame,fr)
        frames_buffers.append( fr.getvalue() )
        length += len(frames_buffers[-1])

    # Write the general header
    fp.write(b"FAC\x00")
    fp.write(struct.pack(">4sIH?H", b"030\x00",17+length,len(frames_buffers),0,1 if len(positions)>1 else 0))

    for buf in frames_buffers:
        fp.write(buf)

def _debug(image):
    print('GeneralHeader'+str(image.header))
    for i in range(image.n_frames):
        image.seek(i)
        print("Frame #%d: mode: %s size=%dx%d" % (i,image.mode, image.size[0], image.size[1]))
        print("\tHeader: ",image.rheader)
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


