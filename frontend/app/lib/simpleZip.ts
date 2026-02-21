export type ZipFileInput = {
  name: string;
  content: string;
};

function pushU16(buffer: number[], value: number) {
  buffer.push(value & 0xff, (value >>> 8) & 0xff);
}

function pushU32(buffer: number[], value: number) {
  buffer.push(
    value & 0xff,
    (value >>> 8) & 0xff,
    (value >>> 16) & 0xff,
    (value >>> 24) & 0xff,
  );
}

function crc32(bytes: Uint8Array): number {
  let crc = -1;
  for (let i = 0; i < bytes.length; i += 1) {
    crc ^= bytes[i];
    for (let j = 0; j < 8; j += 1) {
      const mask = -(crc & 1);
      crc = (crc >>> 1) ^ (0xedb88320 & mask);
    }
  }
  return (crc ^ -1) >>> 0;
}

function getDosTimeDate() {
  const now = new Date();
  const dosTime =
    ((now.getHours() & 0x1f) << 11) |
    ((now.getMinutes() & 0x3f) << 5) |
    ((Math.floor(now.getSeconds() / 2) & 0x1f) >>> 0);
  const dosDate =
    (((now.getFullYear() - 1980) & 0x7f) << 9) |
    (((now.getMonth() + 1) & 0x0f) << 5) |
    (now.getDate() & 0x1f);

  return { dosTime, dosDate };
}

export function createZipBlob(files: ZipFileInput[]): Blob {
  const encoder = new TextEncoder();
  const localAndData: number[] = [];
  const centralDirectory: number[] = [];

  let offset = 0;

  files.forEach((file) => {
    const nameBytes = encoder.encode(file.name);
    const dataBytes = encoder.encode(file.content);
    const dataCrc = crc32(dataBytes);
    const { dosTime, dosDate } = getDosTimeDate();

    pushU32(localAndData, 0x04034b50);
    pushU16(localAndData, 20);
    pushU16(localAndData, 0);
    pushU16(localAndData, 0);
    pushU16(localAndData, dosTime);
    pushU16(localAndData, dosDate);
    pushU32(localAndData, dataCrc);
    pushU32(localAndData, dataBytes.length);
    pushU32(localAndData, dataBytes.length);
    pushU16(localAndData, nameBytes.length);
    pushU16(localAndData, 0);
    localAndData.push(...nameBytes);
    localAndData.push(...dataBytes);

    pushU32(centralDirectory, 0x02014b50);
    pushU16(centralDirectory, 20);
    pushU16(centralDirectory, 20);
    pushU16(centralDirectory, 0);
    pushU16(centralDirectory, 0);
    pushU16(centralDirectory, dosTime);
    pushU16(centralDirectory, dosDate);
    pushU32(centralDirectory, dataCrc);
    pushU32(centralDirectory, dataBytes.length);
    pushU32(centralDirectory, dataBytes.length);
    pushU16(centralDirectory, nameBytes.length);
    pushU16(centralDirectory, 0);
    pushU16(centralDirectory, 0);
    pushU16(centralDirectory, 0);
    pushU16(centralDirectory, 0);
    pushU32(centralDirectory, 0);
    pushU32(centralDirectory, offset);
    centralDirectory.push(...nameBytes);

    offset = localAndData.length;
  });

  const centralOffset = localAndData.length;
  localAndData.push(...centralDirectory);
  const centralSize = centralDirectory.length;

  pushU32(localAndData, 0x06054b50);
  pushU16(localAndData, 0);
  pushU16(localAndData, 0);
  pushU16(localAndData, files.length);
  pushU16(localAndData, files.length);
  pushU32(localAndData, centralSize);
  pushU32(localAndData, centralOffset);
  pushU16(localAndData, 0);

  return new Blob([new Uint8Array(localAndData)], { type: "application/zip" });
}
