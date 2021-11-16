# Converts XML back to MKV
# Licence = MIT, 2012, Vitaly "_Vi" Shukela
# the whole parser has been retrieved from: https://github.com/vi/mkvparse
# xml > mkv: cat filename.xml | ./xml2mkv > filename.mkv
# get permission on ubuntu: chmod +x scriptname.extension
import sys
from xml.sax import make_parser, handler
from struct import pack
import binascii

if sys.version < '3':
    reload(sys)
    sys.setdefaultencoding('utf-8')
    maybe_encode=lambda x:x
    range = xrange
    maybe_encode_utf8=lambda x:x
else:
    def maybe_encode(x):
        if type(x) == str:
            return x.encode("ascii")
        else:
            return x
    chr=lambda x:bytes((x,))
    maybe_encode_utf8=lambda x:x.encode("UTF-8")

# More information can be obtained from https://matroska.org/technical/specs/notes.html#Table_Columns
# or more detailed https://github.com/Matroska-Org/ebml-specification/blob/master/specification.markdown
class EBMLTypes:
    VOID     = 0 # used to overwrite damaged data or reserve space within "Master" for later use
    MASTER   = 1 # contains 0, 1, or other EBML elements
    UNSIGNED = 2 # stores positive or 0 integer. Since it is limited to 8 octets then the length is
                 # from 0 to 18,446,744,073,709,551,615
    SIGNED   = 3
    TEXTA    = 4
    TEXTU    = 5
    BINARY   = 6 # declares a length in octets from zero to VINTMAX
    FLOAT    = 7 # stores a floating-point number as defined in [@!IEEE.754.1985]
    DATE     = 8 # stores stores an integer in the same format as SIGNED that expresses a point in time
                 # referenced in nanoseconds from the precise beginning of the third millennium. Provides
                 # expression of time from 1708-09-11T00:12:44.854775808 UTC to 2293-04-11T11:47:16.854775807 UTC
    PROCEED  = 10

table_element_name = {
 	"EBML": (b"\x1A\x45\xDF\xA3", EBMLTypes.MASTER),
	"EBMLVersion": (b"\x42\x86", EBMLTypes.UNSIGNED),
	"EBMLReadVersion": (b"\x42\xF7", EBMLTypes.UNSIGNED),
	"EBMLMaxIDLength": (b"\x42\xF2", EBMLTypes.UNSIGNED),
	"EBMLMaxSizeLength": (b"\x42\xF3", EBMLTypes.UNSIGNED),
	"DocType": (b"\x42\x82", EBMLTypes.TEXTA),
	"DocTypeVersion": (b"\x42\x87", EBMLTypes.UNSIGNED),
	"DocTypeReadVersion": (b"\x42\x85", EBMLTypes.UNSIGNED),
	"Void": (b"\xEC", EBMLTypes.BINARY),
	"CRC-32": (b"\xBF", EBMLTypes.BINARY),
	"SignatureSlot": (b"\x1B\x53\x86\x67", EBMLTypes.MASTER),
	"SignatureAlgo": (b"\x7E\x8A", EBMLTypes.UNSIGNED),
	"SignatureHash": (b"\x7E\x9A", EBMLTypes.UNSIGNED),
	"SignaturePublicKey": (b"\x7E\xA5", EBMLTypes.BINARY),
	"Signature": (b"\x7E\xB5", EBMLTypes.BINARY),
	"SignatureElements": (b"\x7E\x5B", EBMLTypes.MASTER),
	"SignatureElementList": (b"\x7E\x7B", EBMLTypes.MASTER),
	"SignedElement": (b"\x65\x32", EBMLTypes.BINARY),
	"Segment": (b"\x18\x53\x80\x67", EBMLTypes.PROCEED),
	"SeekHead": (b"\x11\x4D\x9B\x74", EBMLTypes.MASTER),
	"Seek": (b"\x4D\xBB", EBMLTypes.MASTER),
	"SeekID": (b"\x53\xAB", EBMLTypes.BINARY),
	"SeekPosition": (b"\x53\xAC", EBMLTypes.UNSIGNED),
	"Info": (b"\x15\x49\xA9\x66", EBMLTypes.MASTER),
	"SegmentUID": (b"\x73\xA4", EBMLTypes.BINARY),
	"SegmentFilename": (b"\x73\x84", EBMLTypes.TEXTU),
	"PrevUID": (b"\x3C\xB9\x23", EBMLTypes.BINARY),
	"PrevFilename": (b"\x3C\x83\xAB", EBMLTypes.TEXTU),
	"NextUID": (b"\x3E\xB9\x23", EBMLTypes.BINARY),
	"NextFilename": (b"\x3E\x83\xBB", EBMLTypes.TEXTU),
	"SegmentFamily": (b"\x44\x44", EBMLTypes.BINARY),
	"ChapterTranslate": (b"\x69\x24", EBMLTypes.MASTER),
	"ChapterTranslateEditionUID": (b"\x69\xFC", EBMLTypes.UNSIGNED),
	"ChapterTranslateCodec": (b"\x69\xBF", EBMLTypes.UNSIGNED),
	"ChapterTranslateID": (b"\x69\xA5", EBMLTypes.BINARY),
	"TimecodeScale": (b"\x2A\xD7\xB1", EBMLTypes.UNSIGNED),
	"Duration": (b"\x44\x89", EBMLTypes.FLOAT),
	"DateUTC": (b"\x44\x61", EBMLTypes.DATE),
	"Title": (b"\x7B\xA9", EBMLTypes.TEXTU),
	"MuxingApp": (b"\x4D\x80", EBMLTypes.TEXTU),
	"WritingApp": (b"\x57\x41", EBMLTypes.TEXTU),
	"Cluster": (b"\x1F\x43\xB6\x75", EBMLTypes.PROCEED),
	"Timecode": (b"\xE7", EBMLTypes.UNSIGNED),
	"SilentTracks": (b"\x58\x54", EBMLTypes.MASTER),
	"SilentTrackNumber": (b"\x58\xD7", EBMLTypes.UNSIGNED),
	"Position": (b"\xA7", EBMLTypes.UNSIGNED),
	"PrevSize": (b"\xAB", EBMLTypes.UNSIGNED),
	"SimpleBlock": (b"\xA3", EBMLTypes.BINARY),
	"BlockGroup": (b"\xA0", EBMLTypes.MASTER),
	"Block": (b"\xA1", EBMLTypes.BINARY),
	"BlockVirtual": (b"\xA2", EBMLTypes.BINARY),
	"BlockAdditions": (b"\x75\xA1", EBMLTypes.MASTER),
	"BlockMore": (b"\xA6", EBMLTypes.MASTER),
	"BlockAddID": (b"\xEE", EBMLTypes.UNSIGNED),
	"BlockAdditional": (b"\xA5", EBMLTypes.BINARY),
	"BlockDuration": (b"\x9B", EBMLTypes.UNSIGNED),
	"ReferencePriority": (b"\xFA", EBMLTypes.UNSIGNED),
	"ReferenceBlock": (b"\xFB", EBMLTypes.SIGNED),
	"ReferenceVirtual": (b"\xFD", EBMLTypes.SIGNED),
	"CodecState": (b"\xA4", EBMLTypes.BINARY),
	"Slices": (b"\x8E", EBMLTypes.MASTER),
	"TimeSlice": (b"\xE8", EBMLTypes.MASTER),
	"LaceNumber": (b"\xCC", EBMLTypes.UNSIGNED),
	"FrameNumber": (b"\xCD", EBMLTypes.UNSIGNED),
	"BlockAdditionID": (b"\xCB", EBMLTypes.UNSIGNED),
	"Delay": (b"\xCE", EBMLTypes.UNSIGNED),
	"SliceDuration": (b"\xCF", EBMLTypes.UNSIGNED),
	"ReferenceFrame": (b"\xC8", EBMLTypes.MASTER),
	"ReferenceOffset": (b"\xC9", EBMLTypes.UNSIGNED),
	"ReferenceTimeCode": (b"\xCA", EBMLTypes.UNSIGNED),
	"EncryptedBlock": (b"\xAF", EBMLTypes.BINARY),
	"Tracks": (b"\x16\x54\xAE\x6B", EBMLTypes.MASTER),
	"TrackEntry": (b"\xAE", EBMLTypes.MASTER),
	"TrackNumber": (b"\xD7", EBMLTypes.UNSIGNED),
	"TrackUID": (b"\x73\xC5", EBMLTypes.UNSIGNED),
	"TrackType": (b"\x83", EBMLTypes.UNSIGNED),
	"FlagEnabled": (b"\xB9", EBMLTypes.UNSIGNED),
	"FlagDefault": (b"\x88", EBMLTypes.UNSIGNED),
	"FlagForced": (b"\x55\xAA", EBMLTypes.UNSIGNED),
	"FlagLacing": (b"\x9C", EBMLTypes.UNSIGNED),
	"MinCache": (b"\x6D\xE7", EBMLTypes.UNSIGNED),
	"MaxCache": (b"\x6D\xF8", EBMLTypes.UNSIGNED),
	"DefaultDuration": (b"\x23\xE3\x83", EBMLTypes.UNSIGNED),
	"TrackTimecodeScale": (b"\x23\x31\x4F", EBMLTypes.FLOAT),
	"TrackOffset": (b"\x53\x7F", EBMLTypes.SIGNED),
	"MaxBlockAdditionID": (b"\x55\xEE", EBMLTypes.UNSIGNED),
	"Name": (b"\x53\x6E", EBMLTypes.TEXTU),
	"Language": (b"\x22\xB5\x9C", EBMLTypes.TEXTA),
	"CodecID": (b"\x86", EBMLTypes.TEXTA),
	"CodecPrivate": (b"\x63\xA2", EBMLTypes.BINARY),
	"CodecName": (b"\x25\x86\x88", EBMLTypes.TEXTU),
	"AttachmentLink": (b"\x74\x46", EBMLTypes.UNSIGNED),
	"CodecSettings": (b"\x3A\x96\x97", EBMLTypes.TEXTU),
	"CodecInfoURL": (b"\x3B\x40\x40", EBMLTypes.TEXTA),
	"CodecDownloadURL": (b"\x26\xB2\x40", EBMLTypes.TEXTA),
	"CodecDecodeAll": (b"\xAA", EBMLTypes.UNSIGNED),
	"TrackOverlay": (b"\x6F\xAB", EBMLTypes.UNSIGNED),
	"TrackTranslate": (b"\x66\x24", EBMLTypes.MASTER),
	"TrackTranslateEditionUID": (b"\x66\xFC", EBMLTypes.UNSIGNED),
	"TrackTranslateCodec": (b"\x66\xBF", EBMLTypes.UNSIGNED),
	"TrackTranslateTrackID": (b"\x66\xA5", EBMLTypes.BINARY),
	"Video": (b"\xE0", EBMLTypes.MASTER),
	"FlagInterlaced": (b"\x9A", EBMLTypes.UNSIGNED),
	"StereoMode": (b"\x53\xB8", EBMLTypes.UNSIGNED),
	"OldStereoMode": (b"\x53\xB9", EBMLTypes.UNSIGNED),
	"PixelWidth": (b"\xB0", EBMLTypes.UNSIGNED),
	"PixelHeight": (b"\xBA", EBMLTypes.UNSIGNED),
	"PixelCropBottom": (b"\x54\xAA", EBMLTypes.UNSIGNED),
	"PixelCropTop": (b"\x54\xBB", EBMLTypes.UNSIGNED),
	"PixelCropLeft": (b"\x54\xCC", EBMLTypes.UNSIGNED),
	"PixelCropRight": (b"\x54\xDD", EBMLTypes.UNSIGNED),
	"DisplayWidth": (b"\x54\xB0", EBMLTypes.UNSIGNED),
	"DisplayHeight": (b"\x54\xBA", EBMLTypes.UNSIGNED),
	"DisplayUnit": (b"\x54\xB2", EBMLTypes.UNSIGNED),
	"AspectRatioType": (b"\x54\xB3", EBMLTypes.UNSIGNED),
	"ColourSpace": (b"\x2E\xB5\x24", EBMLTypes.BINARY),
	"GammaValue": (b"\x2F\xB5\x23", EBMLTypes.FLOAT),
	"FrameRate": (b"\x23\x83\xE3", EBMLTypes.FLOAT),
	"Audio": (b"\xE1", EBMLTypes.MASTER),
	"SamplingFrequency": (b"\xB5", EBMLTypes.FLOAT),
	"OutputSamplingFrequency": (b"\x78\xB5", EBMLTypes.FLOAT),
	"Channels": (b"\x9F", EBMLTypes.UNSIGNED),
	"ChannelPositions": (b"\x7D\x7B", EBMLTypes.BINARY),
	"BitDepth": (b"\x62\x64", EBMLTypes.UNSIGNED),
	"TrackOperation": (b"\xE2", EBMLTypes.MASTER),
	"TrackCombinePlanes": (b"\xE3", EBMLTypes.MASTER),
	"TrackPlane": (b"\xE4", EBMLTypes.MASTER),
	"TrackPlaneUID": (b"\xE5", EBMLTypes.UNSIGNED),
	"TrackPlaneType": (b"\xE6", EBMLTypes.UNSIGNED),
	"TrackJoinBlocks": (b"\xE9", EBMLTypes.MASTER),
	"TrackJoinUID": (b"\xED", EBMLTypes.UNSIGNED),
	"TrickTrackUID": (b"\xC0", EBMLTypes.UNSIGNED),
	"TrickTrackSegmentUID": (b"\xC1", EBMLTypes.BINARY),
	"TrickTrackFlag": (b"\xC6", EBMLTypes.UNSIGNED),
	"TrickMasterTrackUID": (b"\xC7", EBMLTypes.UNSIGNED),
	"TrickMasterTrackSegmentUID": (b"\xC4", EBMLTypes.BINARY),
	"ContentEncodings": (b"\x6D\x80", EBMLTypes.MASTER),
	"ContentEncoding": (b"\x62\x40", EBMLTypes.MASTER),
	"ContentEncodingOrder": (b"\x50\x31", EBMLTypes.UNSIGNED),
	"ContentEncodingScope": (b"\x50\x32", EBMLTypes.UNSIGNED),
	"ContentEncodingType": (b"\x50\x33", EBMLTypes.UNSIGNED),
	"ContentCompression": (b"\x50\x34", EBMLTypes.MASTER),
	"ContentCompAlgo": (b"\x42\x54", EBMLTypes.UNSIGNED),
	"ContentCompSettings": (b"\x42\x55", EBMLTypes.BINARY),
	"ContentEncryption": (b"\x50\x35", EBMLTypes.MASTER),
	"ContentEncAlgo": (b"\x47\xE1", EBMLTypes.UNSIGNED),
	"ContentEncKeyID": (b"\x47\xE2", EBMLTypes.BINARY),
	"ContentSignature": (b"\x47\xE3", EBMLTypes.BINARY),
	"ContentSigKeyID": (b"\x47\xE4", EBMLTypes.BINARY),
	"ContentSigAlgo": (b"\x47\xE5", EBMLTypes.UNSIGNED),
	"ContentSigHashAlgo": (b"\x47\xE6", EBMLTypes.UNSIGNED),
	"Cues": (b"\x1C\x53\xBB\x6B", EBMLTypes.MASTER),
	"CuePoint": (b"\xBB", EBMLTypes.MASTER),
	"CueTime": (b"\xB3", EBMLTypes.UNSIGNED),
	"CueTrackPositions": (b"\xB7", EBMLTypes.MASTER),
	"CueTrack": (b"\xF7", EBMLTypes.UNSIGNED),
	"CueClusterPosition": (b"\xF1", EBMLTypes.UNSIGNED),
	"CueBlockNumber": (b"\x53\x78", EBMLTypes.UNSIGNED),
	"CueCodecState": (b"\xEA", EBMLTypes.UNSIGNED),
	"CueReference": (b"\xDB", EBMLTypes.MASTER),
	"CueRefTime": (b"\x96", EBMLTypes.UNSIGNED),
	"CueRefCluster": (b"\x97", EBMLTypes.UNSIGNED),
	"CueRefNumber": (b"\x53\x5F", EBMLTypes.UNSIGNED),
	"CueRefCodecState": (b"\xEB", EBMLTypes.UNSIGNED),
	"Attachments": (b"\x19\x41\xA4\x69", EBMLTypes.MASTER),
	"AttachedFile": (b"\x61\xA7", EBMLTypes.MASTER),
	"FileDescription": (b"\x46\x7E", EBMLTypes.TEXTU),
	"FileName": (b"\x46\x6E", EBMLTypes.TEXTU),
	"FileMimeType": (b"\x46\x60", EBMLTypes.TEXTA),
	"FileData": (b"\x46\x5C", EBMLTypes.BINARY),
	"FileUID": (b"\x46\xAE", EBMLTypes.UNSIGNED),
	"FileReferral": (b"\x46\x75", EBMLTypes.BINARY),
	"FileUsedStartTime": (b"\x46\x61", EBMLTypes.UNSIGNED),
	"FileUsedEndTime": (b"\x46\x62", EBMLTypes.UNSIGNED),
	"Chapters": (b"\x10\x43\xA7\x70", EBMLTypes.MASTER),
	"EditionEntry": (b"\x45\xB9", EBMLTypes.MASTER),
	"EditionUID": (b"\x45\xBC", EBMLTypes.UNSIGNED),
	"EditionFlagHidden": (b"\x45\xBD", EBMLTypes.UNSIGNED),
	"EditionFlagDefault": (b"\x45\xDB", EBMLTypes.UNSIGNED),
	"EditionFlagOrdered": (b"\x45\xDD", EBMLTypes.UNSIGNED),
	"ChapterAtom": (b"\xB6", EBMLTypes.MASTER),
	"ChapterUID": (b"\x73\xC4", EBMLTypes.UNSIGNED),
	"ChapterTimeStart": (b"\x91", EBMLTypes.UNSIGNED),
	"ChapterTimeEnd": (b"\x92", EBMLTypes.UNSIGNED),
	"ChapterFlagHidden": (b"\x98", EBMLTypes.UNSIGNED),
	"ChapterFlagEnabled": (b"\x45\x98", EBMLTypes.UNSIGNED),
	"ChapterSegmentUID": (b"\x6E\x67", EBMLTypes.BINARY),
	"ChapterSegmentEditionUID": (b"\x6E\xBC", EBMLTypes.UNSIGNED),
	"ChapterPhysicalEquiv": (b"\x63\xC3", EBMLTypes.UNSIGNED),
	"ChapterTrack": (b"\x8F", EBMLTypes.MASTER),
	"ChapterTrackNumber": (b"\x89", EBMLTypes.UNSIGNED),
	"ChapterDisplay": (b"\x80", EBMLTypes.MASTER),
	"ChapString": (b"\x85", EBMLTypes.TEXTU),
	"ChapLanguage": (b"\x43\x7C", EBMLTypes.TEXTA),
	"ChapCountry": (b"\x43\x7E", EBMLTypes.TEXTA),
	"ChapProcess": (b"\x69\x44", EBMLTypes.MASTER),
	"ChapProcessCodecID": (b"\x69\x55", EBMLTypes.UNSIGNED),
	"ChapProcessPrivate": (b"\x45\x0D", EBMLTypes.BINARY),
	"ChapProcessCommand": (b"\x69\x11", EBMLTypes.MASTER),
	"ChapProcessTime": (b"\x69\x22", EBMLTypes.UNSIGNED),
	"ChapProcessData": (b"\x69\x33", EBMLTypes.BINARY),
	"Tags": (b"\x12\x54\xC3\x67", EBMLTypes.MASTER),
	"Tag": (b"\x73\x73", EBMLTypes.MASTER),
	"Targets": (b"\x63\xC0", EBMLTypes.MASTER),
	"TargetTypeValue": (b"\x68\xCA", EBMLTypes.UNSIGNED),
	"TargetType": (b"\x63\xCA", EBMLTypes.TEXTA),
	"TagTrackUID": (b"\x63\xC5", EBMLTypes.UNSIGNED),
	"TagEditionUID": (b"\x63\xC9", EBMLTypes.UNSIGNED),
	"TagChapterUID": (b"\x63\xC4", EBMLTypes.UNSIGNED),
	"TagAttachmentUID": (b"\x63\xC6", EBMLTypes.UNSIGNED),
	"SimpleTag": (b"\x67\xC8", EBMLTypes.MASTER),
	"TagName": (b"\x45\xA3", EBMLTypes.TEXTU),
	"TagLanguage": (b"\x44\x7A", EBMLTypes.TEXTA),
	"TagDefault": (b"\x44\x84", EBMLTypes.UNSIGNED),
	"TagString": (b"\x44\x87", EBMLTypes.TEXTU),
	"TagBinary": (b"\x44\x85", EBMLTypes.BINARY),
	"CodecDelay": (b"\x56\xAA", EBMLTypes.UNSIGNED),
	"SeekPreRoll": (b"\x56\xBB", EBMLTypes.UNSIGNED),
	"CueRelativePosition": (b"\xF0", EBMLTypes.UNSIGNED),
	"AlphaMode": (b"\x53\xC0", EBMLTypes.UNSIGNED),
	"BitsPerChannel": (b"\x55\xB2", EBMLTypes.UNSIGNED),
	"CbSubsamplingHorz": (b"\x55\xB5", EBMLTypes.UNSIGNED),
	"CbSubsamplingVert": (b"\x55\xB6", EBMLTypes.UNSIGNED),
	"ChapterStringUID": (b"\x56\x54", EBMLTypes.TEXTU),
	"ChromaSitingHorz": (b"\x55\xB7", EBMLTypes.UNSIGNED),
	"ChromaSitingVert": (b"\x55\xB8", EBMLTypes.UNSIGNED),
	"ChromaSubsamplingHorz": (b"\x55\xB3", EBMLTypes.UNSIGNED),
	"ChromaSubsamplingVert": (b"\x55\xB4", EBMLTypes.UNSIGNED),
	"Colour": (b"\x55\xB0", EBMLTypes.MASTER),
	"DefaultDecodedFieldDuration": (b"\x23\x4E\x7A", EBMLTypes.UNSIGNED),
	"DiscardPadding": (b"\x75\xA2", EBMLTypes.SIGNED),
	"FieldOrder": (b"\x9D", EBMLTypes.UNSIGNED),
	"LuminanceMax": (b"\x55\xD9", EBMLTypes.FLOAT),
	"LuminanceMin": (b"\x55\xDA", EBMLTypes.FLOAT),
	"MasteringMetadata": (b"\x55\xD0", EBMLTypes.MASTER),
	"MatrixCoefficients": (b"\x55\xB1", EBMLTypes.UNSIGNED),
	"MaxCLL": (b"\x55\xBC", EBMLTypes.UNSIGNED),
	"MaxFALL": (b"\x55\xBD", EBMLTypes.UNSIGNED),
	"Primaries": (b"\x55\xBB", EBMLTypes.UNSIGNED),
	"PrimaryBChromaticityX": (b"\x55\xD5", EBMLTypes.FLOAT),
	"PrimaryBChromaticityY": (b"\x55\xD6", EBMLTypes.FLOAT),
	"PrimaryGChromaticityX": (b"\x55\xD3", EBMLTypes.FLOAT),
	"PrimaryGChromaticityY": (b"\x55\xD4", EBMLTypes.FLOAT),
	"PrimaryRChromaticityX": (b"\x55\xD1", EBMLTypes.FLOAT),
	"PrimaryRChromaticityY": (b"\x55\xD2", EBMLTypes.FLOAT),
	"Range": (b"\x55\xB9", EBMLTypes.UNSIGNED),
	"TransferCharacteristics": (b"\x55\xBA", EBMLTypes.UNSIGNED),
	"WhitePointChromaticityX": (b"\x55\xD7", EBMLTypes.FLOAT),
	"WhitePointChromaticityY": (b"\x55\xD8", EBMLTypes.FLOAT),
}

def get_largest_byte(byte, signed=False):
    if byte < 0:
		x = 0x100
		
		while (byte + x) < (x / 2):
			x <<= 8 # >> means i / 2**1; << means i * 2**1
		
		byte += x
		if byte < 0x100:
			return chr(byte)
		
		signed = False
	  
    elif (byte < 0x100 and not signed) or (byte < 0x80):
		return chr(byte)
	  
    return get_largest_byte(byte >> 8, signed) + chr(byte & 0xFF)
	
def encode_embl(byte):
    def move_bits(rest_of_byte, bits):
        if bits==8:
            return chr(rest_of_byte & 0xFF);
        else:
            return move_bits(rest_of_byte >> 8, bits - 8) + chr(rest_of_byte & 0xFF)

    if byte == -1:
        return chr(0xFF)
    
    if byte < 2**7 - 1:
        return chr(byte | 0x80)
    
    if byte < 2**14 - 1:
        return chr(0x40 | (byte >> 8)) + move_bits(byte, 8)
    
    if byte < 2**21 - 1:
        return chr(0x20 | (byte >> 16)) + move_bits(byte, 16)
    
    if byte < 2**28 - 1:
        return chr(0x10 | (byte >> 24)) + move_bits(byte, 24)
    
    if byte < 2**35 - 1:
        return chr(0x08 | (byte >> 32)) + move_bits(byte, 32)
    
    if byte < 2**42 - 1:
        return chr(0x04 | (byte >> 40)) + move_bits(byte, 40)
    
    if byte < 2**49 - 1:
        return chr(0x02 | (byte >> 48)) + move_bits(byte, 48)
    
    if byte < 2**56 - 1:
        return chr(0x01) + move_bits(byte, 56)
    
    raise Exception("FOUND BYTE IS TOO BIG")

def get_ebml_element(element_id, element_data, element_length = None):
    if element_length == None:
        element_length = len(element_data)
    
	return get_largest_byte(element_id) + encode_embl(element_length) + element_data
	
class ConvertXMLtoMKV(handler.ContentHandler):
    def __init__(self):
        self.stack_table = []
        self.pump_stack = []
        self.timecodeScale = 1000000
        self.check_duration = None
        self.last_block_duration = 0
        self.compress_header = {}
        self.current_track = None
        self.current_compiling_algorithm = None
        self.current_character_character_content_compiling_settings = None
        pass

    def get_duration(self, duration):
        if not self.check_duration:
            self.check_duration = duration
        else:
            if duration != self.check_duration:
                sys.stderr.write("Duration has been ignored due to being edited\n")
                sys.stderr.write("<duration> is meaningful in <block>s that are used in\n")
                sys.stderr.write("\"nocluster\" mode (mkv2xml -C)\n")

    def startElement(self, name, attributes):
        self.element_name = name
        self.element_data= []
        if name == "mkv2xml":
            pass
        
        elif name == "Segment":
            sys.stdout.write(b"\x18\x53\x80\x67"+b"\xFF")
            sys.stdout.write(b"\xEC\x40\x80" + (b"\x00" * 128))
            pass
        
        elif name == "track" or name == "duration" or name == "timecode":
            pass
        
        elif name == "data":
            self.character_content_of_the_frame = False
            if "encoding" in attributes:
                if attributes["encoding"] == "text":
                    self.character_content_of_the_frame = True

        elif name == "discardable":
            self.discardable_frame = True
        
        elif name == "keyframe":
            self.keyframe_frame = True
        
        elif name == "invisible":
            self.invisible_frame = True
        
        else:
            if name in table_element_name:
                (element_id, element_type) = table_element_name[name]
                self.current_element_type = element_type
                self.stack_table.append((name, attributes))
                self.pump_stack.append(b"")

                if "encoding" in attributes:
                    if attributes["encoding"] == "text":
                        self.current_element_type = EBMLTypes.TEXTA
            
            if name == "SimpleBlock" or name == "Block" or name == "block":
                self.discardable_frame = False
                self.invisible_frame = False
                self.keyframe_frame = False
                self.current_pumped_frame = ""
                self.frame_buffering = []
                self.duration_of_the_frame = None
                self.current_element_type = None # prevent usual binary processing
            
            if name == "BlockGroup":
                self.check_duration = None

    def characters(self, character_content):
        self.element_data.append(character_content)

    def characters_old(self, character_content):
        if self.element_name == "data":
            self.current_pumped_frame += character_content    
            return
        
        if not character_content.isspace():
            pump = ""
            if self.element_name == "track":
                self.track_of_the_frame = int(character_content)
                return
            
            elif self.element_name == "timecode":
                self.timecode_of_the_frame = float(character_content)
                return
            
            elif self.element_name == "duration":
                self.duration_of_the_frame = float(character_content)
                return

            elif self.current_element_type == EBMLTypes.TEXTA:
                pump = str(character_content).encode("ascii")
            
            elif self.current_element_type == EBMLTypes.TEXTU:
                pump = str(character_content).encode("UTF-8")
            
            elif self.current_element_type == EBMLTypes.UNSIGNED:
                pump = get_largest_byte(int(character_content))
                if self.element_name == "TimecodeScale":
                    self.timecodeScale = int(character_content)
                
                elif self.element_name == "Timecode":
                    self.last_cluster = int(character_content)
                
                elif self.element_name == "BlockDuration":
                    self.get_duration(int(character_content))
            
            elif self.current_element_type == EBMLTypes.SIGNED:
                pump = get_largest_byte(int(character_content), True)
            
            elif self.current_element_type == EBMLTypes.BINARY:
                character_content = character_content.replace("\n","").replace("\r","").replace(" ","");
                pump = binascii.unhexlify(maybe_encode(character_content))
                pass
            
            elif self.current_element_type == EBMLTypes.DATE:
                actual_duration = float(character_content)
                actual_duration -= 978300000
                actual_duration *= 1000000000.0;
                pump = get_largest_byte(int(actual_duration), True)
            
            elif self.current_element_type == EBMLTypes.FLOAT:
                pump = pack(">d", float(character_content))


            self.pump_stack[-1]+=pump


    def endElement(self, name):
        character_content = "".join(self.element_data)
        if character_content: 
            self.characters_old(character_content)
            self.element_data=[]

        if name == "track" or name == "timecode" or name == "discardable" or name == "keyframe" or \
             name == "invisible" or name == "duration": 
            return
        
        elif name == "data":
            if self.character_content_of_the_frame:
                self.frame_buffering.append(maybe_encode_utf8(str(self.current_pumped_frame)))
            else:
                text = self.current_pumped_frame.replace("\n", "").replace("\t", "").replace(" ", "")
                self.frame_buffering.append(binascii.unhexlify(maybe_encode(text)))
            self.current_pumped_frame=""
            return

        if name != "block":
            if not name in table_element_name:
                if not name == "mkv2xml":
                    sys.stderr.write("Element is not known %s\n"%name)
                return

        if name=="TrackEntry":
            if self.current_compiling_algorithm == 3:
                self.compress_header[self.current_track] = binascii.unhexlify(maybe_encode(self.current_character_character_content_compiling_settings))
                self.current_character_character_content_compiling_settings = None
                self.current_compiling_algorithm = None
                sys.stderr.write("Using header compression for track "+str(self.current_track)+"\n");
        
        if name=="TrackNumber":
            self.current_track = int(character_content)
        
        if name=="ContentCompAlgo":
            self.current_compiling_algorithm = int(character_content)
        
        if name=="ContentCompSettings":
            self.current_character_character_content_compiling_settings = character_content

        if name=="Segment":
            return

        (element_id, element_type) = (None, None)
        if name != "block":
            (element_id, element_type) = table_element_name[name];

        if (name == "SimpleBlock") or (name == "Block") or (name == "block"):
            exact_timecode = int(self.timecode_of_the_frame * 1000000000 / self.timecodeScale)
            similar_timecode = 0
            if name != "block":
                similar_timecode = exact_timecode - self.last_cluster
                if self.duration_of_the_frame:
                    scale_down_the_duration = int(self.duration_of_the_frame * 1000000000 / self.timecodeScale)
                    self.get_duration(scale_down_the_duration)
            
            if (similar_timecode < -0x8000) or (similar_timecode > 0x7FFF):
                sys.stderr.write("Block timecode is too far from outer Cluster's timecode\n")
                sys.stderr.write("Use no-cluster mode (mkv2xml -C) with <block> elements\n")
                similar_timecode = 0;
            
            if similar_timecode < 0:
                similar_timecode+=0x10000
            
            flags = 0x00
            if self.keyframe_frame:
            	 flags |= 0x80
            
            if self.discardable_frame:
            	 flags |= 0x01
            
            if self.invisible_frame:
            	 flags |= 0x08
            
            length_of_the_XIPH=[]
            character_content = b""
            
            header = None
            if self.track_of_the_frame in self.compress_header:
                header = self.compress_header[self.track_of_the_frame]
            
            for j in self.frame_buffering:
                if header is not None:
                    if j[0:len(header)] != header:
                        sys.stderr.write("Unable to apply header compression here\n")
                    else:
                        j=j[len(header):]
                
                character_content += j
                length_of_the_XIPH.append(len(j))
            
            laced_XIPH=b""
            laced_XIPH_count = len(length_of_the_XIPH)-1
            for j in range(0,laced_XIPH_count):
                length = length_of_the_XIPH[j]
                while length >= 255:
                    laced_XIPH += b"\xFF"
                    length -= 255
                laced_XIPH += chr(length)

            current_frame = None

            if len(length_of_the_XIPH) <= 1:
                current_frame =  encode_embl(self.track_of_the_frame) + \
                         chr(similar_timecode >> 8) + chr(similar_timecode & 0xFF) + chr(flags) + character_content
            else:
                flags |= 0x02 # Xiph lacing
                current_frame =  encode_embl(self.track_of_the_frame) + chr(similar_timecode >> 8) + chr(similar_timecode & 0xFF) + \
                         chr(flags) + chr(laced_XIPH_count) + laced_XIPH + character_content

            if name == "block":
                if not self.duration_of_the_frame:
                	  # Cluster + Timecode + simpleblock
                    cluster =  get_ebml_element(0x1F43B675, b"" + get_ebml_element(0xE7, get_largest_byte(exact_timecode)) + get_ebml_element(0xA3, current_frame))
                else:
                    scale_down_the_duration = int(self.duration_of_the_frame * 1000000000 / self.timecodeScale)
                    # Cluster + Timecode + BlockGroup + Block Duration + Block
                    cluster =  get_ebml_element(0x1F43B675, b"" + get_ebml_element(0xE7, get_largest_byte(exact_timecode)) 
                    										+ get_ebml_element(0xA0, b"" + get_ebml_element(0x9B, get_largest_byte(scale_down_the_duration)) + get_ebml_element(0xA1, current_frame)))
                sys.stdout.write(cluster)
                return
            else:
                self.pump_stack[-1] = current_frame

        if not len(self.stack_table):
            return

        (_, attributes) = self.stack_table.pop()
        pump = self.pump_stack.pop()

        if name == "WritingApp" or name == "MuxingApp":
            if pump.find(b"xml2mkv") == -1:
                pump+=b"; xml2mkv"
        
        if len(self.pump_stack):
            self.pump_stack[-1] +=  element_id + encode_embl(len(pump)) + pump
        else:
            sys.stdout.write(element_id)
            sys.stdout.write(encode_embl(len(pump)))
            sys.stdout.write(pump)
            pass


if sys.version >= '3':
    sys.stdout = sys.stdout.detach()
            
parser = make_parser()
parser.setContentHandler(ConvertXMLtoMKV())
parser.parse(sys.stdin)