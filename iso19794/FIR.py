
"""

This module defines a Pillow extension to support ISO 19794:2011 images.

ISO 19794-4 Images
------------------

Reading
'''''''

The :py:meth:`open()` method sets the following ``info`` properties

``version``
    Fixed version (``020``)

``nb_representation``
    The number of representations, i.e. the number of frames

``nb_position``
    The number of position, i.e. the different finger ranks present in the frames

``certification_flag``
    A flag indicating if the certification blocks are included or not

In addition, each frame has the following additional attributes:

``header``
    The representation header (specific to each frame), containing:

    - ``length``: length of this single frame (including this header, the image data and the extended data)
    - ``capture_datetime``
    - ``capture_device_technology_id``
    - ``capture_device_vendor_id``
    - ``capture_device_type_id``
    - ``quality_records``: a list of quality records (``score``, ``algo_vendor_id``, ``algo_id``)
    - ``certification_records``: a list of certification records (``authority_id``, ``scheme_id``)
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
>>> header = FIRRepresentationHeader(
...     length=0,                                       # will be calculated when image is saved
...     capture_datetime = datetime.datetime.now(),
...     capture_device_technology_id=b'\\x00',          # unknown
...     capture_device_vendor_id=b'\\xab\\xcd',
...     capture_device_type_id=b'\\x12\\x34',
...     quality_records=[],
...     certification_records=[],
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
>>> sample.save(buffer,"FIR")
Traceback (most recent call last):
    ...
AttributeError: 'Image' object has no attribute 'header'

Header must be defined on the image for the save operation to work correctly:

>>> sample.header = header
>>> buffer = io.BytesIO()
>>> sample.save(buffer,"FIR")
>>> print(len(buffer.getvalue()))   # should be 200*300 + 41 + 16
60057
>>> print(buffer.getvalue()[0:3])
b'FIR'
>>> print(buffer.getvalue()[4:7])
b'020'
>>> print(buffer.getvalue()[14])
0

Multi-frames image is generated with the ``save_all`` option:

>>> buffer_multi = io.BytesIO()
>>> sample.save(buffer_multi,"FIR",save_all=True,append_images=[sample])
>>> print(len(buffer_multi.getvalue()))   # should be 2*(200*300 + 41) + 16
120098

Certification blocks will alter the flag in the header:

>>> header = header._replace(certification_records = [FIRCertificationRecord(b'\\x78\\xab',b'\\x01')])
>>> sample.header = header
>>> buffer = io.BytesIO()
>>> sample.save(buffer,"FIR")
>>> print(len(buffer.getvalue()))   # should be 200*300 + 42 + 3 + 16
60061
>>> print(buffer.getvalue()[14])
1

Image format is automatically detected:

>>> nsample = Image.open(buffer)
>>> nsample.mode
'L'
>>> nsample.size
(200, 300)
>>> nsample.header.certification_records[0].authority_id
b'x\\xab'

For a single frame image, ``seek`` will fail if we want to access the second frame:

>>> nsample.seek(1)
Traceback (most recent call last):
    ...
EOFError: attempt to seek outside sequence

But it will not fail for a true multi-frame image:

>>> nsample = Image.open(buffer_multi)
>>> nsample.info['nb_representation']
2
>>> nsample.info['nb_position']
1
>>> nsample.seek(1)
>>> nsample.mode
'L'
>>> nsample.size
(200, 300)

Image can be saved in ``JPEG`` format:

>>> buffer = io.BytesIO()
>>> sample.header = sample.header._replace(image_compression_algo='JPEG')
>>> sample.save(buffer,"FIR")
>>> print(len(buffer.getvalue()) < 60061)   # should be less than 200*300 + 42 + 3 + 16
True

The same for a multiframe image:

>>> nsample = Image.open(buffer_multi)
>>> buffer = io.BytesIO()
>>> nsample.header = nsample.header._replace(image_compression_algo='JPEG')
>>> nsample.save(buffer,"FIR",save_all=True)
>>> print(len(buffer.getvalue())>61000 and  len(buffer.getvalue())<120098)
True

Both frames can be compressed:

>>> buffer = io.BytesIO()
>>> nsample.seek(1)
>>> nsample.header = nsample.header._replace(image_compression_algo='JPEG')
>>> nsample.save(buffer,"FIR",save_all=True)
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
>>> sample.header = sample.header._replace(image_compression_algo='JPEG2000_LOSSY')
>>> sample.save(buffer,"FIR")
>>> print(len(buffer.getvalue()) < 6000)
True
>>> sample2 = PIL.Image.open(buffer)
>>> data = sample2.load()
>>> sample2.tobytes()==sample.tobytes()
False

>>> buffer = io.BytesIO()
>>> sample.header = sample.header._replace(image_compression_algo='JPEG2000_LOSSLESS')
>>> sample.save(buffer,"FIR")
>>> print(len(buffer.getvalue()) > 20000)
True
>>> sample2 = PIL.Image.open(buffer)
>>> data = sample2.load()
>>> sample2.tobytes()==sample.tobytes()
True

Using an invalid compression algo will raise an exception:

>>> buffer = io.BytesIO()
>>> sample.header = sample.header._replace(image_compression_algo='UNKNOWN')
>>> sample.save(buffer,"FIR")
Traceback (most recent call last):
    ...
SyntaxError: Unknown compression algo UNKNOWN

"""

# XXX All compressions (missing: PNG)
# XXX Add table 4 (capture device techno)
# XXX Add Table 5 (certification schemes)

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
FIRHeader = namedtuple('FIRHeader',[
    'version',
    'length',
    'nb_repr',
    'cert_flag',
    'nb_pos'
    ])

# Table 2
FIRRepresentationHeader = namedtuple('FIRRepresentationHeader',[
    'length',
    'capture_datetime',
    'capture_device_technology_id',
    'capture_device_vendor_id',
    'capture_device_type_id',
    'quality_records',
    'certification_records',
    'position',
    'number',
    'scale_units',
    'horizontal_scan_sampling_rate',
    'vertical_scan_sampling_rate',
    'horizontal_image_sampling_rate',
    'vertical_image_sampling_rate',
    #'bit_depth',                   # available through image.mode
    'image_compression_algo',
    'impression_type',
    #'horizontal_line_length',      # available through image.size
    #'vertical_line_length'         # available through image.size
    ])


FIRQualityRecord = namedtuple('FIRQualityRecord',[
    'score',
    'algo_vendor_id',
    'algo_id'])
FIRCertificationRecord = namedtuple('FIRCertificationRecord',[
    'authority_id',
    'scheme_id'])

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
    return prefix[:4] == b"FIR\x00"

class FIRImageFile(ImageFile.ImageFile):

    format = "FIR"
    format_description = "ISO19794-4 image (fingerprint image)"
    _close_exclusive_fp_after_loading = False

    def _open(self):
        # General header (§8.2)
        header = self.fp.read(16)
        if header[:4] != b"FIR\x00":
            raise SyntaxError("not a ISO19794-4 file")

        if header[4:8] != b"020\x00":
            raise SyntaxError("Invalid version for a ISO19794-4 file")

        # Big Endian (§6.1)
        header = FIRHeader._make(struct.unpack(">4sIH?B",header[4:]))
        self.info['version'] = header.version
        self.info['nb_representation'] = header.nb_repr
        self.info['nb_position'] = header.nb_pos
        self.info['certification_flag'] = header.cert_flag

        # setup frame pointers
        self.__first = self.__next = 16     # skip the general header
        self.__frame = -1
        self.__fp = self.fp
        self._frame_pos = []
        self.n_frames = header.nb_repr

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
                raise EOFError("no more images in FIR file")
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
        self.header = self._rheaders[frame]
        self.__next = self._frame_pos[frame] + self.header.length
        self.__frame = frame

        if ns.bit_depth==8:
            self.mode = "L"
        try:
            self.size = (ns.horizontal_line_length,ns.vertical_line_length)
        except AttributeError:
            # Support Pillow >= 5.3.0
            self._size = (ns.horizontal_line_length,ns.vertical_line_length)

        # data descriptor
        # Select decoder: RAW, RAW_PACKED, WSQ, JPEG, JPEG2000_LOSSY, JPEG2000_LOSSLESS, PNG
        if rheader.image_compression_algo=="RAW" or rheader.image_compression_algo=="RAW_PACKED":
            self.tile = [
                ('raw', (0, 0) + self.size, self._frame_pos[frame]+offset, (self.mode, 0, 1))
            ]
        elif rheader.image_compression_algo=="WSQ":
            self.tile = [
                ('wsq', (0, 0) + self.size, self._frame_pos[frame]+offset, (12,))
            ]
        elif rheader.image_compression_algo=="JPEG":
            self.tile = [
                ('jpeg', (0, 0) + self.size, self._frame_pos[frame]+offset, (self.mode,self.mode,1,0))
            ]
        elif rheader.image_compression_algo=="JPEG2000_LOSSY" or rheader.image_compression_algo=="JPEG2000_LOSSLESS":
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
            raise SyntaxError("Unknown compression algo "+rheader.image_compression_algo)


    def tell(self):
        "Return the current frame number"
        return self.__frame

    def read_header(self):
        # Reader representation header starting at current position
        # return a namedtuple
        nb = 0
        # Temporary namespace used during the analysis of the header
        ns = types.SimpleNamespace()

        ns.length,ns.capture_datetime,ns.capture_device_technology_id,ns.capture_device_vendor_id,ns.capture_device_type_id,q_length = \
            struct.unpack(">I9ss2s2sB",self.fp.read(19))
        # XXX micro or milli seconds?
        ns.capture_datetime = datetime.datetime( *struct.unpack(">HBBBBBH",ns.capture_datetime) )
        nb += 19
        Q = []
        for i in range(q_length):
            Q.append( FIRQualityRecord._make( struct.unpack(">B2s2s",self.fp.read(5)) ) )
            nb += 5
        ns.quality_records = Q

        C = []
        if self.info['certification_flag']:
            (c_length,) = struct.unpack(">B",self.fp.read(1))
            nb += 1
            for i in range(c_length):
                C.append( FIRCertificationRecord._make( struct.unpack(">2s1s",self.fp.read(3)) ) )
                nb += 3
        ns.certification_records = C

        ns.position,ns.number,ns.scale_units,ns.horizontal_scan_sampling_rate,ns.vertical_scan_sampling_rate, \
        ns.horizontal_image_sampling_rate,ns.vertical_image_sampling_rate,ns.bit_depth,ns.image_compression_algo, \
        ns.impression_type,ns.horizontal_line_length,ns.vertical_line_length,ns.image_data_length = \
            struct.unpack(">BBBHHHHBBBHHI",self.fp.read(22))
        nb += 22

        # Buid the namedtuple and convert part of it
        nt = FIRRepresentationHeader._make( (
            ns.length,
            ns.capture_datetime,ns.capture_device_technology_id,ns.capture_device_vendor_id,ns.capture_device_type_id,
            ns.quality_records,ns.certification_records,
            {v: k for k, v in POSITION.items()}[ns.position],
            ns.number,
            {v: k for k, v in UNIT.items()}[ns.scale_units],
            ns.horizontal_scan_sampling_rate,
            ns.vertical_scan_sampling_rate,
            ns.horizontal_image_sampling_rate,
            ns.vertical_image_sampling_rate,
            #ns.bit_depth,
            {v: k for k, v in COMPRESSION.items()}[ns.image_compression_algo],
            {v: k for k, v in IMPRESSION.items()}[ns.impression_type],
            #ns.horizontal_line_length,
            #ns.vertical_line_length
            ) )
        return nt,nb,ns

#
# Save operations
#
import PIL.JpegImagePlugin
import PIL.Jpeg2KImagePlugin
def _save_frame(im,fp,cert_flag):
    # Return bytes for one frame
    try:
        info = im.encoderinfo
    except:
        im.encoderinfo = {}
        info = im.encoderinfo
    image_data = io.BytesIO()

    ns = im.header
    if im.mode == 'L':
        bit_depth = 8
    else:
        bit_depth = 24

    if ns.image_compression_algo=="RAW":
        im.encoderconfig = ()
        encoder = ('raw', (0, 0) + im.size, 0, (im.mode, 0, 1))
        bit_depth = 8
        ImageFile._save(im, image_data, [encoder])
    elif ns.image_compression_algo=="RAW_PACKED":
        im.encoderconfig  ()
        encoder = ('raw', (0, 0) + im.size, 0, (im.mode, 0, 1))
        bit_depth = 8
        ImageFile._save(im, image_data, [encoder])
    elif ns.image_compression_algo=="WSQ":
        im.encoderconfig  ()
        encoder = ('wsq', (0, 0) + im.size, 0, (12,))
        bit_depth = 8
        ImageFile._save(im, image_data, [encoder])
    elif ns.image_compression_algo=="JPEG":
        info['quality'] = 'maximum'
        info['dpi'] = (im.header.horizontal_image_sampling_rate,im.header.vertical_image_sampling_rate)
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
    if cert_flag:
        rheader += struct.pack(">B",len(ns.certification_records))
        for c in ns.certification_records:
            rheader += struct.pack(">2s1s",c.authority_id,c.scheme_id)

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
    _save_frame(im,fr,len(im.header.certification_records)>0)
    fr_data = fr.getvalue()

    # Write the general header
    fp.write(b"FIR\x00")
    fp.write(struct.pack(">4sIH?B", b"020\x00",16+len(fr_data),1,len(im.header.certification_records)>0,1))

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

    # check if there is a certification block
    cert_flag = False
    # Count number of position
    positions = set()
    for frame in frames(images):
        if len(frame.header.certification_records)>0:
            cert_flag = True
        positions.add(frame.header.position)

    # Generate the frames
    frames_buffers = []
    length = 0
    for frame in frames(images):
        fr = io.BytesIO()
        _save_frame(frame,fr,cert_flag)
        frames_buffers.append( fr.getvalue() )
        length += len(frames_buffers[-1])

    # Write the general header
    fp.write(b"FIR\x00")
    fp.write(struct.pack(">4sIH?B", b"020\x00",16+length,len(frames_buffers),cert_flag,len(positions)))

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
Image.register_open(FIRImageFile.format, FIRImageFile, _accept)
Image.register_save(FIRImageFile.format, _save)
Image.register_save_all(FIRImageFile.format, _save_all)

Image.register_extension(FIRImageFile.format, ".fir")
Image.register_mime(FIRImageFile.format, "image/fir")


if __name__ == "__main__":
    import doctest
    doctest.testmod()


