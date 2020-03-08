
import unittest
import io
import os
import datetime

import PIL.Image
import PIL.ImageDraw
import iso19794
from iso19794.FIR import *

#_______________________________________________________________________________
class TestFIR(unittest.TestCase):
    
    def test_fir1(self):
        # check we can read an ISO image
        i = PIL.Image.open(os.path.join(os.path.dirname(__file__),'annexc.fir'))
        self.assertEqual(i.info['nb_representation'],1)
        self.assertEqual(i.info['nb_position'],1)
        # self.assertEqual(i.info['length'],234441)
        i.header['position'] = 'RIGHT_RING_FINGER'
        with self.assertRaises(EOFError):
            i.seek(1)
        # rotate the image
        i2 = i.rotate(45,expand=True,fillcolor=128)        
        i2.header = i.header
        i2.header = i.header
        # check we can save it
        buf = io.BytesIO()
        i2.save(buf,"FIR")
        self.assertGreater( len(buf.getvalue()) , 1000 )

    def test_fir2(self):
        # check we can read an ISO image
        i = PIL.Image.open(os.path.join(os.path.dirname(__file__),'twofingers.fir'))
        self.assertEqual(i.info['nb_representation'],2)
        self.assertEqual(i.info['nb_position'],2)
        self.assertEqual(i.header['position'],'LEFT_INDEX_FINGER')
        i.rotate(90)
        i.seek(1)
        i.rotate(90)
        self.assertEqual(i.info['nb_representation'],2)
        self.assertEqual(i.info['nb_position'],2)
        self.assertEqual(i.header['position'],'LEFT_MIDDLE_FINGER')
        with self.assertRaises(EOFError):
            i.seek(2)

    def test_multi(self):
        i1 = PIL.Image.open(os.path.join(os.path.dirname(__file__),'annexc.fir'))
        i2 = PIL.Image.open(os.path.join(os.path.dirname(__file__),'twofingers.fir'))
        buf = io.BytesIO()
        i1.save(buf,"FIR",save_all=True,append_images=[i2])

        i = PIL.Image.open(buf)
        self.assertEqual(i.info['nb_representation'],3)
        self.assertEqual(i.info['nb_position'],2)

    def test_v20(self):
        sample = PIL.Image.new("L",(200,300),255)
        draw = PIL.ImageDraw.Draw(sample)
        for i in range(20,100,10):
            for n in range(5):
                draw.ellipse( (i+n,i+n,200-i-n,300-i-n),outline=0)

        header = dict(
            capture_datetime = datetime.datetime.now(),
            capture_device_technology_id=b'\\x00',          # unknown
            capture_device_vendor_id=b'\\xab\\xcd',
            capture_device_type_id=b'\\x12\\x34',
            quality_records=[],
            certification_records=[],
            position='LEFT_INDEX_FINGER',
            number=1,
            scale_units='PPI',
            horizontal_scan_sampling_rate=500,
            vertical_scan_sampling_rate=500,
            horizontal_image_sampling_rate=500,
            vertical_image_sampling_rate=500,
            image_compression_algo='RAW',
            impression_type='LIVESCAN_ROLLED'
        )

        # Header is mandatory
        buffer = io.BytesIO()
        with self.assertRaises(AttributeError,msg="'Image' object has no attribute 'header'"):
            sample.save(buffer,"FIR")

        # Save
        sample.header = header
        buffer = io.BytesIO()
        sample.save(buffer,"FIR")
        self.assertEqual(len(buffer.getvalue()),200*300+41+16)
        self.assertEqual(buffer.getvalue()[14],0)

        # Save multi
        buffer_multi = io.BytesIO()
        sample.save(buffer_multi,"FIR",save_all=True,append_images=[sample])
        self.assertEqual(len(buffer_multi.getvalue()), 2*(200*300 + 41) + 16)

        # Check cert flag
        header['certification_records'] = [FIRCertificationRecord(b'\x78\xab',b'\x01')]
        sample.header = header
        buffer = io.BytesIO()
        sample.save(buffer,"FIR")
        self.assertEqual(len(buffer.getvalue()),200*300 + 42 + 3 + 16)
        self.assertEqual(buffer.getvalue()[14],1)
        with self.assertRaises(EOFError):
            sample.seek(1)

        # Read the multi frame image
        nsample = Image.open(buffer)
        self.assertEqual(nsample.mode,'L')
        self.assertEqual(nsample.size, (200, 300))
        self.assertEqual(nsample.header['certification_records'][0].authority_id, b'x\xab')

        # Test JPEG compression
        buffer = io.BytesIO()
        sample.header['image_compression_algo'] ='JPEG'
        sample.save(buffer,"FIR")
        self.assertLess(len(buffer.getvalue()), 200*300 + 42 + 3 + 16 - 1)

        nsample = Image.open(buffer_multi)
        buffer = io.BytesIO()
        nsample.header['image_compression_algo'] ='JPEG'
        nsample.seek(1)
        nsample.header['image_compression_algo'] ='JPEG'
        nsample.save(buffer,"FIR",save_all=True)

        # Read

        nsample2 = PIL.Image.open(buffer)
        data = nsample2.load()  # force decoding of the image
        nsample2.seek(1)
        data = nsample2.load()

        # Test JPEG2000
        buffer = io.BytesIO()
        sample.header['image_compression_algo'] ='JPEG2000_LOSSY'
        sample.save(buffer,"FIR")
        self.assertLess(len(buffer.getvalue()), 6000)
        sample2 = PIL.Image.open(buffer)
        data = sample2.load()

        buffer = io.BytesIO()
        sample.header['image_compression_algo'] ='JPEG2000_LOSSLESS'
        sample.save(buffer,"FIR")
        self.assertGreater(len(buffer.getvalue()), 20000)
        sample2 = PIL.Image.open(buffer)
        data = sample2.load()
        self.assertEqual(sample2.tobytes(),sample.tobytes())

        # Invalid compression
        buffer = io.BytesIO()
        sample.header['image_compression_algo'] ='UNKNOWN'
        with self.assertRaises(SyntaxError, msg="Unknown compression algo UNKNOWN"):
            sample.save(buffer,"FIR")

#_______________________________________________________________________________
class TestFAC(unittest.TestCase):

    def test_v010(self):
        # Build a sample image
        sample = PIL.Image.new("RGB",(200,300),255)
        draw = PIL.ImageDraw.Draw(sample)
        for i in range(20,100,10):
            for n in range(5):
                draw.ellipse( (i+n,i+n,200-i-n,300-i-n),outline=0)

        # Prepare frame header
        header = dict(
            landmark_points=[],
            gender='M',
            eye_colour='BLUE',
            hair_colour='BLACK',
            property_mask=['GLASSES'],
            expression='NEUTRAL',
            pose_yaw=0,
            pose_pitch=0,
            pose_roll=0,
            pose_uncertainty_yaw=0,
            pose_uncertainty_pitch=0,
            pose_uncertainty_roll=0,
            face_image_type='FULL_FRONTAL',
            image_data_type='JPEG',
            source_type='STATIC_CAMERA',
            device_type=b'\\x00\\x00',
            quality=b'\\x00\\x00',
        )

        # Header is mandatory
        buffer = io.BytesIO()
        with self.assertRaises(AttributeError,msg="'Image' object has no attribute 'header'"):
            sample.save(buffer,"FAC", version='010')

        sample.header = header
        buffer = io.BytesIO()
        sample.save(buffer,"FAC", version='010')
        self.assertLess(len(buffer.getvalue()),56000)

        # Read the image
        nsample = PIL.Image.open(buffer)
        self.assertEqual(nsample.mode, 'RGB')
        self.assertEqual(nsample.size, (200, 300))

        with self.assertRaises(EOFError):
            nsample.seek(1)

        # Generate a multi frame image
        buffer_multi = io.BytesIO()
        sample.save(buffer_multi,"FAC",save_all=True,append_images=[sample], version='010')
        self.assertLess(len(buffer_multi.getvalue()),111000)

        # Define compression
        nsample = PIL.Image.open(buffer_multi)
        buffer = io.BytesIO()
        nsample.header['image_data_type'] = 'JPEG2000'
        nsample.seek(1)
        nsample.header['image_data_type'] = 'JPEG2000'
        nsample.save(buffer,"FAC",version='010',save_all=True)
        self.assertLess(len(buffer.getvalue()),len(buffer_multi.getvalue()))

        # Check JPEG2000 can be read
        nsample2 = PIL.Image.open(buffer)
        data = nsample2.load()  # force decoding of the image
        nsample2.seek(1)
        data = nsample2.load()

        # Invalid image data type
        buffer = io.BytesIO()
        sample.header['image_data_type'] = 'UNKNOWN'
        with self.assertRaises(SyntaxError,msg="Unknown compression algo UNKNOWN"):
            sample.save(buffer,"FAC",version='010')

    def test_v010_property_mask(self):
        # Builid a sample image
        sample = PIL.Image.new("RGB",(200,300),255)
        draw = PIL.ImageDraw.Draw(sample)
        for i in range(20,100,10):
            for n in range(5):
                draw.ellipse( (i+n,i+n,200-i-n,300-i-n),outline=0)

        # Prepare frame header
        header = dict(
            property_mask=['GLASSES'],  # => b0000 0010 = \x02
        )

        sample.header = header
        buffer1 = io.BytesIO()
        sample.save(buffer1,"FAC", version='010')

        header = dict(
            property_mask=['GLASSES','BEARD','LEFT_EYE_PATCH','DARK_GLASSES'], # => b1000 1010 = \x8a
        )

        sample.header = header
        buffer2 = io.BytesIO()
        sample.save(buffer2,"FAC", version='010')

        self.assertEqual(buffer1.getvalue()[23:26],b"\x00\x00\x02")
        self.assertEqual(buffer2.getvalue()[23:26],b"\x00\x02\x8a")

# ______________________________________________________________________________
if __name__=='__main__':
    unittest.main()
    

	
