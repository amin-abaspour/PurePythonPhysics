
import os
import struct

def read_bmp(file_path):
    """
    Reads a 24-bit BMP file and returns the pixel data in RGB format.
    """
    with open(file_path, "rb") as f:
        # Read BMP Header
        header_field = f.read(2)
        if header_field != b'BM':
            raise ValueError(f"{file_path} is not a BMP file.")

        file_size = struct.unpack('<I', f.read(4))[0]
        reserved1 = struct.unpack('<H', f.read(2))[0]
        reserved2 = struct.unpack('<H', f.read(2))[0]
        offset = struct.unpack('<I', f.read(4))[0]

        # Read DIB Header
        dib_header_size = struct.unpack('<I', f.read(4))[0]
        width = struct.unpack('<I', f.read(4))[0]
        height = struct.unpack('<I', f.read(4))[0]
        planes = struct.unpack('<H', f.read(2))[0]
        bit_count = struct.unpack('<H', f.read(2))[0]
        compression = struct.unpack('<I', f.read(4))[0]
        image_size = struct.unpack('<I', f.read(4))[0]
        x_ppm = struct.unpack('<I', f.read(4))[0]
        y_ppm = struct.unpack('<I', f.read(4))[0]
        clr_used = struct.unpack('<I', f.read(4))[0]
        clr_important = struct.unpack('<I', f.read(4))[0]

        if bit_count != 24:
            raise ValueError(f"{file_path} is not a 24-bit BMP file.")

        # Move to pixel data
        f.seek(offset)

        # Each row is padded to a multiple of 4 bytes
        row_padded = (width * 3 + 3) & ~3
        raw_data = f.read(row_padded * height)

        # Convert BMP to top-down RGB
        pixel_data = bytearray()
        for row in range(height):
            row_start = row * row_padded
            row_end = row_start + (width * 3)
            row_data = raw_data[row_start:row_end]
            # BMP stores in BGR format; convert to RGB
            for i in range(0, len(row_data), 3):
                b, g, r = row_data[i:i+3]
                pixel_data += bytes([r, g, b])
        return pixel_data


def pad_to_even(data):
    """
    Pads the data to ensure its length is even.
    """
    if len(data) % 2 != 0:
        return data + b'\x00'
    return data


def create_avi(frames_dir, output_avi, frame_rate=30):
    """
    Creates an uncompressed AVI file from BMP frames located in frames_dir.
    """
    # Collect and sort BMP frame files
    frame_files = sorted([f for f in os.listdir(frames_dir) if f.lower().endswith('.bmp')])
    if not frame_files:
        raise ValueError("No BMP files found in the specified directory.")

    # Read all frames
    frames = []
    print("Reading BMP frames...")
    for frame_file in frame_files:
        frame_path = os.path.join(frames_dir, frame_file)
        pixel_data = read_bmp(frame_path)
        frames.append(pixel_data)

    num_frames = len(frames)
    if num_frames == 0:
        raise ValueError("No frames to process.")

    # Assume all frames are the same size
    frame_size = len(frames[0])
    width = 200  # Update this if your frames have a different width
    height = 200  # Update this if your frames have a different height

    # AVI Main Header (avih)
    microsec_per_frame = int(1e6 / frame_rate)
    max_bytes_per_sec = width * height * 3 * frame_rate  # Uncompressed
    padding_granularity = 0
    flags = 0x10  # AVIF_HASINDEX
    total_frames = num_frames
    initial_frames = 0
    streams = 1
    suggested_buffer_size = width * height * 3
    width_avi = width
    height_avi = height

    avih = struct.pack('<14I',
                       microsec_per_frame,
                       max_bytes_per_sec,
                       padding_granularity,
                       flags,
                       total_frames,
                       initial_frames,
                       streams,
                       suggested_buffer_size,
                       width_avi,
                       height_avi,
                       0, 0, 0, 0)

    # AVI Stream Header (strh)
    fcc_type = b'vids'
    fcc_handler = b'DIB '  # Indicates no compression (BI_RGB)
    flags_strh = 0
    priority = 0
    language = 0
    initial_frames_strh = 0
    scale = 1
    rate = frame_rate
    start = 0
    length = num_frames
    suggested_buffer_size_strh = suggested_buffer_size
    quality = 0xFFFF  # Default (-1) as unsigned
    sample_size = 0

    # Corrected strh packing with proper format string and arguments
    # AVISTREAMHEADER includes rcFrame which is 16 bytes (4 LONGs)
    strh = struct.pack('<4s4sIHHIIIIIIII16s',
                       fcc_type,
                       fcc_handler,
                       flags_strh,
                       priority,
                       language,
                       initial_frames_strh,
                       scale,
                       rate,
                       start,
                       length,
                       suggested_buffer_size_strh,
                       quality,
                       sample_size,
                       b'\x00' * 16)  # rcFrame set to zero

    # AVI Stream Format (strf) - BITMAPINFOHEADER
    bi_size = 40
    bi_width = width
    bi_height = height
    bi_planes = 1
    bi_bit_count = 24
    bi_compression = 0  # BI_RGB
    bi_size_image = width * height * 3
    bi_x_pels_per_meter = 2835
    bi_y_pels_per_meter = 2835
    bi_clr_used = 0
    bi_clr_important = 0

    strf = struct.pack('<IIIHHIIIIII',
                       bi_size,
                       bi_width,
                       bi_height,
                       bi_planes,
                       bi_bit_count,
                       bi_compression,
                       bi_size_image,
                       bi_x_pels_per_meter,
                       bi_y_pels_per_meter,
                       bi_clr_used,
                       bi_clr_important)

    # Construct 'hdrl' LIST chunk
    avih_chunk = b'avih' + struct.pack('<I', len(avih)) + avih
    strh_chunk = b'strh' + struct.pack('<I', len(strh)) + strh
    strf_chunk = b'strf' + struct.pack('<I', len(strf)) + strf
    strl_list = b'LIST' + struct.pack('<I', 4 + len(strh_chunk) + len(strf_chunk)) + b'strl' + strh_chunk + strf_chunk
    hdrl_list = b'LIST' + struct.pack('<I', 4 + len(avih_chunk) + len(strl_list)) + b'hdrl' + avih_chunk + strl_list

    # Construct 'movi' LIST chunk
    movi_list = bytearray()
    movi_list += b'movi'

    # To create the index, keep track of each frame's byte offset within 'movi'
    idx_entries = []
    movi_data_offset = 0  # Relative to start of 'movi' data

    print("Assembling 'movi' LIST chunk...")
    for i, frame in enumerate(frames):
        chunk_id = b'00dc'  # Video frame
        frame_data = frame
        frame_size = len(frame_data)
        frame_chunk = chunk_id + struct.pack('<I', frame_size) + frame_data
        frame_chunk = pad_to_even(frame_chunk)
        movi_list += frame_chunk

        # Each frame entry in idx1: (4s, I, I)
        # 4s: chunk ID
        # I: flags (0x10 for key frame)
        # I: offset (relative to 'movi' list start)
        idx_entry = struct.pack('<4sII', chunk_id, 0x10, movi_data_offset)
        idx_entries.append(idx_entry)

        # Update offset: each frame chunk size
        movi_data_offset += len(frame_chunk)

        if (i + 1) % 100 == 0:
            print(f"{i + 1} frames added to 'movi' LIST.")

    movi_chunk = b'LIST' + struct.pack('<I', len(movi_list)) + movi_list

    # Construct 'idx1' chunk
    idx1 = bytearray()
    for entry in idx_entries:
        idx1 += entry
    idx1_chunk = b'idx1' + struct.pack('<I', len(idx1)) + idx1

    # Write the AVI file
    with open(output_avi, 'wb') as avi:
        # Write RIFF header with placeholder for file size
        avi.write(b'RIFF')
        avi.write(struct.pack('<I', 0))  # Placeholder
        avi.write(b'AVI ')

        # Write 'hdrl' LIST
        avi.write(hdrl_list)

        # Write 'movi' LIST
        avi.write(movi_chunk)

        # Write 'idx1' chunk
        avi.write(idx1_chunk)

        # Calculate the total file size
        file_size = avi.tell() - 8  # Exclude 'RIFF' and size field
        avi.seek(4)
        avi.write(struct.pack('<I', file_size))  # Update file size

    print(f"AVI file '{output_avi}' created successfully with {num_frames} frames.")


if __name__ == "__main__":
    # Define video output parameters
    frames_directory = "./frames"  # Directory containing BMP frames
    output_video = "./output.avi"    # Output AVI file name
    frame_rate = 30                # Frames per second

    # Create AVI video from frames
    create_avi(frames_directory, output_video, frame_rate)
