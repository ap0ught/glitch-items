#!/usr/bin/env python3
"""Peek at an SWF file: version, compression, CRECT, frame rate/count, and tag inventory."""
import struct, sys, zlib, lzma

NAMES = {0:'DoAction',1:'ShowFrame',2:'DefineShape',4:'PlaceObject',5:'RemoveObject',
 6:'DefineBits',7:'DefineButton',8:'JPEGTables',9:'SetBackgroundColor',10:'DefineFont',
 11:'DefineText',12:'DoInitAction',14:'DefineBitsLossless',22:'DefineButtonSound',
 24:'EnableDebugger',27:'DefineShape2',28:'DefineMorphShape',29:'DefineBitsJPEG2',
 32:'DefineFontInfo',35:'ExportAssets',36:'ImportAssets',37:'EnableDebugger',
 39:'DefineFont2',46:'EnableDebugID',48:'End',56:'DefineEditText',
 57:'DefineSprite',58:'ProductInfo',64:'DefineVideoStream',
 71:'DefineScalingGrid',72:'DoInitAction2',76:'DefineMorphShape2',
 82:'DefineVideoStream',83:'DefineVideoFrame',84:'DefineFont3',
 89:'FileAttributes',92:'DefineSceneAndFrameLabelData',93:'DefineBinaryData',
 95:'DefineFontName',97:'DefineFontAlignZones',98:'StartSound',99:'ButtonSound'}

def parse(path):
    raw = open(path, 'rb').read()
    sig = raw[:3]
    if sig == b'CWS':
        ver = raw[3]
        uncomp_len = struct.unpack_from('<I', raw, 4)[0]
        body = zlib.decompress(raw[8:])
        comp = 'zlib'
    elif sig == b'FWS':
        ver = raw[3]
        uncomp_len = struct.unpack_from('<I', raw, 4)[0]
        body = lzma.decompress(raw[8:], format=lzma.FORMAT_ALONE) if uncomp_len > 8 else b''
        comp = 'lzma'
    else:
        ver = raw[0]
        body = raw
        comp = 'none'
    xmin, ymin, xmax, ymax = struct.unpack_from('<4h', body, 2)
    print(f'{path}')
    print(f'  v{ver} {comp} stage={xmax/20:.0f}x{abs(ymin)/20:.0f} ({xmin/20:.0f},{ymin/20:.0f}..{xmax/20:.0f},{ymax/20:.0f})')
    tags = {}
    meta = {}
    i = 10
    while i + 2 <= len(body):
        hdr = struct.unpack_from('<H', body, i)[0]
        i += 2
        code = hdr >> 6
        length = hdr & 0x3F
        if code in (0, 1, 2, 7, 26, 57, 58, 89):
            length = struct.unpack_from('<I', body, i)[0]
            i += 4
        b = body[i:i+length]
        i += length
        tags[code] = tags.get(code, 0) + 1
        if code == 89 and length >= 7:
            fr = struct.unpack_from('<H', b, 1)[0]
            fc = struct.unpack_from('<I', b, 3)[0]
            meta['frames'] = fc
            meta['fps'] = (fr >> 1) / (fr & 1 or 1)
    for code in sorted(tags):
        print(f'  {code:3d} {NAMES.get(code, "Unknown"):28s} x{tags[code]}')
    if 'frames' in meta:
        print(f'  => frames={meta["frames"]} fps={meta["fps"]}')

if __name__ == '__main__':
    parse(sys.argv[1])
