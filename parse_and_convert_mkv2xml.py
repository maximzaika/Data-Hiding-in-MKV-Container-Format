# mkv > xml:  cat filename.mkv | python filename > filename.xml
# the whole parser has been retrieved from: https://github.com/vi/mkvparse
# videos for testing retrieved from: http://www.sample-videos.com/index.php#sample-mkv-video
# Licence = MIT, 2012, Vitaly "_Vi" Shukela
# get permission on ubuntu: chmod +x scriptname.extension

'''
* import traceback:
- provides a standard interface to extract,
  format and print stack tracer. Prints stack
  traces under program control, such as in a
  "wrapper" around the interpreter.

* from struct import unpack:
- used in handling binary data stored in files
  or from network connections, among other
  sources. Uses Format String as compact
  descriptions of the layout of the C structs
  and the intended conversion to/from Python values.
- unpacks the string (packed by pack(fmt, ...)).

* import sys:
- provides access to some variables used or maintained
  by the interpreter and to functions that interact
  strongly with the interpreter. It is always available.

* import datetime"
- supplises classes for manipulating dates and times in
  both simple and complex ways.

* import binascii:
- contains a number of methods to convert between binary
  and various ASCII-encoded binary representations.
'''

import traceback
from struct import unpack
import sys
import datetime
import re
import binascii
from os import getenv
from xml.sax import saxutils

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

'''Signed (int) and Unsigned (uint) integers are stored in a big endian byte order, with leading 0x00
   (for positive) and 0xFF (for negative) being cut off. Cannot be larger than 8 bytes.'''
table_element_name = { # the EBML ID gets converted into hexadecimal to identify the location
                 # https://matroska.org/technical/specs/index.html
                                 # EBML HEADER
                0x1A45DFA3: (EBMLTypes.MASTER,        "EBML"), #1A 45 DF A3
                0x4286:     (EBMLTypes.UNSIGNED,      "EBMLVersion"), #42 86
                0x42F7:     (EBMLTypes.UNSIGNED,      "EBMLReadVersion"), #42 F7
                0x42F2:     (EBMLTypes.UNSIGNED,      "EBMLMaxIDLength"), #42 F2
                0x42F3:     (EBMLTypes.UNSIGNED,      "EBMLMaxSizeLength"), #42 F3
                0x4282:     (EBMLTypes.TEXTA,         "DocType"), #42 82
                0x4287:     (EBMLTypes.UNSIGNED,      "DocTypeVersion"), #42 87
                0x4285:     (EBMLTypes.UNSIGNED,      "DocTypeReadVersion"),#42 85
                                 # GLOBAL ELEMENTS
                0xEC:       (EBMLTypes.BINARY,        "Void"), #EC
                0xBF:       (EBMLTypes.BINARY,        "CRC-32"), #BF
                0x1B538667: (EBMLTypes.MASTER,        "SignatureSlot"), #1B 53 86 67
                0x7E8A:     (EBMLTypes.UNSIGNED,      "SignatureAlgo"), #7E 8A
                0x7E9A:     (EBMLTypes.UNSIGNED,      "SignatureHash"), #7E 9A
                0x7EA5:     (EBMLTypes.BINARY,        "SignaturePublicKey"), #7E A5
                0x7EB5:     (EBMLTypes.BINARY,        "Signature"), #7E B5
                0x7E5B:     (EBMLTypes.MASTER,        "SignatureElements"), #7E 5B
                0x7E7B:     (EBMLTypes.MASTER,        "SignatureElementList"), #7E 7B
                0x6532:     (EBMLTypes.BINARY,        "SignedElement"), #65 32
                                 # SEGMENT
                0x18538067: (EBMLTypes.PROCEED,    "Segment"), #11 4D 9B 74
                                 # META SEEK INFORMATION
                0x114D9B74: (EBMLTypes.MASTER,        "SeekHead"), #11 4D 9B 74
                0x4DBB:     (EBMLTypes.MASTER,        "Seek"), #4D BB
                0x53AB:     (EBMLTypes.BINARY,        "SeekID"), #53 AB
                0x53AC:     (EBMLTypes.UNSIGNED,      "SeekPosition"), #53 AC
                                 # SEGMENT INFORMATION              
                0x1549A966: (EBMLTypes.MASTER,        "Info"), #15 48 A9 66
                0x73A4:     (EBMLTypes.BINARY,        "SegmentUID"), #73 A4
                0x7384:     (EBMLTypes.TEXTU,         "SegmentFilename"), #73 84
                0x3CB923:   (EBMLTypes.BINARY,        "PrevUID"), #3C B9 23
                0x3C83AB:   (EBMLTypes.TEXTU,         "PrevFilename"), #3C 83 AB
                0x3EB923:   (EBMLTypes.BINARY,        "NextUID"), #3E B9 23
                0x3E83BB:   (EBMLTypes.TEXTU,         "NextFilename"), #3E 83 BB
                0x4444:     (EBMLTypes.BINARY,        "SegmentFamily"), #44 44
                0x6924:     (EBMLTypes.MASTER,        "ChapterTranslate"), #69 24
                0x69FC:     (EBMLTypes.UNSIGNED,      "ChapterTranslateEditionUID"), #69 FC
                0x69BF:     (EBMLTypes.UNSIGNED,      "ChapterTranslateCodec"), #69 BF
                0x69A5:     (EBMLTypes.BINARY,        "ChapterTranslateID"), #69 A5
                0x2AD7B1:   (EBMLTypes.UNSIGNED,      "TimecodeScale"), #2A D7 B1
                0x4489:     (EBMLTypes.FLOAT,         "Duration"), #44 89
                0x4461:     (EBMLTypes.DATE,          "DateUTC"), #44 61
                0x7BA9:     (EBMLTypes.TEXTU,         "Title"), #7B A9
                0x4D80:     (EBMLTypes.TEXTU,         "MuxingApp"), #4D 80
                0x5741:     (EBMLTypes.TEXTU,         "WritingApp"), #57 41
                                 # CLUSTER              
                0x1F43B675: (EBMLTypes.PROCEED,    "Cluster"), #1F 43 B6 75
                0xE7:       (EBMLTypes.UNSIGNED,      "Timecode"), #E7
                0x5854:     (EBMLTypes.MASTER,        "SilentTracks"), #58 54
                0x58D7:     (EBMLTypes.UNSIGNED,      "SilentTrackNumber"), #58 D7
                0xA7:       (EBMLTypes.UNSIGNED,      "Position"), #A7
                0xAB:       (EBMLTypes.UNSIGNED,      "PrevSize"), #AB
                0xA3:       (EBMLTypes.BINARY,        "SimpleBlock"), #A3
                0xA0:       (EBMLTypes.MASTER,        "BlockGroup"), #A0
                0xA1:       (EBMLTypes.BINARY,        "Block"), #A1
                0xA2:       (EBMLTypes.BINARY,        "BlockVirtual"), #A2
                0x75A1:     (EBMLTypes.MASTER,        "BlockAdditions"), #75 A1
                0xA6:       (EBMLTypes.MASTER,        "BlockMore"), #A6
                0xEE:       (EBMLTypes.UNSIGNED,      "BlockAddID"), #EE
                0xA5:       (EBMLTypes.BINARY,        "BlockAdditional"), #A5
                0x9B:       (EBMLTypes.UNSIGNED,      "BlockDuration"), #9B 
                0xFA:       (EBMLTypes.UNSIGNED,      "ReferencePriority"), #FA
                0xFB:       (EBMLTypes.SIGNED,        "ReferenceBlock"), #FB
                0xFD:       (EBMLTypes.SIGNED,        "ReferenceVirtual"), #FD
                0xA4:       (EBMLTypes.BINARY,        "CodecState"), #A4
                0x75A2:     (EBMLTypes.SIGNED,        "DiscardPadding"), #75 A2
                0x8E:       (EBMLTypes.MASTER,        "Slices"), #8E
                0xE8:       (EBMLTypes.MASTER,        "TimeSlice"), #E8
                0xCC:       (EBMLTypes.UNSIGNED,      "LaceNumber"), #CC
                0xCD:       (EBMLTypes.UNSIGNED,      "FrameNumber"), #CD
                0xCB:       (EBMLTypes.UNSIGNED,      "BlockAdditionID"), #CB
                0xCE:       (EBMLTypes.UNSIGNED,      "Delay"), #CE
                0xCF:       (EBMLTypes.UNSIGNED,      "SliceDuration"), #CF
                0xC8:       (EBMLTypes.MASTER,        "ReferenceFrame"), #C8
                0xC9:       (EBMLTypes.UNSIGNED,      "ReferenceOffset"), #C9
                0xCA:       (EBMLTypes.UNSIGNED,      "ReferenceTimeCode"), #CA
                0xAF:       (EBMLTypes.BINARY,        "EncryptedBlock"), #AF
                                 # TRACK             
                0x1654AE6B: (EBMLTypes.MASTER,        "Tracks"), #16 54 AE 6B
                0xAE:       (EBMLTypes.MASTER,        "TrackEntry"), #AE
                0xD7:       (EBMLTypes.UNSIGNED,      "TrackNumber"), #D7
                0x73C5:     (EBMLTypes.UNSIGNED,      "TrackUID"), #73 C5
                0x83:       (EBMLTypes.UNSIGNED,      "TrackType"), #83 
                0xB9:       (EBMLTypes.UNSIGNED,      "FlagEnabled"),#B9
                0x88:       (EBMLTypes.UNSIGNED,      "FlagDefault"),#88
                0x55AA:     (EBMLTypes.UNSIGNED,      "FlagForced"),#55 AA
                0x9C:       (EBMLTypes.UNSIGNED,      "FlagLacing"),#9C
                0x6DE7:     (EBMLTypes.UNSIGNED,      "MinCache"),#6D E7
                0x6DF8:     (EBMLTypes.UNSIGNED,      "MaxCache"),#6D F8
                0x23E383:   (EBMLTypes.UNSIGNED,      "DefaultDuration"), #23 E3 83
                0x234E7A:   (EBMLTypes.UNSIGNED,      "DefaultDecodedFieldDuration"), #23 4E 7A
                0x23314F:   (EBMLTypes.FLOAT,         "TrackTimecodeScale"), #23 4E 7A
                0x537F:     (EBMLTypes.SIGNED,        "TrackOffset"), #53 7F
                0x55EE:     (EBMLTypes.UNSIGNED,      "MaxBlockAdditionID"), #55 EE
                0x536E:     (EBMLTypes.TEXTU,         "Name"), #53 6E
                0x22B59C:   (EBMLTypes.TEXTA,         "Language"), #22 B5 9C
                0x86:       (EBMLTypes.TEXTA,         "CodecID"), #86
                0x63A2:     (EBMLTypes.BINARY,        "CodecPrivate"),#63 A2
                0x258688:   (EBMLTypes.TEXTU,         "CodecName"),#25 86 88
                0x7446:     (EBMLTypes.UNSIGNED,      "AttachmentLink"),#74 46
                0x3A9697:   (EBMLTypes.TEXTU,         "CodecSettings"),#3A 96 97
                0x3B4040:   (EBMLTypes.TEXTA,         "CodecInfoURL"),#3B 40 40
                0x26B240:   (EBMLTypes.TEXTA,         "CodecDownloadURL"),#26 B2 40
                0xAA:       (EBMLTypes.UNSIGNED,      "CodecDecodeAll"),#AA
                0x6FAB:     (EBMLTypes.UNSIGNED,      "TrackOverlay"),#6F AB
                0x56AA:     (EBMLTypes.UNSIGNED,      "CodecDelay"), #56 AA
                0x56BB:     (EBMLTypes.UNSIGNED,      "SeekPreRoll"), #56 BB
                0x6624:     (EBMLTypes.MASTER,        "TrackTranslate"),#66 24
                0x66FC:     (EBMLTypes.UNSIGNED,      "TrackTranslateEditionUID"), #66 FC
                0x66BF:     (EBMLTypes.UNSIGNED,      "TrackTranslateCodec"),#66 BF
                0x66A5:     (EBMLTypes.BINARY,        "TrackTranslateTrackID"),#66 A5
                0xE0:       (EBMLTypes.MASTER,        "Video"), #E0
                0x9A:       (EBMLTypes.UNSIGNED,      "FlagInterlaced"),#9A
                0x9D:       (EBMLTypes.UNSIGNED,      "FieldOrder"), #9D
                0x53B8:     (EBMLTypes.UNSIGNED,      "StereoMode"),#53 B8
                0x53C0:     (EBMLTypes.UNSIGNED,      "AlphaMode"),#53 C0
                0x53B9:     (EBMLTypes.UNSIGNED,      "OldStereoMode"),#53 B9
                0xB0:       (EBMLTypes.UNSIGNED,      "PixelWidth"),#B0
                0xBA:       (EBMLTypes.UNSIGNED,      "PixelHeight"),#BA
                0x54AA:     (EBMLTypes.UNSIGNED,      "PixelCropBottom"),#54 AA
                0x54BB:     (EBMLTypes.UNSIGNED,      "PixelCropTop"),#54 BB
                0x54CC:     (EBMLTypes.UNSIGNED,      "PixelCropLeft"),#54 CC
                0x54DD:     (EBMLTypes.UNSIGNED,      "PixelCropRight"),#54 DD
                0x54B0:     (EBMLTypes.UNSIGNED,      "DisplayWidth"),#54 B0
                0x54BA:     (EBMLTypes.UNSIGNED,      "DisplayHeight"),#54 BA
                0x54B2:     (EBMLTypes.UNSIGNED,      "DisplayUnit"),#54 B2
                0x54B3:     (EBMLTypes.UNSIGNED,      "AspectRatioType"),#54 B3
                0x2EB524:   (EBMLTypes.BINARY,        "ColourSpace"),#2E B5 24
                0x2FB523:   (EBMLTypes.FLOAT,         "GammaValue"),#2F B5 23
                0x2383E3:   (EBMLTypes.FLOAT,         "FrameRate"),#23 83 E3
                0x55B0:     (EBMLTypes.MASTER,        "Colour"), #55 B0
                0x55B1:     (EBMLTypes.UNSIGNED,      "MatrixCoefficients"),#55 B1
                0x55B2:     (EBMLTypes.UNSIGNED,      "BitsPerChannel"), #55 B2
                0x55B3:     (EBMLTypes.UNSIGNED,      "ChromaSubsamplingHorz"),#55 B3
                0x55B4:     (EBMLTypes.UNSIGNED,      "ChromaSubsamplingVert"), #55 B4
                0x55B5:     (EBMLTypes.UNSIGNED,      "CbSubsamplingHorz"), #55 B5
                0x55B6:     (EBMLTypes.UNSIGNED,      "CbSubsamplingVert"), #55 B6
                0x55B7:     (EBMLTypes.UNSIGNED,      "ChromaSitingHorz"), #55 B7
                0x55B8:     (EBMLTypes.UNSIGNED,      "ChromaSitingVert"), #55 B8
                0x55B9:     (EBMLTypes.UNSIGNED,      "Range"), #55 B9
                0x55BA:     (EBMLTypes.UNSIGNED,      "TransferCharacteristics"), #55 BA
                0x55BB:     (EBMLTypes.UNSIGNED,      "Primaries"), #55 BB
                0x55BC:     (EBMLTypes.UNSIGNED,      "MaxCLL"), #55 BC
                0x55BD:     (EBMLTypes.UNSIGNED,      "MaxFALL"), #55 BD
                0x55D0:     (EBMLTypes.MASTER,        "MasteringMetadata"), #55 D0
                0x55D5:     (EBMLTypes.FLOAT,         "PrimaryBChromaticityX"), #55 D1
                0x55D6:     (EBMLTypes.FLOAT,         "PrimaryBChromaticityY"), #55 D2
                0x55D3:     (EBMLTypes.FLOAT,         "PrimaryGChromaticityX"), #55 D3
                0x55D4:     (EBMLTypes.FLOAT,         "PrimaryGChromaticityY"), #55 D4
                0x55D1:     (EBMLTypes.FLOAT,         "PrimaryRChromaticityX"), #55 D5
                0x55D2:     (EBMLTypes.FLOAT,         "PrimaryRChromaticityY"), #55 D6
                0x55D7:     (EBMLTypes.FLOAT,         "WhitePointChromaticityX"), #55 D7
                0x55D8:     (EBMLTypes.FLOAT,         "WhitePointChromaticityY"), #55 D8
                0x55D9:     (EBMLTypes.FLOAT,         "LuminanceMax"), #55 D9
                0x55DA:     (EBMLTypes.FLOAT,         "LuminanceMin"), #55 DA
                0xE1:       (EBMLTypes.MASTER,        "Audio"), #E1
                0xB5:       (EBMLTypes.FLOAT,         "SamplingFrequency"),#B5
                0x78B5:     (EBMLTypes.FLOAT,         "OutputSamplingFrequency"),#78 B5
                0x9F:       (EBMLTypes.UNSIGNED,      "Channels"),#9F
                0x7D7B:     (EBMLTypes.BINARY,        "ChannelPositions"),#7D 7B
                0x6264:     (EBMLTypes.UNSIGNED,      "BitDepth"),#62 64
                0xE2:       (EBMLTypes.MASTER,        "TrackOperation"),#E2
                0xE3:       (EBMLTypes.MASTER,        "TrackCombinePlanes"),#E3
                0xE4:       (EBMLTypes.MASTER,        "TrackPlane"),#E4
                0xE5:       (EBMLTypes.UNSIGNED,      "TrackPlaneUID"),#E5
                0xE6:       (EBMLTypes.UNSIGNED,      "TrackPlaneType"),#E6
                0xE9:       (EBMLTypes.MASTER,        "TrackJoinBlocks"),#E9
                0xED:       (EBMLTypes.UNSIGNED,      "TrackJoinUID"),#ED
                0xC0:       (EBMLTypes.UNSIGNED,      "TrickTrackUID"),#C0
                0xC1:       (EBMLTypes.BINARY,        "TrickTrackSegmentUID"), #C1
                0xC6:       (EBMLTypes.UNSIGNED,      "TrickTrackFlag"),#C6
                0xC7:       (EBMLTypes.UNSIGNED,      "TrickMasterTrackUID"),#C7
                0xC4:       (EBMLTypes.BINARY,        "TrickMasterTrackSegmentUID"),#C4
                0x6D80:     (EBMLTypes.MASTER,        "ContentEncodings"),#6D 80
                0x6240:     (EBMLTypes.MASTER,        "ContentEncoding"),#62 40
                0x5031:     (EBMLTypes.UNSIGNED,      "ContentEncodingOrder"),#50 31
                0x5032:     (EBMLTypes.UNSIGNED,      "ContentEncodingScope"),#50 32
                0x5033:     (EBMLTypes.UNSIGNED,      "ContentEncodingType"),#50 33
                0x5034:     (EBMLTypes.MASTER,        "ContentCompression"),#50 34
                0x4254:     (EBMLTypes.UNSIGNED,      "ContentCompAlgo"),#42 54
                0x4255:     (EBMLTypes.BINARY,        "ContentCompSettings"),#42 55
                0x5035:     (EBMLTypes.MASTER,        "ContentEncryption"),#50 35
                0x47E1:     (EBMLTypes.UNSIGNED,      "ContentEncAlgo"),#47 E1
                0x47E2:     (EBMLTypes.BINARY,        "ContentEncKeyID"),#47 E2
                0x47E3:     (EBMLTypes.BINARY,        "ContentSignature"),#47 E3
                0x47E4:     (EBMLTypes.BINARY,        "ContentSigKeyID"),#47 E4
                0x47E5:     (EBMLTypes.UNSIGNED,      "ContentSigAlgo"),#47 E5
                0x47E6:     (EBMLTypes.UNSIGNED,      "ContentSigHashAlgo"),#47 E6
                                 # CUEING DATA                
                0x1C53BB6B: (EBMLTypes.MASTER,        "Cues"), #1C 53 BB 6B
                0xBB:       (EBMLTypes.MASTER,        "CuePoint"), #BB
                0xB3:       (EBMLTypes.UNSIGNED,      "CueTime"), #B3
                0xB7:       (EBMLTypes.MASTER,        "CueTrackPositions"), #B7
                0xF7:       (EBMLTypes.UNSIGNED,      "CueTrack"), #F7
                0xF1:       (EBMLTypes.UNSIGNED,      "CueClusterPosition"), #F1
                0xF0:       (EBMLTypes.UNSIGNED,      "CueRelativePosition"), #F0
                0x5378:     (EBMLTypes.UNSIGNED,      "CueBlockNumber"), #53 78
                0xEA:       (EBMLTypes.UNSIGNED,      "CueCodecState"), #EA
                0xDB:       (EBMLTypes.MASTER,        "CueReference"), #DB
                0x96:       (EBMLTypes.UNSIGNED,      "CueRefTime"), #96
                0x97:       (EBMLTypes.UNSIGNED,      "CueRefCluster"),#97
                0x535F:     (EBMLTypes.UNSIGNED,      "CueRefNumber"),#53 5F
                0xEB:       (EBMLTypes.UNSIGNED,      "CueRefCodecState"),#EB
                                 # ATTACHMENT                
                0x1941A469: (EBMLTypes.MASTER,        "Attachments"),#19 41 A4 69
                0x61A7:     (EBMLTypes.MASTER,        "AttachedFile"), #61 A7
                0x467E:     (EBMLTypes.TEXTU,         "FileDescription"), #46 7E
                0x466E:     (EBMLTypes.TEXTU,         "FileName"),#46 6E
                0x4660:     (EBMLTypes.TEXTA,         "FileMimeType"),#46 60
                0x465C:     (EBMLTypes.BINARY,        "FileData"),#46 5C
                0x46AE:     (EBMLTypes.UNSIGNED,      "FileUID"),#46 AE
                0x4675:     (EBMLTypes.BINARY,        "FileReferral"),#46 75
                0x4661:     (EBMLTypes.UNSIGNED,      "FileUsedStartTime"),#46 61
                0x4662:     (EBMLTypes.UNSIGNED,      "FileUsedEndTime"),#46 62
                                 # CHAPTERS
                0x1043A770: (EBMLTypes.MASTER,        "Chapters"), #10 43 A7 70
                0x45B9:     (EBMLTypes.MASTER,        "EditionEntry"), #45 B9
                0x45BC:     (EBMLTypes.UNSIGNED,      "EditionUID"), #45 BC
                0x45BD:     (EBMLTypes.UNSIGNED,      "EditionFlagHidden"), #45 BD
                0x45DB:     (EBMLTypes.UNSIGNED,      "EditionFlagDefault"), #45 DB
                0x45DD:     (EBMLTypes.UNSIGNED,      "EditionFlagOrdered"), #45 DD
                0xB6:       (EBMLTypes.MASTER,        "ChapterAtom"),#B6
                0x73C4:     (EBMLTypes.UNSIGNED,      "ChapterUID"),#73 C4
                0x5654:     (EBMLTypes.TEXTU,         "ChapterStringUID"), #56 54
                0x91:       (EBMLTypes.UNSIGNED,      "ChapterTimeStart"),#91
                0x92:       (EBMLTypes.UNSIGNED,      "ChapterTimeEnd"),#92
                0x98:       (EBMLTypes.UNSIGNED,      "ChapterFlagHidden"),#98
                0x4598:     (EBMLTypes.UNSIGNED,      "ChapterFlagEnabled"),#45 98
                0x6E67:     (EBMLTypes.BINARY,        "ChapterSegmentUID"),#6E 67
                0x6EBC:     (EBMLTypes.UNSIGNED,      "ChapterSegmentEditionUID"),#6E BC
                0x63C3:     (EBMLTypes.UNSIGNED,      "ChapterPhysicalEquiv"),#63 C3
                0x8F:       (EBMLTypes.MASTER,        "ChapterTrack"),#8F
                0x89:       (EBMLTypes.UNSIGNED,      "ChapterTrackNumber"),#89
                0x80:       (EBMLTypes.MASTER,        "ChapterDisplay"),#80
                0x85:       (EBMLTypes.TEXTU,         "ChapString"),#85
                0x437C:     (EBMLTypes.TEXTA,         "ChapLanguage"),#43 7C
                0x437E:     (EBMLTypes.TEXTA,         "ChapCountry"),#43 7F
                0x6944:     (EBMLTypes.MASTER,        "ChapProcess"),#69 44
                0x6955:     (EBMLTypes.UNSIGNED,      "ChapProcessCodecID"),# 69 55
                0x450D:     (EBMLTypes.BINARY,        "ChapProcessPrivate"),#45 0D
                0x6911:     (EBMLTypes.MASTER,        "ChapProcessCommand"),#69 11
                0x6922:     (EBMLTypes.UNSIGNED,      "ChapProcessTime"),#69 22
                0x6933:     (EBMLTypes.BINARY,        "ChapProcessData"),#69 33
                                 # TAGGING
                0x1254C367: (EBMLTypes.MASTER,        "Tags"), #12 54 C3 67
                0x7373:     (EBMLTypes.MASTER,        "Tag"), #73 73
                0x63C0:     (EBMLTypes.MASTER,        "Targets"), #63 C0
                0x68CA:     (EBMLTypes.UNSIGNED,      "TargetTypeValue"),#68 CA
                0x63CA:     (EBMLTypes.TEXTA,         "TargetType"),#63 CA
                0x63C5:     (EBMLTypes.UNSIGNED,      "TagTrackUID"),#63 C5
                0x63C9:     (EBMLTypes.UNSIGNED,      "TagEditionUID"),#63 C9
                0x63C4:     (EBMLTypes.UNSIGNED,      "TagChapterUID"),#63 C4
                0x63C6:     (EBMLTypes.UNSIGNED,      "TagAttachmentUID"),#63 C6
                0x67C8:     (EBMLTypes.MASTER,        "SimpleTag"),#67 C8
                0x45A3:     (EBMLTypes.TEXTU,         "TagName"),#45 A3
                0x447A:     (EBMLTypes.TEXTA,         "TagLanguage"),#44 7A
                0x4484:     (EBMLTypes.UNSIGNED,      "TagDefault"),#44 84
                0x4487:     (EBMLTypes.TEXTU,         "TagString"),#44 87
                0x4485:     (EBMLTypes.BINARY,        "TagBinary"),#44 85
               }

class MKV_handler:
    def available_Tracks(self):
        pass
    def available_SegmentInfo(self):
        pass
    def frame(self, trackID, timestamp, frameData, laced_frames, duration, keyframe, invisible, discardable):
        pass
    def ebml(self, ebmlID, ebmlNAME, ebmlTYPE, ebmlDATA):
        pass
    def before_handling(self):
        pass
    def start_handling(self, elementID, elementName, elementType, headersize, datasize):
        return elementType
    def available_Data(self, dataID, dataNAME, dataTYPE, headersize, data):
        pass

def getBitNumber(value):
    '''
    Takes:   the uint8 value
    Returns: the greatest numical bit (a.k.a. most significant
             bit) + number with that bit removed
    Example: 0b10010101 gives (0, 0b00010101)
             3          gives (6, 1)
    '''
    if not value:
        raise Exception("getBitNumber Error")

    i = 0x80 # declares an integer but in a hexadecimal form
    j = 0
    while not value & i:
        j += 1
        i >>= 1 # >> means i / 2**1; << means i * 2**1
    return (j, value - i) #or (j, value &~ i)

def readElement_Header(file):
    '''
    Reads: the elementID and the element_size
    Returns: ID, SIZE, and headerSIZE
    '''
    (elementID, n) = readMKV_number(file, unsignedByte = True)
    (element_size, n2)     = readMKV_number(file)
    return (elementID, element_size, n+n2)

def readMKV_number(file, unsignedByte = False, signedByte = False):
    '''
    converts the bit into the proper hexadecimal
    Reads:   MKV's number. unsignedByte means that the length bit isn't cleared.
    Returns: the number of the MKV element & length as a tuple.
    '''
    if unsignedByte and signedByte: # this scenario is unlikely to happen, but if it does then catch error
        raise Exception("ERROR: No such thing possible! It contradicts itself!")

    theFirstByte = file.read(1)

    if theFirstByte == "":
        raise StopIteration

    ascii_val = ord(theFirstByte)
    (n, ascii_val_2) = getBitNumber(ascii_val)

    if not unsignedByte:
        ascii_val = ascii_val_2

    j = n
    while j:
        ascii_val = ascii_val * 0x100 + ord(file.read(1))
        j -= 1

    if signedByte: #then it becomes NEGATIVE
        ascii_val = ascii_val - (2**(7*n+7)-1) # use more than 7 leadig zeros
    else:
        if ascii_val == (2**(7*n+7)-1):
            return (-1, n+1)

    return (ascii_val, n+1)

def parseMKV_number(elementData, location, unsignedByte = False, signedByte = False):
    '''
    Reads: parses ebml number from buffer[location:]
    Returns: the number of the MKV element + new location in the input buffer
    '''
    if unsignedByte and signedByte: # this scenario is unlikely to happen, but if it does then catch error
        raise Exception("ERROR: No such thing possible! It contradicts itself!")

    ascii_val = ord(elementData[location])
    location += 1
    (n, ascii_val_2) = getBitNumber(ascii_val)

    if not unsignedByte:
        ascii_val = ascii_val_2

    j = n
    while j:
        ascii_val = ascii_val * 0x100 + ord(elementData[location])
        location += 1
        j -= 1

    if signedByte: #then it becomes NEGATIVE
        ascii_val = ascii_val - (2**(7*n+6)-1) # use more than 7 leadig zeros
    else:
        if ascii_val == (2**(7*n+7)-1):
            return (-1, location)

    return (ascii_val, location)

def resynchronise(file):
    sys.stderr.write("parseMKV: Resynchronising\n")
    while True:
        bit = file.read(1)
        if bit == b"": # if the bit is empty
            return (None, None)

        if bit == b"\x1F":
            bit_2 = file.read(3)
            if bit_2 == b"\x43\xB6\x75":
                # cluster - contains multimedia data and usually spans over a range of a few seconds.
                (elementSize, headerSize) = readMKV_number(file)
                return (0x1F43B675, elementSize, headerSize+4) 
            
        if bit == b"\x18":
            bit_2 = file.read(3)
            if bit_2 == b"\x53\x80\x67":
                # segment - contains multimedia data, as well as any header data necessary for replay.
                (elementSize, headerSize) = readMKV_number(file)
                return (0x18538067, elementSize, headerSize+4)

        if bit == b"\x16":
            bit_2 = file.read(3)
            if bit_2 == b"\x54\xAE\x6B":
                # tracks = contains information about the track taht are stored in the Segment,
                # like track type (audio, video, subtitles), the used codec, resolution and sample rate.
                (elementSize, headerSize) = readMKV_number(file)
                return (0x1654AE6B, elementSize, headerSize+4)

def ebmlElementTree(file, totSize):
    '''
    Builds the tree of all the EBML Elements
    Read: file until total size has been reached
    Returns: list of elements in pairs (elementName, elementVal)
    '''
    childTable = [] # contains all the childs
    while totSize > 0:
        (elementID, elementSize, header_size) = readElement_Header(file)
        if (elementSize == -1) or (elementSize > totSize):
            sys.stderr.write("parseMKV: Element %x has no size. Data is probably damaged. %d byte is skipped\n" %(elementID, elementSize, totSize))
            file.read(totSize)
            break

	# separate the previous part if it is malfunctioning

        elementType = EBMLTypes.BINARY
        elementName = "unknownName_%x" % elementID

        if elementID in table_element_name:
            (elementType, elementName) = table_element_name[elementID]
            
        elementData = readElement(file, elementType, elementSize)
        totSize = totSize - (elementSize + header_size)

        childTable.append((elementName, (elementType, elementData)))
    return childTable


def readElement(file, elementType, elementSize):
    '''
    Identifies the size, and the type of the element in the table_element_name
    Reads: the type, and the size from the ebmlElementTree
    Returns: the data of the element or elementData (combined)
    '''
    elementDate = None
    if elementSize == 0:
        return ""

    #performs job on UNSGINED INTEGERS
    if elementType == EBMLTypes.UNSIGNED: 
        elementData = get_fixed_length_number(file, elementSize, False)

    #performs job on SIGNED INTEGERS
    elif elementType == EBMLTypes.SIGNED:
        elementData = get_fixed_length_number(file, elementSize, True)

    #performs job on TEXTA
    elif elementType == EBMLTypes.TEXTA: 
        elementData = file.read(elementSize)
        elementData = elementData.replace(b"\x00", b"") #filters out all the \0
        elementData = elementData.decode("ascii")

    #performs job on TEXTU
    elif elementType == EBMLTypes.TEXTU: 
        elementData = file.read(elementSize)
        elementData = elementData.replace(b"\x00", b"") #filters out all the \0
        elementData = elementData.decode("UTF-8")

    #performs job on MASTER
    elif elementType == EBMLTypes.MASTER: 
        elementData = ebmlElementTree(file, elementSize)

    #perform job on DATE - changes to UNIX date
    elif elementType == EBMLTypes.DATE: 
        elementData = get_fixed_length_number(file, elementSize)
        elementData = elementData * 1e-9
        elementData = elementData + (datetime.datetime(2001, 1, 1) - datetime.datetime(1970, 1, 1)).total_seconds()

    #perform job on FLOAT
    elif elementType == EBMLTypes.FLOAT:
        if elementSize == 4: #float length 4
            elementData = file.read(4)
            elementData = unpack(">f", elementData)[0]
        elif elementSize == 8: #float length 8
            elementData = file.read(8)
            elementData = unpack(">d", elementData)[0]
        else: #not any of the above
            elementData = get_fixed_length_number(file, elementSize, False)
            sys.stderr.write("parseMKV: The floating point of the size %d is not recognised\n" % size)
            elementData = None

    else:
        elementData = file.read(elementSize)

    return elementData

def get_fixed_length_number(file, lengthByte, signedByte = False):
    '''
    parse fixed length number using parse_fixed_length_number fuction
    Read: length of the btye 
    Return: number
    '''
    buffer = file.read(lengthByte) #reads the lnegth of the byte
    (number, location) = parse_fixed_length_number(buffer, 0, lengthByte, signedByte) #calls the parser to get the number
    return number

def parse_fixed_length_number(numberData, location, lengthByte, signedByte = False):
    '''
    Reads: big endian number from numberData[location: location + lengthByte]
    Return: number together with the position

    Eg:
    "\xFF\x04" signed ===> (-0x00FC,  pos+2)
    "\x01"            ===> (0x1,    pos+1)
    "\xFF\x04"        ===> (0xFF04,  pos+2)
    "\x55"            ===> (0x55, pos+1)
    "\x55" signed     ===> (0x55, pos+1)
    '''
    number = 0
    for j in range(lengthByte):
        number = number * 0x100 + ord(numberData[location+j])

    if signedByte:
        if ord(numberData[location]) & 0x80:
            number = number - 2**(8*lengthByte)

    return (number, location + lengthByte)

def block_handler(buffer, handler, clusterTimecode, timecodeScale = 1000000, duration = None, removeHeaders_for_tracks = {}):
    '''
    handles all the lacings, decodes a block, sends appropriate timestamp to handler, tracks the number
    '''
    location = 0
    (trackID, location) = parseMKV_number(buffer, location, signedByte = False)
    (timeCode, location) = parse_fixed_length_number(buffer, location, 2, signedByte = True)
    flag = ord(buffer[location]) #sets if the track is usable
    location += 1
    fileKeyFrame = (flag & 0x80 == 0x80)
    fileInvisible = (flag & 0x80 == 0x08)
    fileDiscardable = (flag & 0x01 == 0x01)
    flagLacing = flag & 0x06

    timeCode_block = (clusterTimecode + timeCode) * (timecodeScale * 0.000000001)

    removeHeaders_Prefix = b""
    if trackID in removeHeaders_for_tracks:
        removeHeaders_Prefix = removeHeaders_for_tracks[trackID]

    # no lacing
    if flagLacing == 0x00:
        buffVal = buffer[location:]
        handler.frame(trackID, timeCode_block, removeHeaders_Prefix + buffVal, 0, duration, fileKeyFrame, fileInvisible, fileDiscardable)
        return

    number_of_frames = ord(buffer[location])
    location += 1

    totalFrameLength = []

    # XIPH Lacing
    if flagLacing == 0x02:
        accumulatedLength = 0
        for j in range(number_of_frames-1):
            (l, location) = parseXIPH(buffer, location)
            totalFrameLength.append(l)
            accumulatedLength = accumulatedLength + l
        totalFrameLength.append(len(buffer) - location - accumulatedLength)

    # EBML Lacing
    elif flagLacing == 0x06:
        accumulatedLength = 0
        if number_of_frames:
            (frameLength, location) = parseMKV_number(buffer, location, signedByte = False)
            totalFrameLength.append(frameLength)
            accumulatedLength = accumulatedLength + frameLength
        for j in range(number_of_frames-2):
            (l, location) = parseMKV_number(buffer, location, signedByte = True)
            frameLength = frameLength + l
            totalFrameLength.append(frameLength)
            accumulatedLength = accumulatedLength + frameLength
        totalFrameLength.append(len(buffer) - location - accumulatedLength)

    #Fixed SIZE Lacing
    elif flagLacing == 0x04:
        frame_1 = int((len(buffer) - location) / number_of_frames)
        for j in range(number_of_frames):
            totalFrameLength.append(frame_1)

    otherLacingFrames = number_of_frames - 1
    for j in totalFrameLength:
        buffVal = buffer[location:location+j]
        location = location + j
        handler.frame(trackID, timeCode_block, removeHeaders_Prefix + buffVal, otherLacingFrames, duration, fileKeyFrame, fileInvisible, fileDiscardable)
        otherLacingFrames = otherLacingFrames - 1

def parseXIPH(elementData, location):
    '''
    Parses the xiph lacing number from elementData[location]
    Return: number + new location
    '''
    ascii_val = ord(elementData[location])
    location = location + 1

    n = 0
    while ascii_val == 255:
        n = n + ascii_val
        ascii_val = ord(elementData[location]) #reassigns
        location = location + 1

    n = n + ascii_val
    return (n, location)

def parseMKV(file, handler): # handler = MKV_handler
    '''
    Reads an MKV 'file', calls handler when segment or track info is ready,
    or when frame has been read. handler - responsible for lacing & timecodes
    '''
    timecodeScale = 1000000 #each scaled timecode is multiplied by timecodescale to obtain a timecode in nanoseconds
    clusterTimecode = 0 # timecode all block timecodes are indicated relatively to
    resyncElement_ID = None
    resyncElement_Size = None
    resyncElement_Headersize = None
    removeHeaders_for_tracks = {}

    '''
    1. Need to find the hexadecimal value first, so the right elementID & type can be identified
    '''
    while file:
        (elementID, elementSize, header_size) = (None, None, None)
        elementTree = None
        elementData = None
        (elementType, elementName) = (None, None)
        try:
            if not resyncElement_ID:
                try:
                    handler.before_handling()
                    (elementID, elementSize, header_size) =  readElement_Header(file)
                except StopIteration:
                    break

                if (elementID not in table_element_name):
                    # the interpreter's own prompts and its error messages go to stderr. Any object is acceptable
                    # as long as it writes a string argument
                    sys.stderr.write("parseMKV: Unknown element with id %x and size %d has been found.\n" %(elementID, elementSize))
                    (resyncElement_ID, resyncElement_Size, resyncElement_Headersize) = resynchronise(file)
                    if resyncElement_ID:
                        continue
                    else:
                        break

            else:
                elementID = resyncElement_ID
                elementSize = resyncElement_Size
                header_size = resyncElement_Headersize
                resyncElement_ID = None #reset, since previous variable store the vals
                resyncElement_Size = None #reset, since previous variable store the vals
                resyncElement_Headersize = None #reset, since previous variable store the vals

            (elementType, elementName) = table_element_name[elementID]
            (elementType, elementName) = table_element_name[elementID]
            elementType = handler.start_handling(elementID, elementName, elementType, header_size, elementSize) # calls MKV_Handler by the user

            if elementType == EBMLTypes.MASTER:
                elementTree = ebmlElementTree(file, elementSize)
                elementData = elementTree

        except Exception:
            traceback.print_exc() #extract, format and print stack tracer
            handler.before_handling()
            (resyncElement_ID, resyncElement_Size, resyncElement_Headersize) = resynchronise(file)
            if resyncElement_ID:
                continue
            else:
                break

        #verifies the EBML\Matroska\webm file
        if elementName == "EBML" and type(elementData) == list: 
            dictionary = dict(elementTree)
            if "EBMLReadVersion" in dictionary:
                if dictionary["EBMLReadVersion"][1] > 1:
                    sys.stderr.write("parseMKV: EBMLReadVersion is too big\n")

            if "DocTypeReadVersion" in dictionary:
                if dictionary["DocTypeReadVersion"][1] > 2:
                    sys.stderr.write("parseMKV: DocTypeReadVersion is too big\n")
                    
            if dictionary["DocType"][1] != "matroska" and dictionary["DocType"][1] != "webm":
                sys.stderr.write("parseMKV: The type of the document is not \"matroska\" or \"webm\"\n")

        elif elementName == "Info" and type(elementData) == list:
            handler.segment_info = elementTree
            handler.available_SegmentInfo()

            dictionary = dict(elementTree)
            if "TimecodeScale" in dictionary :
                timecodeScale = dictionary["TimecodeScale"][1]

        elif elementName == "Tracks" and type(elementData) == list:
            handler.tracks = {}
            for (ten, (trackID, track)) in elementTree:
                if ten != "TrackEntry":
                    continue

                dictionary = dict(track)
                n = dictionary["TrackNumber"][1]
                handler.tracks[n] = dictionary

                trackInfo = dictionary["TrackType"][1]
                if trackInfo == 0x01:
                    dictionary["type"] = "video"
                elif trackInfo == 0x02:
                    dictionary["type"] = "audio"
                elif trackInfo == 0x03:
                    dictionary["type"] = "complex"
                elif trackInfo == 0x10:
                    dictionary["type"] = "logo"
                elif trackInfo == 0x11:
                    dictionary["type"] = "subtitle"
                elif trackInfo == 0x12:
                    dictionary["type"] = "button"
                elif trackInfo == 0x20:
                    dictionary["type"] = "control"

                if "TrackTimecodeScale" in dictionary:
                    sys.stderr.write("parseMKV: TrackTimecodeScale is not supported.\n")

                if "ContentEncodings" in dictionary:
                    try:
                        compress = dict(dictionary["ContentEncodings"][1][0][1][1][0][1][1])
                        if compress["ContentCompAlgo"][1] == 3:
                            removeHeaders_for_tracks[n] = compress["ContentCompSettings"][1]
                        else:
                            sys.stderr.write("parseMKV: compression of anything else but header is not supported\n")
                    except:
                        sys.stderr.write("parseMKV: the removal of the header is unsuccessful")

            handler.available_Tracks()
            
        elif elementName == "Timecode" and elementType == EBMLTypes.UNSIGNED:
            elementData = get_fixed_length_number(file, elementSize, False)
            clusterTimecode = elementData

        elif elementName == "SimpleBlock" and elementType == EBMLTypes.BINARY:
            elementData = file.read(elementSize)
            block_handler(elementData, handler, clusterTimecode, timecodeScale, None, removeHeaders_for_tracks)

        elif elementName == "BlockGroup" and elementType == EBMLTypes.MASTER:
            dictionary_2 = dict(elementTree)
            duration = None
            if "BlockDuration" in dictionary_2:
                duration = dictionary_2["BlockDuration"][1]
                duration = duration * 0.000000001 * timecodeScale
            if "Block" in dictionary_2:
                block_handler(dictionary_2["Block"][1], handler, clusterTimecode, timecodeScale, duration, removeHeaders_for_tracks)
    
        else:
            if (elementType != EBMLTypes.PROCEED) and (elementType != EBMLTypes.MASTER):
                elementData = readElement(file, elementType, elementSize)

        handler.ebml(elementID, elementName, elementType, elementData)
				

'''MKV to XML converter begins here'''
class ConvertMKVtoXML(MKV_handler):
	def __init__(self, block_list, no_clusters):
		 self.segment_found = False
		 self.cluster_found = False
		 self.beginning = 0
		 self.get_trackID = None
		 self.get_ts = None
		 self.get_data = []
		 self.get_duration = None
		 self.block_list = block_list
		 self.no_clusters = no_clusters
		 self.get_tracksText = frozenset([])
		 self.private_codec = False
		 self.get_duration = None
		 self.get_trackID = 555
		 self.get_ts = 555.5
		 self.get_data = []
		 self.get_keyframe = False
		 self.get_invisible = False
		 self.get_discardable = False
		
		 print("<mkv2xml>")

	def __del__(self):
		if self.cluster_found:
			print("</Cluster>")
			
		if self.segment_found:
			print("</Segment>")
		print("</mkv2xml>")

	def available_Tracks(self):
		get_tracksText = []
		for i in self.tracks:
			theTrack = self.tracks[i]
			if theTrack['CodecID'][1][:6] == "S_TEXT":
				get_tracksText.append(i)
		self.get_tracksText = frozenset(get_tracksText)

	def available_SegmentInfo(self):
		pass

	def frame(self, trackID, timestamp, frameData, laced_frames, duration, keyframe, invisible, discardable):
		self.get_duration = duration
		self.get_available_Tracks = trackID
		self.get_ts = timestamp
		self.get_data.append(frameData)
		self.get_keyframe = keyframe
		self.get_invisible = invisible
		self.get_discardable = discardable
		
		if self.no_clusters:
			print("<block>%s</block>" % self.format_block(""))
			
	def format_block(self, beginning_):
		timecodeData = "\n  " + beginning_ + "<track>%s</track>" % self.get_available_Tracks
		timecodeData += "\n  " + beginning_ + "<timecode>%s</timecode>" % self.get_ts
	
		if self.get_duration:
			timecodeData += "\n  " + beginning_ + "<duration>%s</duration>" % self.get_duration
			
		if self.get_keyframe:
			timecodeData += "\n  " + beginning_ + "<keyframe/>" 
			
		if self.get_invisible:
			timecodeData += "\n  " + beginning_ + "<invisible/>"
        
		if self.get_discardable:
			timecodeData+="\n  " + beginning_+ "<discardable/>"
			
		for anotherData in self.get_data:
			decode_to_Text = False
			if self.get_available_Tracks in self.get_tracksText:
				try:
					anotherData = anotherData.decode("UTF-8")
					timecodeData += "\n  " + beginning_ + "<data encoding=\"text\"><![CDATA["
					timecodeData += anotherData.replace("\x00","").replace("]]>", "]]]]><![CDATA[>")
					timecodeData += "]]></data>"
					decode_to_Text = True
				except UnicodeDecodeError:
					sys.stderr.write("Error encountered decoding to UTF-8, data remained unchanged (in binary)\n")
					
			if not decode_to_Text:
				timecodeData += "\n  "+ beginning_ + "<data>"
				for chunk in chunks(maybe_decode(binascii.hexlify(anotherData)), length_of_the_chunk):
					timecodeData += "\n    " + beginning_
					timecodeData += chunk
				
				timecodeData += "\n  " + beginning_ + "</data>"
		
		timecodeData += "\n"+beginning_
		self.get_duration = None
		self.get_available_Tracks = None
		self.get_ts = None
		self.get_data = []
		
		return timecodeData
	
	def returnTree(self, theList, beginning):
		beginning_ = "  " * beginning;
		for (elementName, (elementType, elementData)) in theList:
			beginning_of_the_tag = elementName
			if self.cluster_found and \
				elementName != "Timecode" and \
				elementName != "SilentTracks" and \
				elementName != "Position" and \
				elementName != "PrevSize" and \
				elementName != "SimpleBlock" and \
				elementName != "BlockGroup" and \
				elementName != "Void" and \
				elementName != "CRC-32" and \
				elementName != "SignatureSlot" and \
				elementName != "EncryptedBlock" and \
				beginning == self.beginning:
				
				beginning_ = ""
				beginning = 0
				self.beginning = 0
				print("</Cluster>")
				self.cluster_found=False
				
			if elementName == "TrackNumber":
				self.private_codec = elementData in self.get_tracksText
				
			if elementName in self.block_list:
				continue
				
			if elementType == EBMLTypes.BINARY:
				if elementName == "SimpleBlock" or elementName == "Block":
					elementData=self.format_block(beginning_)
					
				elif elementData:
					encoded_as_text = False
					if elementName == "CodecPrivate" and self.private_codec:
						try:
							elementData = elementData.decode("UTF-8")
							elementData = elementData.replace("]]>", "]]]]><![CDATA[>")
							elementData = "<![CDATA[" + elementData + "]]>"
							beginning_of_the_tag = "CodecPrivate encoding=\"text\""
							encoded_as_text = True
						except UnicodeDecodeError:
							sys.stderr.write("Error encountered decoding to UTF-8, data remained unchanged (in binary)\n")
					
					if not encoded_as_text:
						elementData = maybe_decode(binascii.hexlify(elementData))
						if len(elementData) > 40:
							timecodeData = ""
							for chunk in chunks(elementData, length_of_the_chunk):
								timecodeData += "\n  " + beginning_
								timecodeData += chunk
							timecodeData += "\n" + beginning_
							elementData = timecodeData
							
			if elementType == EBMLTypes.MASTER:
				print("%s<%s>"%(beginning_, elementName))
				self.returnTree(elementData, beginning + 1)
				print("%s</%s>"%(beginning_, elementName))
			elif elementType == EBMLTypes.PROCEED:
				if elementName == "Segment":
					if self.segment_found:
						print("</Segment>")
					print("<Segment>")
					self.segment_found = True
				elif elementName == "Cluster":
					print("<Cluster>")
					self.cluster_found = True
					self.beginning = 1
				else:
					sys.stderr.write("Unknown element for PROCEEDing %s\n" % elementName)
			else:
				if elementType == EBMLTypes.TEXTA or elementType == EBMLTypes.TEXTU:
					# saxutils - contains a number of classes and functions that are
					# commonly useful when creating SAX applications, either in direct
					# use, or as base classes.
					elementData = saxutils.escape(str(elementData))
				print("%s<%s>%s</%s>"%(beginning_, beginning_of_the_tag, elementData, elementName))
				
	def ebml(self, ebmlID, ebmlNAME, ebmlTYPE, ebmlDATA):
		self.returnTree([(ebmlNAME, (ebmlTYPE, ebmlDATA))], self.beginning)

def chunks(elementData, length_of_the_chunk):
	"""
	Returns: the length of the chunk from the ElementData
	"""
	if not length_of_the_chunk:
		yield elementData
		return
    
	for i in range(0, len(elementData), length_of_the_chunk):
		yield elementData[i:i + length_of_the_chunk]
				
if __name__ == '__main__':
	if sys.version < '3':
		reload(sys)
		sys.setdefaultencoding('utf-8') #stops faiiling on uncoding subtitles
		range = xrange
		maybe_decode = lambda x:x
	else:
		maybe_decode = lambda x:x.decode("ascii")

	block_list = ["SeekHead", "CRC-32", "Void", "Cues", "PrevSize", "Position"]
	no_clusters = False
	length_of_the_chunk = 64

	if len(sys.argv) > 1:
		if sys.argv[1] == "-v":
			banlist = []

		if sys.argv[1] == "-C":
			no_clusters = True
			block_list=["SeekHead", "CRC-32", "Void", "Cues", "PrevSize", "Position", "Cluster", "Timecode", "PrevSize", "EncryptedBlock", "BlockGroup", "SimpleBlock"]

	length_of_the_chunk = int(getenv("CHUNKLENGTH", "64"))

	if sys.version >= '3':
		sys.stdin = sys.stdin.detach()

	parseMKV(sys.stdin, ConvertMKVtoXML(frozenset(block_list), no_clusters))

