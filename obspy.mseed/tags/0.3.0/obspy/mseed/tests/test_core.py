# -*- coding: utf-8 -*-

from obspy.core import UTCDateTime, Stream, Trace, read
from obspy.core.util import NamedTemporaryFile
from obspy.mseed import LibMSEED
from obspy.mseed.core import readMSEED
from obspy.mseed.headers import ENCODINGS
from obspy.mseed.libmseed import MSStruct
import inspect
import numpy as np
import os
import platform
import unittest


class CoreTestCase(unittest.TestCase):
    """
    """
    def setUp(self):
        # Directory where the test files are located
        self.path = os.path.dirname(inspect.getsourcefile(self.__class__))

    def tearDown(self):
        pass

    def test_readFileViaLibMSEED(self):
        """
        Read file test via L{obspy.mseed.core.readMSEED}.
        """
        testfile = os.path.join(self.path, 'data', 'test.mseed')
        testdata = [2787, 2776, 2774, 2780, 2783]
        # read
        stream = readMSEED(testfile)
        stream.verify()
        self.assertEqual(stream[0].stats.network, 'NL')
        self.assertEqual(stream[0].stats['station'], 'HGN')
        self.assertEqual(stream[0].stats.get('location'), '00')
        self.assertEqual(stream[0].stats.npts, 11947)
        self.assertEqual(stream[0].stats['sampling_rate'], 40.0)
        self.assertEqual(stream[0].stats.get('channel'), 'BHZ')
        for _i in xrange(5):
            self.assertEqual(stream[0].data[_i], testdata[_i])

    def test_readFileViaObsPy(self):
        """
        Read file test via L{obspy.core.Stream}.
        """
        testfile = os.path.join(self.path, 'data', 'test.mseed')
        testdata = [2787, 2776, 2774, 2780, 2783]
        # without given format -> auto detect file format
        stream = read(testfile)
        stream.verify()
        self.assertEqual(stream[0].stats.network, 'NL')
        self.assertEqual(stream[0].stats['station'], 'HGN')
        self.assertEqual(stream[0].stats.npts, 11947)
        for _i in xrange(5):
            self.assertEqual(stream[0].data[_i], testdata[_i])
        # with given format
        stream = read(testfile, format='MSEED')
        stream.verify()
        self.assertEqual(stream[0].stats.get('location'), '00')
        self.assertEqual(stream[0].stats.get('channel'), 'BHZ')
        self.assertEqual(stream[0].stats['sampling_rate'], 40.0)
        for _i in xrange(5):
            self.assertEqual(stream[0].data[_i], testdata[_i])
        # file with gaps
        gapfile = os.path.join(self.path, 'data', 'gaps.mseed')
        # without given format -> autodetect using extension
        stream = read(gapfile)
        stream.verify()
        self.assertEqual(4, len(stream.traces))
        for _i in stream.traces:
            self.assertEqual(True, isinstance(_i, Trace))

    def test_readHeadFileViaObsPy(self):
        """
        Read file test via L{obspy.core.Stream}.
        """
        testfile = os.path.join(self.path, 'data', 'test.mseed')
        stream = read(testfile, headonly=True, format='MSEED')
        self.assertEqual(stream[0].stats.network, 'NL')
        self.assertEqual(stream[0].stats['station'], 'HGN')
        self.assertEqual(str(stream[0].data), '[]')
        self.assertEqual(stream[0].stats.npts, 11947)
        #
        gapfile = os.path.join(self.path, 'data', 'gaps.mseed')
        # without given format -> autodetect using extension
        stream = read(gapfile, headonly=True)
        self.assertEqual(4, len(stream.traces))
        for _i in stream.traces:
            self.assertEqual(True, isinstance(_i, Trace))
            self.assertEqual(str(_i.data), '[]')

    def test_writeIntegersViaObsPy(self):
        """
        Write integer array via L{obspy.core.Stream}.
        """
        tempfile = NamedTemporaryFile().name
        npts = 1000
        # data array of integers - float won't work!
        np.random.seed(815) # make test reproducable
        data = np.random.randint(-1000, 1000, npts).astype('int32')
        st = Stream([Trace(data=data)])
        # write
        st.write(tempfile, format="MSEED")
        # read again
        stream = read(tempfile)
        os.remove(tempfile)
        stream.verify()
        self.assertEquals(stream[0].data.tolist(), data.tolist())

    def test_readWithWildCard(self):
        """
        Reads wildcard filenames.
        """
        files = os.path.join(self.path, 'data',
                             'BW.BGLD.__.EHE.D.2008.001.*_record')
        st = read(files)
        self.assertEquals(len(st), 3)
        st.merge()
        self.assertEquals(len(st), 1)

    def test_readFullSEED(self):
        """
        Reads a full SEED volume.
        """
        files = os.path.join(self.path, 'data', 'ArclinkRequest_340397.fseed')
        st = read(files)
        self.assertEquals(len(st), 3)
        self.assertEquals(len(st[0]), 602)
        self.assertEquals(len(st[1]), 623)
        self.assertEquals(len(st[2]), 610)

    def test_Header(self):
        """
        Tests whether the header is correctly written and read.
        """
        tempfile = NamedTemporaryFile().name
        np.random.seed(815) # make test reproducable
        data = np.random.randint(-1000, 1000, 50).astype('int32')
        stats = {'network': 'BW', 'station': 'TEST', 'location':'A',
                 'channel': 'EHE', 'npts': len(data), 'sampling_rate': 200.0,
                 'mseed' : {'dataquality' : 'D'}}
        stats['starttime'] = UTCDateTime(2000, 1, 1)
        st = Stream([Trace(data=data, header=stats)])
        # Write it.
        st.write(tempfile, format="MSEED")
        # Read it again and delete the temporary file.
        stream = read(tempfile)
        os.remove(tempfile)
        stream.verify()
        # Loop over the attributes to be able to assert them because a
        # dictionary is not a stats dictionary.
        # This also assures that there are no additional keys.
        for key in stats.keys():
            self.assertEqual(stats[key], stream[0].stats[key])
        # Test the dataquality key extra.
        self.assertEqual(stream[0].stats.mseed.dataquality, 'D')

    def test_writeAndReadDifferentRecordLengths(self):
        """
        Tests Mini-SEED writing and record lengths.
        """
        # libmseed instance.
        mseed = LibMSEED()
        npts = 6000
        np.random.seed(815) # make test reproducable
        data = np.random.randint(-1000, 1000, npts).astype('int32')
        st = Stream([Trace(data=data)])
        record_lengths = [256, 512, 1024, 2048, 4096, 8192]
        # Loop over some record lengths.
        for rec_len in record_lengths:
            # Write it.
            tempfile = NamedTemporaryFile().name
            st.write(tempfile, format="MSEED", reclen=rec_len)
            # Open the file.
            file = open(tempfile, 'rb')
            info = mseed._getMSFileInfo(file, tempfile)
            file.close()
            # Test reading the two files.
            temp_st = read(tempfile)
            np.testing.assert_array_equal(data, temp_st[0].data)
            del temp_st
            os.remove(tempfile)
            # Check record length.
            self.assertEqual(info['record_length'], rec_len)
            # Check if filesize is a multiple of the record length.
            self.assertEqual(info['filesize'] % rec_len, 0)

    def test_invalidRecordLength(self):
        """
        An invalid record length should raise an exception.
        """
        npts = 6000
        tempfile = NamedTemporaryFile().name
        np.random.seed(815) # make test reproducable
        data = np.random.randint(-1000, 1000, npts).astype('int32')
        st = Stream([Trace(data=data)])
        # Writing should fail with invalid record lengths.
        # Not a power of 2.
        self.assertRaises(ValueError, st.write, tempfile, format="MSEED",
                          reclen=1000)
        # Too small.
        self.assertRaises(ValueError, st.write, tempfile, format="MSEED",
                          reclen=8)
        # Not a number.
        self.assertRaises(ValueError, st.write, tempfile, format="MSEED",
                          reclen='A')
        os.remove(tempfile)

    def test_writeAndReadDifferentEncodings(self):
        """
        Writes and read a file with different encoding via the obspy.core
        methods.
        """
        # libmseed instance.
        npts = 1000
        np.random.seed(815) # make test reproducable
        data = np.random.randn(npts).astype('float64') * 1e3 + .5
        st = Stream([Trace(data=data)])
        # Loop over some record lengths.
        for encoding, value in ENCODINGS.iteritems():
            seed_dtype = value[2]
            tempfile = NamedTemporaryFile().name
            # Write it once with the encoding key and once with the value.
            st[0].data = data.astype(seed_dtype)
            st.verify()
            st.write(tempfile, format="MSEED", encoding=encoding)
            temp_st1 = read(tempfile)
            np.testing.assert_array_equal(st[0].data, temp_st1[0].data)
            del temp_st1
            ms = MSStruct(tempfile)
            ms.read(-1, 1, 1, 0)
            self.assertEqual(ms.msr.contents.encoding, encoding)
            del ms # for valgrind
            os.remove(tempfile)

    def test_invalidEncoding(self):
        """
        An invalid encoding should raise an exception.
        """
        npts = 6000
        tempfile = NamedTemporaryFile().name
        np.random.seed(815) # make test reproducable
        data = np.random.randint(-1000, 1000, npts).astype('int32')
        st = Stream([Trace(data=data)])
        # Writing should fail with invalid record lengths.
        # Wrong number.
        self.assertRaises(ValueError, st.write, tempfile, format="MSEED",
                          encoding=2)
        # Wrong Text.
        self.assertRaises(ValueError, st.write, tempfile, format="MSEED",
                          encoding='FLOAT_64')
        os.remove(tempfile)

    def test_readPartsOfFile(self):
        """
        Test reading only parts of an Mini-SEED file without unpacking or
        touching the rest.
        """
        temp = os.path.join(self.path, 'data', 'BW.BGLD.__.EHE.D.2008.001')
        file = temp + '.first_10_percent'
        t = [UTCDateTime(2008, 1, 1, 0, 0, 1, 975000),
             UTCDateTime(2008, 1, 1, 0, 0, 4, 30000)]
        tr1 = read(file, starttime=t[0], endtime=t[1])[0]
        self.assertEqual(t[0], tr1.stats.starttime)
        self.assertEqual(t[1], tr1.stats.endtime)
        # initialize second record
        file2 = temp + '.second_record'
        tr2 = read(file2)[0]
        np.testing.assert_array_equal(tr1.data, tr2.data)

    def test_readWithGSE2Option(self):
        """
        Test that reading will still work if wrong option (of gse2)
        verify_chksum is given. This is important if the read method is
        called for an unknown file format.
        """
        file = os.path.join(self.path, 'data', 'BW.BGLD.__.EHE.D.2008.001'
                            '.second_record')
        tr = read(file, verify_chksum=True, starttime=None)[0]
        data = np.array([-397, -387, -368, -381, -388])
        np.testing.assert_array_equal(tr.data[0:5], data)
        self.assertEqual(412, len(tr.data))
        data = np.array([-406, -417, -403, -423, -413])
        np.testing.assert_array_equal(tr.data[-5:], data)

    def test_allDataTypesAndEndiansInMultipleFiles(self):
        """
        Tests writing all different types. This is an test which is independent of
        the read method. Only the data part is verified.
        """
        file = os.path.join(self.path, "data", \
                            "BW.BGLD.__.EHE.D.2008.001.first_record")
        tempfile = NamedTemporaryFile().name
        # Read the data and copy them
        st = read(file)
        data_copy = st[0].data.copy()
        # Float64, Float32, Int32, Int24, Int16, Char
        encodings = {5: "f8", 4: "f4", 3: "i4", 0: "S1", 1: "i2"}
        byteorders = {0:'<', 1:'>'}
        for byteorder, btype in byteorders.iteritems():
            for encoding, dtype in encodings.iteritems():
                # Convert data to floats and write them again
                st[0].data = data_copy.astype(dtype)
                st.write(tempfile, format="MSEED", encoding=encoding,
                         reclen=256, byteorder=byteorder)
                # Read the first record of data without header not using ObsPy
                s = open(tempfile, "rb").read()
                data = np.fromstring(s[56:256], dtype=btype + dtype)
                np.testing.assert_array_equal(data, st[0].data[:len(data)])
                # Read the binary chunk of data with ObsPy
                st2 = read(tempfile)
                np.testing.assert_array_equal(st2[0].data, st[0].data)
        os.remove(tempfile)

    def test_invalidDataType(self):
        """
        Writing data of type int64 and int16 are not supported.
        """
        npts = 6000
        tempfile = NamedTemporaryFile().name
        np.random.seed(815) # make test reproducable
        # int64
        data = np.random.randint(-1000, 1000, npts).astype('int64')
        st = Stream([Trace(data=data)])
        self.assertRaises(Exception, st.write, tempfile, format="MSEED")
        # int8
        data = np.random.randint(-1000, 1000, npts).astype('int8')
        st = Stream([Trace(data=data)])
        self.assertRaises(Exception, st.write, tempfile, format="MSEED")
        os.remove(tempfile)

    def test_SavingSmallASCII(self):
        """
        Tests writing small ASCII strings.
        """
        tempfile = NamedTemporaryFile().name
        st = Stream()
        st.append(Trace(data=np.fromstring("A" * 8, "|S1")))
        st.write(tempfile, format="MSEED")
        os.remove(tempfile)

    def test_allDataTypesAndEndiansInSingleFile(self):
        """
        Tests all data and endian types into a single file.
        """
        tempfile = NamedTemporaryFile().name
        st1 = Stream()
        data = np.random.randint(-1000, 1000, 500)
        for dtype in ["i2", "i4", "f4", "f8", "S1"]:
            for enc in ["<", ">", "="]:
                st1.append(Trace(data=data.astype(np.dtype(enc + dtype))))
        st1.write(tempfile, format="MSEED")
        # read everything back (int16 gets converted into int32)
        st2 = read(tempfile)
        for dtype in ["i4", "i4", "f4", "f8", "S1"]:
            for enc in ["<", ">", "="]:
                tr = st2.pop(0).data
                self.assertEqual(tr.dtype.kind + str(tr.dtype.itemsize), dtype)
                # byte order is always native (=)
                np.testing.assert_array_equal(tr, data.astype("=" + dtype))
        os.remove(tempfile)

    def test_writeWrongEncoding(self):
        """
        Tests to write a floating point mseed file with incoding STEIM1.
        An exception should be raised.
        """
        file = os.path.join(self.path, "data", \
                            "BW.BGLD.__.EHE.D.2008.001.first_record")
        tempfile = NamedTemporaryFile().name
        # Read the data and convert them to float
        st = read(file)
        st[0].data = st[0].data.astype('float32') + .5
        # Type is not consistent float32 cannot be compressed with STEIM1,
        # therefor an exception must be raised.
        self.assertRaises(Exception, st.write, tempfile, format="MSEED",
                          encoding=10, reclen=256, byteorder=0)
        os.remove(tempfile)

    def test_filesFromLibmseed(self):
        """
        Tests reading of files that are created by libmseed.

        This test also checks the files created by libmseed to some extend.
        """
        path = os.path.join(self.path, "data", "libmseed")
        # Dictionary. The key is the filename, the value a tuple: dtype,
        # sampletype, encoding, content
        def_content = np.arange(1, 51, dtype='int32')
        files = {
            os.path.join(path, "smallASCII.mseed") : ('|S1', 'a', 0,
                        np.fromstring('ABCDEFGH', dtype='|S1')),
            # Tests all ASCII letters.
            os.path.join(path, "fullASCII.mseed") : ('|S1', 'a', 0,
               np.fromstring(
               """ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUV""" + \
               """WXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~""", dtype='|S1')),
            # XXX: int16 array will also be returned as int32.
            os.path.join(path, "int16_INT16.mseed") : ('int32', 'i', 1,
                                                    def_content.astype('int16')),
            os.path.join(path, "int32_INT32.mseed") : ('int32', 'i', 3,
                                                    def_content),
            os.path.join(path, "int32_Steim1.mseed") : ('int32', 'i', 10,
                                                    def_content),
            os.path.join(path, "int32_Steim2.mseed") : ('int32', 'i', 11,
                                                    def_content),
            os.path.join(path, "float32_Float32.mseed") : ('float32', 'f', 4,
                                                def_content.astype('float32')),
            os.path.join(path, "float64_Float64.mseed") : ('float64', 'd', 5,
                                                def_content.astype('float64'))
        }
        # Loop over all files and read them.
        for file in files.keys():
            # Check little and big Endian for each file.
            for _i in ('littleEndian', 'bigEndian'):
                cur_file = file[:-6] + '_' + _i + '.mseed'
                st = read(os.path.join(cur_file))
                # Check the array. 
                np.testing.assert_array_equal(st[0].data, files[file][3])
                # Check the dtype.
                self.assertEqual(st[0].data.dtype, files[file][0])
                # Check byteorder. Should always be native byteorder. Byteorder
                # does not apply to ASCII arrays.
                if 'ASCII' in cur_file:
                    self.assertEqual(st[0].data.dtype.byteorder, '|')
                else:
                    self.assertEqual(st[0].data.dtype.byteorder, '=')
                del st
                # Read just the first record to check encoding. The sampletype
                # should follow from the encoding. But libmseed seems not to
                # read the sampletype when reading a file.
                ms = MSStruct(cur_file, filepointer=False)
                ms.read(-1, 0, 1, 0)
                # Check values.
                self.assertEqual(getattr(ms.msr.contents, 'encoding'),
                                 files[file][2])
                if _i == 'littleEndian':
                    self.assertEqual(getattr(ms.msr.contents, 'byteorder'), 0)
                else:
                    self.assertEqual(getattr(ms.msr.contents, 'byteorder'), 1)
                # Deallocate for debugging with valrgind
                del ms

    def test_wrongRecordLengthAsArgument(self):
        """
        Specifying a wrong record length should raise an error.
        """
        # XXX: The test does not work under windows because libmseed does not
        # seem to handle the record length attribute correctly.
        if not platform.system() == "Windows":
            file = os.path.join(self.path, 'data', 'libmseed',
                                'float32_Float32_bigEndian.mseed')
            self.assertRaises(Exception, read, file, reclen=4096)


def suite():
    return unittest.makeSuite(CoreTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')